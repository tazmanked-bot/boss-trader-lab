"""Owner-run wheel collection and offline-install evidence; no local installs."""
import argparse
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse
import zipfile

from research.dependency_closeout import (
    canonical, check_hash, collect_wheel, installed, request_json, sha256, write_json,
)

CCXT_HASH = "004c4a9176700df6c5d4f8f7b2fd4691743040b70a2818c7afe1ad93021e62d4"
VERSION = "4.5.92"


def collect(output):
    wheelhouse = output / "wheelhouse"
    wheelhouse.mkdir(parents=True, exist_ok=False)
    # Resolve/download only; no downloaded distribution is imported or executed.
    # All binaries are checked against exact-version PyPI metadata before install.
    subprocess.run(["python", "-m", "pip", "--isolated", "download", "--index-url",
                    "https://pypi.org/simple", "--only-binary=:all:",
                    "--dest", str(wheelhouse), "ccxt==" + VERSION], check=True)
    from email.parser import BytesParser
    manifest = {"schema": 1, "wheels": [], "inventory": [], "status": "OWNER_REVIEW_REQUIRED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "research_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "python": platform.python_version(), "platform": platform.platform(),
                "image_version": os.environ.get("ImageVersion"),
                "resolution": "first-run transitive snapshot; not a previously reviewed transitive lock"}
    source = json.loads((Path(__file__).parent / "ccxt-candidate.json").read_text())
    for wheel in sorted(wheelhouse.iterdir()):
        if wheel.suffix != ".whl":
            raise AssertionError("source builds are not permitted")
        with zipfile.ZipFile(wheel) as archive:
            meta = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
            if len(meta) != 1:
                raise AssertionError("wheel metadata missing")
            msg = BytesParser().parsebytes(archive.read(meta[0]))
            name, version = canonical(msg["Name"]), msg["Version"]
            unpacked = sum(i.file_size for i in archive.infolist())
        release = request_json(f"https://pypi.org/pypi/{name}/{version}/json")
        write_json(output / "pypi" / (name + ".json"), release)
        matches = [f for f in release["urls"] if f["filename"] == wheel.name]
        if len(matches) != 1 or matches[0].get("yanked"):
            raise AssertionError("unverified or yanked wheel")
        artifact = matches[0]
        if urlparse(artifact["url"]).hostname != "files.pythonhosted.org":
            raise AssertionError("unexpected wheel origin")
        check_hash(wheel.read_bytes(), artifact["digests"]["sha256"])
        if name == "ccxt":
            if version != VERSION:
                raise AssertionError("unexpected CCXT release")
            check_hash(wheel.read_bytes(), CCXT_HASH)
        inventory = collect_wheel(wheel, output, source["reviewed_sources"] if name == "ccxt" else {})
        if name == "ccxt" and len(inventory["reviewed_sources"]) != 1:
            raise AssertionError("reviewed Kraken source not present")
        inventory.update(wheel_filename=wheel.name, compressed_bytes=wheel.stat().st_size,
                         unpacked_bytes=unpacked)
        manifest["inventory"].append(inventory)
        manifest["wheels"].append({"name": name, "version": version, "filename": wheel.name,
                                   "sha256": sha256(wheel.read_bytes()), "url": artifact["url"]})
    names = [i["name"] for i in manifest["wheels"]]
    if names.count("ccxt") != 1 or len(names) != len(set(names)):
        raise AssertionError("ambiguous runtime distribution set")
    write_json(output / "resolved-manifest.json", manifest)
    lock = "# Owner-run snapshot; review before promotion or reuse.\n" + "\n".join(
        i["name"] + "==" + i["version"] + " --hash=sha256:" + i["sha256"]
        for i in manifest["wheels"]) + "\n"
    (output / "runtime.lock").write_text(lock)
    coverage = []
    queries = [(i["name"], i["version"]) for i in manifest["wheels"]]
    for name in ("pip", "setuptools"):
        try:
            queries.append((name, metadata.version(name)))
        except metadata.PackageNotFoundError:
            pass
    for name, version in sorted(set(queries)):
        row = {"name": name, "version": version,
               "timestamp": datetime.now(timezone.utc).isoformat()}
        try:
            response = request_json("https://api.osv.dev/v1/query",
                        {"package": {"ecosystem": "PyPI", "name": name}, "version": version})
            write_json(output / "osv" / f"{name}-{version}.json", response)
            row.update(status="RESPONSE_RECORDED", ids=[v["id"] for v in response.get("vulns", [])])
        except Exception as exc:
            row.update(status="UNVERIFIED", error_type=type(exc).__name__)
        coverage.append(row)
    write_json(output / "advisory-coverage.json", coverage)
    print(json.dumps({"status": "HASHED_SNAPSHOT_SECURITY_REVIEW_REQUIRED", "packages": names,
                      "total_wheel_bytes": sum(i["compressed_bytes"] for i in manifest["inventory"]),
                      "total_unpacked_bytes": sum(i["unpacked_bytes"] for i in manifest["inventory"])}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("collect", "installed"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Use the authorized temporary Actions runner only")
    args.output.mkdir(parents=True, exist_ok=True)
    if args.stage == "collect":
        collect(args.output)
    else:
        installed(args.output, json.loads((args.output / "resolved-manifest.json").read_text()))


if __name__ == "__main__":
    main()
