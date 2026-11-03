"""Manual bookmarks never infer history or overwrite unrelated preferences."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ContinueWatchingTests(unittest.TestCase):
    def test_bookmarks_and_persistence(self):
        browser = Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"
        if not browser.is_file():
            self.skipTest("Installed Chrome required")
        source = (ROOT / "web/data.js").read_text(encoding="utf-8")
        source = source[source.index("var Prefs ="):source.index("var Data =")]
        js = "var SOURCE = " + json.dumps(source) + ";\n"
        js += r"""
function check(ok, message) { if (!ok) throw Error(message); }
var record = JSON.stringify({city: 'Brasilia', tmdbKey: 'test-marker', shelf: ['existing']});
var storage = {getItem: function() { return record; }, setItem: function(key, value) { record = value; }};
function load() {
 return new Function('localStorage', 'CONFIG', 'Place', SOURCE + '\nreturn ContinueWatching;')(storage, {}, {});
}
var model = load();
check(model.list().length === 0 && JSON.parse(record).continueWatching === undefined, 'No fabricated history or automatic write');
check(!model.save(null, -1) && !model.save({title: '', category: 'movies'}, -1), 'Missing data rejected');
check(model.save({title: 'Manual anime', category: 'anime', image: 'javascript:bad'}, -1), 'Manual inclusion');
var entry = model.list()[0];
check(entry.image === '' && entry.season === 1 && entry.episode === 1, 'Missing fields and unsafe image');
entry.season = 2; entry.episode = 8; entry.appId = 'discovered-id';
check(model.save(entry, 0), 'Editing');
model = load();
check(model.list()[0].episode === 8 && model.list()[0].season === 2 && model.list()[0].appId === 'discovered-id', 'Persistence');
check(model.save({title: 'Manual movie', category: 'movies', season: 5}, -1) && model.list()[1].season === null, 'Movie has no episode fields');
check(model.save({title: 'Manual series', category: 'series'}, -1), 'Third entry');
check(!model.save({title: 'Fourth', category: 'movies'}, -1), 'Three-title limit');
model.remove(1); model = load();
check(model.list().length === 2 && model.list()[1].title === 'Manual series', 'Removal persists');
var saved = JSON.parse(record);
check(saved.city === 'Brasilia' && saved.tmdbKey === 'test-marker' && saved.shelf[0] === 'existing', 'Other settings preserved');
record = JSON.stringify({continueWatching: [{title: 'Broken', category: 'unknown'}, null]});
check(load().list().length === 0, 'Invalid stored entries ignored');
document.body.textContent = 'PASS_CONTINUE';
"""
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder) / "test.html"
            page.write_text("<!doctype html><body><script>try {" + js + "} catch(e) {document.body.textContent = 'FAIL: ' + e.message;}</script>", encoding="utf-8")
            result = subprocess.run([str(browser), "--headless", "--disable-gpu", "--no-first-run",
                                     "--user-data-dir=" + str(Path(folder) / "profile"), "--dump-dom", page.as_uri()],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.assertEqual(result.returncode, 0, result.stderr[-1000:])
            self.assertIn("<body>PASS_CONTINUE</body>", result.stdout)
