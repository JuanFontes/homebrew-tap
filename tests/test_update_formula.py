"""Exercise release verification and atomic formula updates without network access."""

import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/update_formula.py"
if SCRIPT.is_file():
    spec = importlib.util.spec_from_file_location("update_formula", SCRIPT)
    updater = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(updater)
else:
    updater = None


class FormulaUpdates(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(updater, "Release verification is not implemented")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.formula = Path(self.temporary.name) / "curlimp.rb"
        self.before = (ROOT / "Formula/curlimp.rb").read_text()
        self.formula.write_text(self.before)
        self.current = updater.formula_version(self.before)
        self.new_version = f"{int(self.current.split('.')[0]) + 1}.0.0"
        self.release, self.downloads = self.fixture(self.new_version)

    def fixture(self, version):
        base = f"https://github.com/JuanFontes/curlimp/releases/download/v{version}/"
        downloads = {}
        assets = []
        sums = []
        for platform in ("macos-arm64", "linux-amd64", "linux-arm64"):
            name = f"curlimp-{version}-{platform}.tar.gz"
            data = f"fixture-{platform}".encode()
            sha = hashlib.sha256(data).hexdigest()
            downloads[base + name] = data
            sums.append(f"{sha}  {name}\n")
            assets.append(
                {
                    "name": name,
                    "browser_download_url": base + name,
                    "size": len(data),
                    "digest": "sha256:" + sha,
                }
            )
        manifest = "".join(sums).encode()
        downloads[base + "SHA256SUMS"] = manifest
        assets.append(
            {
                "name": "SHA256SUMS",
                "browser_download_url": base + "SHA256SUMS",
                "size": len(manifest),
                "digest": "sha256:" + hashlib.sha256(manifest).hexdigest(),
            }
        )
        return {
            "tag_name": "v" + version,
            "draft": False,
            "prerelease": False,
            "assets": assets,
        }, downloads

    def open_url(self, request, **kwargs):
        url = request.full_url
        if url == "https://api.github.com/repos/JuanFontes/curlimp/releases/latest":
            return io.BytesIO(json.dumps(self.release).encode())
        self.assertNotIn("Authorization", request.headers)
        return io.BytesIO(self.downloads[url])

    def update(self):
        with patch.object(updater.urllib.request, "urlopen", side_effect=self.open_url):
            return updater.update(self.formula)

    def rejected(self):
        with self.assertRaises(ValueError):
            self.update()
        self.assertEqual(self.formula.read_text(), self.before)

    def test_updates_all_platform_urls_and_verified_hashes(self):
        self.assertTrue(self.update())
        actual = self.formula.read_text()
        self.assertEqual(updater.formula_version(actual), self.new_version)
        for asset in self.release["assets"][:3]:
            self.assertIn(asset["browser_download_url"], actual)
            self.assertIn(asset["digest"][7:], actual)
        self.assertIn(self.before.split("  def install", 1)[1], actual)

    def test_current_release_is_an_unchanged_noop(self):
        self.release, self.downloads = self.fixture(self.current)
        self.assertFalse(self.update())
        self.assertEqual(self.formula.read_text(), self.before)

    def test_older_latest_cannot_downgrade(self):
        self.release, self.downloads = self.fixture("0.0.0")
        self.assertFalse(self.update())
        self.assertEqual(self.formula.read_text(), self.before)

    def test_prerelease_draft_and_invalid_tags_are_rejected(self):
        for change in (
            {"prerelease": True},
            {"draft": True},
            {"tag_name": "v1.0.0-rc.1"},
            {"tag_name": "v01.0.0"},
            {"tag_name": "v1.0.0\ninjected=true"},
        ):
            with self.subTest(change=change):
                self.release, self.downloads = self.fixture(self.new_version)
                self.release.update(change)
                self.rejected()

    def test_missing_or_duplicate_assets_are_rejected(self):
        self.release["assets"].pop(0)
        self.rejected()
        self.release, self.downloads = self.fixture(self.new_version)
        self.release["assets"].append(dict(self.release["assets"][0]))
        self.rejected()

    def test_download_urls_must_point_to_the_exact_upstream_release(self):
        self.release["assets"][0]["browser_download_url"] = "https://untrusted.invalid/archive"
        self.rejected()

    def test_corrupt_archive_or_wrong_size_cannot_change_formula(self):
        url = self.release["assets"][0]["browser_download_url"]
        self.downloads[url] = b"corrupt"
        self.rejected()
        self.release, self.downloads = self.fixture(self.new_version)
        self.release["assets"][0]["size"] += 1
        self.rejected()

    def test_manifest_and_api_digest_must_agree(self):
        self.release["assets"][0]["digest"] = "sha256:" + "0" * 64
        self.rejected()

    def test_corrupt_manifest_is_rejected(self):
        self.downloads[self.release["assets"][-1]["browser_download_url"]] = b"bad manifest"
        self.rejected()

    def test_duplicate_checksum_names_are_rejected(self):
        asset = self.release["assets"][-1]
        data = self.downloads[asset["browser_download_url"]]
        data += data.splitlines(keepends=True)[0]
        self.downloads[asset["browser_download_url"]] = data
        asset.update(size=len(data), digest="sha256:" + hashlib.sha256(data).hexdigest())
        self.rejected()

    def test_unrecognized_formula_layout_fails_before_writing(self):
        self.before = self.before.replace("macos-arm64.tar.gz", "macos-intel.tar.gz")
        self.formula.write_text(self.before)
        self.rejected()

    def test_network_failure_leaves_formula_unchanged(self):
        with patch.object(updater.urllib.request, "urlopen", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                updater.update(self.formula)
        self.assertEqual(self.formula.read_text(), self.before)

    def test_verify_current_rejects_replaced_release_assets(self):
        self.release, self.downloads = self.fixture(self.current)
        with patch.object(updater.urllib.request, "urlopen", side_effect=self.open_url):
            with self.assertRaisesRegex(ValueError, "checksums changed"):
                updater.update(self.formula, verify_current=True)
        self.assertEqual(self.formula.read_text(), self.before)

    def test_verify_current_downloads_every_asset_without_changing_formula(self):
        self.release, self.downloads = self.fixture(self.current)
        hashes = {
            platform: self.release["assets"][i]["digest"][7:]
            for i, platform in enumerate(updater.PLATFORMS)
        }
        self.before = updater.render(self.before, self.current, self.current, hashes)
        self.formula.write_text(self.before)
        with patch.object(updater.urllib.request, "urlopen", side_effect=self.open_url) as opened:
            self.assertFalse(updater.update(self.formula, verify_current=True))
        self.assertEqual(opened.call_count, 5)
        self.assertEqual(self.formula.read_text(), self.before)

    def test_failed_atomic_replace_preserves_the_original(self):
        with patch.object(updater.urllib.request, "urlopen", side_effect=self.open_url):
            with patch.object(updater.os, "replace", side_effect=OSError("read only")):
                with self.assertRaises(OSError):
                    updater.update(self.formula)
        self.assertEqual(self.formula.read_text(), self.before)
        self.assertEqual(list(self.formula.parent.iterdir()), [self.formula])


if __name__ == "__main__":
    unittest.main()
