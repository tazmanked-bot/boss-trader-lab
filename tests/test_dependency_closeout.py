"""Offline corruption checks; no package installation or network calls."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from research.dependency_closeout import check_hash, collect_wheel, installed, safe_member, verify_wheel_record


class IntegrityTests(unittest.TestCase):
    def test_artifact_hash_corruption(self):
        digest = hashlib.sha256(b"reviewed").hexdigest()
        check_hash(b"reviewed", digest)
        with self.assertRaises(AssertionError):
            check_hash(b"corrupted", digest)

    def test_unsafe_member(self):
        for name in ("../escape", "/absolute", "pkg\\escape", "pkg.data/purelib/a.py"):
            with self.subTest(name=name), self.assertRaises(AssertionError):
                safe_member(name)

    def archive(self, changed=False, extra=False):
        payload = b"original"
        digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).decode().rstrip("=")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("pkg/file.py", b"tampered" if changed else payload)
            archive.writestr("pkg-1.dist-info/RECORD",
                             f"pkg/file.py,sha256={digest},8\npkg-1.dist-info/RECORD,,\n")
            if extra:
                archive.writestr("unrecorded.py", b"unexpected")
        return zipfile.ZipFile(io.BytesIO(buf.getvalue()))

    def test_record_integrity(self):
        with self.archive() as archive:
            verify_wheel_record(archive)
        for changed, extra in ((True, False), (False, True)):
            with self.archive(changed, extra) as archive, self.assertRaises(AssertionError):
                verify_wheel_record(archive)

    def full_wheel(self, path):
        files = {"pkg/file.py": b"reviewed source\n",
                 "pkg-1.dist-info/METADATA": b"Name: pkg\nVersion: 1\nLicense: MIT\n\n",
                 "pkg-1.dist-info/LICENSE": b"MIT license fixture"}
        rows = []
        for name, data in files.items():
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
            rows.append(f"{name},sha256={digest},{len(data)}")
        files["pkg-1.dist-info/RECORD"] = ("\n".join(rows) + "\npkg-1.dist-info/RECORD,,\n").encode()
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        return files

    def test_license_inventory_and_source_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = root / "pkg.whl"
            files = self.full_wheel(wheel)
            sources = {"pkg/file.py": {"sha256": hashlib.sha256(files["pkg/file.py"]).hexdigest()}}
            result = collect_wheel(wheel, root / "evidence", sources)
            self.assertEqual(result["name"], "pkg")
            self.assertEqual(len(result["notices"]), 1)
            sources["pkg/file.py"]["sha256"] = "0" * 64
            with self.assertRaises(AssertionError):
                collect_wheel(wheel, root / "evidence", sources)

    def test_installed_byte_tampering_and_unlocked_distribution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "evidence"
            (output / "wheelhouse").mkdir(parents=True)
            wheel = output / "wheelhouse" / "pkg.whl"
            files = self.full_wheel(wheel)
            target = root / "runtime"
            for name, data in files.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            dist = SimpleNamespace(metadata={"Name": "pkg"}, version="1",
                locate_file=lambda name: target / name,
                read_text=lambda name: (target / "pkg-1.dist-info" / name).read_text())
            manifest = {"wheels": [{"name": "pkg", "version": "1", "filename": "pkg.whl",
                         "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}]}
            with patch("research.dependency_closeout.platform_contract"), \
                 patch("research.dependency_closeout.sys.prefix", str(target)), \
                 patch("research.dependency_closeout.metadata.distributions", return_value=[dist]), \
                 patch("research.dependency_closeout.metadata.distribution", return_value=dist):
                installed(output, manifest)
                self.assertEqual(json.loads((output / "installed-identity.json").read_text())["status"], "PASS")
                (target / "pkg/file.py").write_bytes(b"tampered")
                with self.assertRaises(AssertionError):
                    installed(output, manifest)
                with patch("research.dependency_closeout.metadata.distributions", return_value=[dist, dist]):
                    with self.assertRaises(AssertionError):
                        installed(output, manifest)


if __name__ == "__main__":
    unittest.main()
