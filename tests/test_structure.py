"""Permanent offline checks against current sources, not the upstream snapshot."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import os
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import webapp


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("src", "href"):
            value = attrs.get(key, "")
            if value and not value.startswith(("http:", "https:", "data:", "#")):
                self.paths.append(value)


class StructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Exercise the real generators in a disposable output tree, never dist/.
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name)
        write_bytes = Path.write_bytes
        write_text = Path.write_text

        def destination(path):
            target = cls.output / path.relative_to(ROOT / "dist")
            os.makedirs(target.parent, exist_ok=True)
            return target

        for script in ("prepare_preview.py", "prepare_tizen.py"):
            module = runpy.run_path(str(ROOT / "scripts" / script))
            with patch.object(Path, "mkdir"), patch.object(
                Path, "write_bytes", lambda path, data: write_bytes(destination(path), data)
            ), patch.object(
                Path, "write_text", lambda path, data, **kw: write_text(destination(path), data, **kw)
            ):
                module["main"]()

    def test_current_sources_reach_both_outputs(self):
        expected = webapp.files(dict(webapp.GENERIC), "validation")
        generated = {"config.js", "coins.js", "i18n.js"}
        for output in ("preview", "tizen"):
            folder = self.output / output
            for name, data in expected.items():
                with self.subTest(output=output, resource=name):
                    path = folder / name
                    self.assertTrue(path.is_file())
                    if name not in generated:
                        self.assertEqual(path.read_bytes(), data)
            for name in generated:
                # Ignore only the generator name in the first comment.
                actual = (folder / name).read_text(encoding="utf-8")
                wanted = expected[name].decode("utf-8")
                self.assertEqual(re.sub(r"^/\*.*?\*/\n", "", actual),
                                 re.sub(r"^/\*.*?\*/\n", "", wanted))

    def test_html_and_css_local_resources(self):
        for name in ("preview", "tizen"):
            folder = self.output / name
            parser = Resources()
            parser.feed((folder / "index.html").read_text(encoding="utf-8"))
            for resource in parser.paths:
                self.assertTrue((folder / urlsplit(resource).path).is_file(), resource)
            css = (folder / "home.css").read_text(encoding="utf-8")
            for resource in re.findall(r"url\(['\"]?([^)'\"]+)", css):
                if not resource.startswith(("data:", "http:", "https:")):
                    self.assertTrue((folder / resource).is_file(), resource)

    def test_manifest_identity_and_copy(self):
        manifest = ROOT / "tizen/config.xml"
        self.assertEqual(manifest.read_bytes(), (self.output / "tizen/config.xml").read_bytes())
        app = ET.parse(manifest).getroot().find("{http://tizen.org/ns/widgets}application")
        self.assertEqual(app.attrib["id"], "FmtvDU8a01.FreeMyTVVariant")
        self.assertEqual(app.attrib["package"], "FmtvDU8a01")
        self.assertEqual(app.attrib["required_version"], "2.3")

    def test_licenses_and_credits_in_outputs(self):
        notices = {"LICENSE": "LICENSE", "UPSTREAM_README.md": "docs/UPSTREAM_README.md",
                   "fonts/OFL.txt": "web/fonts/OFL.txt",
                   "symbols/LICENSE-material-symbols.txt": "web/symbols/LICENSE-material-symbols.txt"}
        for output in ("preview", "tizen"):
            for destination, source in notices.items():
                self.assertEqual((self.output / output / destination).read_bytes(),
                                 (ROOT / source).read_bytes())
            folder = self.output / output
            notice = (folder / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
            source_notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
            self.assertEqual(notice, source_notice.replace(
                "](docs/UPSTREAM_README.md)", "](UPSTREAM_README.md)"))
            self.assertNotIn("](docs/UPSTREAM_README.md)", notice)
            self.assertIn("](UPSTREAM_README.md)", notice)
            self.assertTrue((folder / "UPSTREAM_README.md").is_file())

    def test_sdk_allowlist_exact_and_safe(self):
        folder = self.output / "tizen"
        settings = (folder / "tizen_web_project.yaml").read_text(encoding="utf-8")
        listed = [json.loads(line[4:]) for line in settings.split("files:\n", 1)[1]
                  .split("excludes:", 1)[0].splitlines() if line.startswith("  - ")]
        # SDK artifacts are not resources and may coexist with the staged project.
        sdk_dirs = {"Debug", "Release", "Build", "Test", ".vscode", ".tizen-rds",
                    ".buildResult", ".sign"}
        actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*")
                  if p.is_file() and not (set(p.relative_to(folder).parts[:-1]) & sdk_dirs)
                  and p.suffix.lower() != ".wgt"}
        self.assertEqual(set(listed), actual - {"tizen_web_project.yaml"})
        self.assertIn('signing_profile: ""', settings)
        self.assertIn('profile: tv-samsung', settings)
        for name in listed:
            self.assertNotIn("..", Path(name).parts)
            self.assertFalse(Path(name).is_absolute())
            self.assertFalse(set(Path(name).parts) & {".git", ".vscode", "backups", "scripts", "tests"})
            self.assertNotIn(Path(name).suffix.lower(), {".p12", ".pfx", ".wgt", ".key", ".pem"})

if __name__ == "__main__":
    unittest.main()
