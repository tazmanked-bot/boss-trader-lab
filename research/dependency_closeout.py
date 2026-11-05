"""Issue #6 evidence collection, runnable only on an authorized Actions runner.

Downloads are never imported. Installation is a separate, offline hash-enforced
workflow step. Findings produce evidence, not an automatic security approval.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.metadata as metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parent


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def check_hash(data, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or sha256(data) != expected:
        raise AssertionError("SHA-256 mismatch")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def request_json(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = Request(url, data=data, headers={"Content-Type": "application/json",
                      "User-Agent": "boss-trader-lab-issue-6-evidence"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def safe_member(name):
    parts = PurePosixPath(name)
    if parts.is_absolute() or ".." in parts.parts or "\\" in name:
        raise AssertionError(f"unsafe wheel member: {name}")
    # This reviewed wheel set has no .data relocation scheme.
    if any(part.endswith(".data") for part in parts.parts):
        raise AssertionError(f"unreviewed wheel relocation: {name}")
    return parts


def verify_wheel_record(archive):
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise AssertionError("duplicate wheel members")
    records = [n for n in names if n.endswith(".dist-info/RECORD")]
    if len(records) != 1:
        raise AssertionError("expected one wheel RECORD")
    rows = list(csv.reader(io.StringIO(archive.read(records[0]).decode())))
    recorded = set()
    for name, digest, size in rows:
        safe_member(name)
        if name in recorded:
            raise AssertionError("duplicate RECORD entry")
        recorded.add(name)
        data = archive.read(name)
        if name == records[0]:
            if digest or size:
                raise AssertionError("RECORD must not hash itself")
            continue
        if not digest.startswith("sha256="):
            raise AssertionError(f"missing SHA-256 RECORD digest: {name}")
        expected = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        if digest != "sha256=" + expected or size != str(len(data)):
            raise AssertionError(f"wheel RECORD mismatch: {name}")
    if recorded != {n for n in names if not n.endswith("/")}:
        raise AssertionError("wheel files and RECORD differ")


def collect_wheel(path, output, reviewed_sources):
    from email.parser import BytesParser
    with zipfile.ZipFile(path) as archive:
        verify_wheel_record(archive)
        names = archive.namelist()
        metas = [n for n in names if n.endswith(".dist-info/METADATA")]
        if len(metas) != 1:
            raise AssertionError("expected one wheel METADATA")
        msg = BytesParser().parsebytes(archive.read(metas[0]))
        notices = []
        sources = []
        for name in names:
            safe_member(name)
            if name.endswith("/"):
                continue
            data = archive.read(name)
            if re.search(r"license|copying|notice|copyright|authors", name, re.I):
                dest = output / "notices" / path.name / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                notices.append({"path": name, "sha256": sha256(data)})
            if name in reviewed_sources:
                check_hash(data, reviewed_sources[name]["sha256"])
                sources.append({"path": name, "sha256": sha256(data),
                                "reviewed_source": reviewed_sources[name]})
        if canonical(msg["Name"]) == "pandas-ta-classic" and len(sources) != len(reviewed_sources):
            raise AssertionError("reviewed source missing from wheel")
        if not notices:
            raise AssertionError(f"no license/notice files in {path.name}")
        return {"name": msg["Name"], "version": msg["Version"],
                "requires_dist": msg.get_all("Requires-Dist", []),
                "license_expression": msg.get("License-Expression"),
                "license": msg.get("License"), "license_files": msg.get_all("License-File", []),
                "notices": notices, "reviewed_sources": sources,
                "wheel_sha256": sha256(path.read_bytes())}


def platform_contract():
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise AssertionError("lock supports Linux x86_64 only")
    if platform.python_version() != "3.11.17":
        raise AssertionError("lock evidence requires Python 3.11.17")


def prepare(output, manifest):
    platform_contract()
    wheelhouse = output / "wheelhouse"
    wheelhouse.mkdir(parents=True, exist_ok=False)
    inventory = []
    for item in manifest["wheels"]:
        url = f'https://pypi.org/pypi/{item["name"]}/{item["version"]}/json'
        release = request_json(url)
        write_json(output / "pypi" / (item["name"] + ".json"), release)
        matches = [f for f in release["urls"] if f["filename"] == item["filename"]]
        if len(matches) != 1:
            raise AssertionError(f"release wheel not found: {item['filename']}")
        artifact = matches[0]
        if artifact.get("yanked") or artifact["digests"]["sha256"] != item["sha256"]:
            raise AssertionError("release metadata differs from reviewed manifest")
        parsed = urlparse(artifact["url"])
        if parsed.scheme != "https" or parsed.hostname != "files.pythonhosted.org":
            raise AssertionError("unapproved artifact host")
        with urlopen(artifact["url"], timeout=60) as response:
            if urlparse(response.url).hostname != "files.pythonhosted.org":
                raise AssertionError("unapproved artifact redirect")
            data = response.read()
        check_hash(data, item["sha256"])
        path = wheelhouse / item["filename"]
        path.write_bytes(data)
        row = collect_wheel(path, output, manifest["reviewed_sources"])
        if canonical(row["name"]) != item["name"] or row["version"] != item["version"]:
            raise AssertionError("wheel metadata does not match lock")
        row["artifact_url"] = artifact["url"]
        inventory.append(row)
    write_json(output / "wheel-inventory.json", inventory)
    toolchain = []
    for name in ("pip", "setuptools"):
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue
        notices = []
        for file in dist.files or []:
            if re.search(r"license|copying|notice|copyright|authors", str(file), re.I):
                data = Path(dist.locate_file(file)).read_bytes()
                # Preserve the name in JSON; use digest as a safe destination.
                digest = sha256(data)
                dest = output / "toolchain-notices" / name / digest
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                notices.append({"path": str(file), "sha256": digest})
        toolchain.append({"name": name, "version": dist.version,
                          "license": dist.metadata.get("License"), "notices": notices})
    write_json(output / "toolchain.json", toolchain)
    queries = [(i["name"], i["version"]) for i in manifest["wheels"]]
    queries += [(i["name"], i["version"]) for i in toolchain]
    queries.append(("setuptools", "79.0.1"))
    coverage = []
    for name, version in sorted(set(queries)):
        body = {"package": {"ecosystem": "PyPI", "name": name}, "version": version}
        row = {"name": name, "version": version, "queried_at": datetime.now(timezone.utc).isoformat(),
               "endpoint": "https://api.osv.dev/v1/query", "request": body}
        try:
            response = request_json(row["endpoint"], body)
            write_json(output / "osv" / f"{name}-{version}.json", response)
            row.update(status="RESPONSE_RECORDED", advisory_ids=[v["id"] for v in response.get("vulns", [])])
        except Exception as exc:
            row.update(status="UNVERIFIED", error=str(exc))
        coverage.append(row)
    write_json(output / "advisory-coverage.json", coverage)
    write_json(output / "prepare.json", {"status": "WHEELS_VERIFIED_SECURITY_REVIEW_REQUIRED",
               "timestamp": datetime.now(timezone.utc).isoformat(),
               "research_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
               "python": platform.python_version(), "platform": platform.platform(),
               "libc": platform.libc_ver(), "os_release": Path("/etc/os-release").read_text(),
               "runner_image_version": os.environ.get("ImageVersion"),
               "provenance": "No pandas-ta-classic PyPI attestation verified; source equality is not provenance"})


def installed(output, manifest):
    platform_contract()
    distributions = list(metadata.distributions())
    expected = {i["name"]: i["version"] for i in manifest["wheels"]}
    actual = {canonical(d.metadata["Name"]): d.version for d in distributions}
    if actual != expected or len(distributions) != len(expected):
        raise AssertionError(f"unlocked runtime distributions: {actual!r}")
    results = []
    for item in manifest["wheels"]:
        dist = metadata.distribution(item["name"])
        path = output / "wheelhouse" / item["filename"]
        check_hash(path.read_bytes(), item["sha256"])
        checked = 0
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                safe_member(name)
                if name.endswith("/") or name.endswith(".dist-info/RECORD"):
                    continue
                target = Path(dist.locate_file(name)).resolve()
                if not target.is_relative_to(Path(sys.prefix).resolve()):
                    raise AssertionError("installed file escapes isolated environment")
                if target.read_bytes() != archive.read(name):
                    raise AssertionError(f"installed bytes differ from wheel: {name}")
                checked += 1
        record = dist.read_text("RECORD")
        if record is None:
            raise AssertionError("installed RECORD missing")
        record_checks = 0
        for name, digest, size in csv.reader(io.StringIO(record)):
            target = Path(dist.locate_file(name)).resolve()
            if not target.is_relative_to(Path(sys.prefix).resolve()):
                raise AssertionError("RECORD path escapes environment")
            data = target.read_bytes()
            if not digest:
                if not name.endswith(".dist-info/RECORD") or size:
                    raise AssertionError("unexpected unhashed installed file")
                continue
            encoded = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
            if digest != "sha256=" + encoded or size != str(len(data)):
                raise AssertionError(f"installed RECORD mismatch: {name}")
            record_checks += 1
        results.append({"name": item["name"], "version": dist.version,
                        "wheel_files_equal": checked, "installed_record_hashes_equal": record_checks})
    write_json(output / "installed-identity.json", {"status": "PASS", "distributions": results,
               "scope": "fresh closeout runtime only; not a retrospective proof of earlier runs"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "installed"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run only in the owner-authorized temporary GitHub Actions runner")
    manifest = json.loads((ROOT / "dependency-manifest.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        globals()[args.stage](args.output, manifest)
    except Exception as exc:
        write_json(args.output / (args.stage + "-failure.json"),
                   {"status": "FAIL", "error": str(exc), "type": type(exc).__name__})
        raise


if __name__ == "__main__":
    main()
