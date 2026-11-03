"""Behavior checks in an installed Chrome, without npm or third-party packages."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TopActionsTests(unittest.TestCase):
    def test_exit_symbol_is_packaged(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import webapp
        files = webapp.files(dict(webapp.GENERIC), "test")
        self.assertEqual(files["symbols/logout.png"], (ROOT / "web/symbols/logout.png").read_bytes())
        self.assertTrue(files["symbols/logout.png"].startswith(b"\x89PNG\r\n\x1a\n"))

    def test_navigation_rendering_and_exit_adapter(self):
        browser = shutil.which("google-chrome") or shutil.which("chromium")
        if not browser:
            for base in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", "")):
                candidate = Path(base) / "Google/Chrome/Application/chrome.exe"
                if candidate.is_file():
                    browser = str(candidate)
                    break
        if not browser:
            self.skipTest("Chrome/Chromium not installed; browser behavior test unavailable")

        home = (ROOT / "web/home.js").read_text(encoding="utf-8")
        tv = (ROOT / "web/tv.js").read_text(encoding="utf-8")
        # Exercise the production functions with a minimal DOM and TV stubs.
        actions = home[home.index("  var TOP_ACTIONS"):home.index("];", home.index("  var TOP_ACTIONS")) + 2]
        render = home[home.index("  function renderTop()"):home.index("  function renderQuotes()")]
        activate = home[home.index("  function activate()"):home.index("  function selectTab(")]
        move = home[home.index("  function move(dx, dy)"):home.index("  function back()")]
        setup = r"""
function check(ok, message) { if (!ok) throw new Error(message); }
var $ = function(id) { return document.getElementById(id); };
var Z = {TOP: 'top', SHELF: 'shelf', CARDS: 'cards', ANIME: 'anime', HIGHLIGHT: 'highlight', WATCH: 'watch', DRAWER: 'drawer'};
var highlightCategory = 0, highlightTab = 0, selectedCategory = '', animeOn = false, step = 0, SeasonAnime = {step: function(dx) { step += dx; }, select: function(kind) { selectedCategory = kind; }};
function animeVisible() { return animeOn; }
function shelfSize() { return shelf.length + 1; }
var watchCursor = 0, ContinueWatching = {list: function() { return [{}, {}]; }};
var st = {zone: Z.TOP, top: 3, tab: 0};
var keyed = false, Data = {hasKey: function() { return keyed; }};
var shelf = [{}], cards = [], drawerInputs = 2, recorded = '', message = '';
function tr(text) { return text.split('|').pop(); }
function el(tag, cls, parent, text) {
  var node = document.createElement(tag); node.className = cls;
  if (text) node.textContent = text; parent.appendChild(node); return node;
}
function sym(name, parent) { el('span', 'sym', parent).dataset.symbol = name; }
function hover(node, zone, index) { node.dataset.index = index; }
function updateFocus() {}
var attentionPending = 0, idleAt = 0; function scheduleAmbient() {}
function selectTab(index) { st.tab = index; }
function openSettings() { recorded = 'settings'; }
function openDrawer() { recorded = 'hdmi'; }
function liveTV() { return {id: 'existing-live-id'}; }
function launcher(id) { return function() { recorded = id; }; }
function toast(text) { message = text; }
"""
        checks = r"""
renderTop();
check($('buttons').children.length === 4, 'Four actions must render');
for (var i = 0; i < 4; i++) {
  var node = $('buttons').children[i];
  check(Number(node.dataset.index) === 3 + i, 'Focus index');
  var left = parseInt(node.style.left, 10);
  check(left >= 0 && left + 68 * 1.1 < 1920, 'Visible focused button');
}
check($('buttons').lastChild.classList.contains('last'), 'Right-aligned tooltip');
check($('buttons').lastChild.textContent === 'Samsung Original', 'Exit tooltip');
move(1, 0); move(1, 0); move(1, 0);
check(st.top === 6, 'Fourth action reachable');
move(1, 0); check(st.top === 6, 'Right boundary');
move(-1, 0); check(st.top === 5, 'Return to Settings');
st.top = 3; move(-1, 0); check(st.top === 3, 'Hidden tabs skipped');
keyed = true; move(-1, 0); check(st.top === 2, 'Visible tabs reachable');
st.top = 6; move(0, 1); check(st.zone === Z.SHELF, 'Down returns to shelf');
move(0, -1); check(st.zone === Z.TOP, 'Up returns to actions');
animeOn = true; st.zone = Z.SHELF; move(0, -1); check(st.zone === Z.ANIME, 'Shelf enters anime');
move(1, 0); move(-1, 0); check(step === 0 && st.zone === Z.ANIME, 'Anime arrows stay in zone');
move(0, -1); check(st.zone === Z.HIGHLIGHT, 'Anime up enters category tabs');
keyed = false; move(1, 0); check(highlightTab === 0, 'Missing key skips disabled Movies');
keyed = true; move(1, 0); check(highlightTab === 1, 'Movies reachable with key');
activate(); check(selectedCategory === 'movies', 'OK confirms category');
move(1, 0); activate(); check(selectedCategory === 'series' && highlightTab === 2, 'Third tab confirms series');
move(1, 0); check(highlightTab === 2, 'Third tab right boundary');
move(-1, 0); activate(); check(selectedCategory === 'movies', 'Return from series to movies');
move(0, -1); check(st.zone === Z.TOP, 'Tabs up enters actions');
move(0, 1); check(st.zone === Z.HIGHLIGHT, 'Actions down enters tabs');
move(0, 1); check(st.zone === Z.ANIME, 'Tabs down enters anime');
move(0, 1); check(st.zone === Z.SHELF, 'Anime down returns to shelf');
st.zone = Z.TOP; st.top = 3; activate(); check(recorded === 'existing-live-id', 'Live TV unchanged');
st.top = 4; activate(); check(recorded === 'hdmi', 'HDMI unchanged');
st.zone = Z.TOP; st.top = 5; activate(); check(recorded === 'settings', 'Settings unchanged');
st.top = 6; activate(); check(message.length > 0, 'Browser fallback');
st.zone = Z.DRAWER; move(0, 1); check(st.zone === Z.WATCH, 'Drawer down enters watch list');
move(1, 0); check(watchCursor === 1, 'Edit action reachable');
move(0, 1); check(watchCursor === 3, 'Next entry edit action');
move(0, -1); move(0, -1); check(st.zone === Z.DRAWER, 'Watch list up returns shortcuts');
"""
        adapter_checks = r"""
check(TV.exitApplication() === false, 'No Tizen API is safe');
var exits = 0, hides = 0;
window.tizen = {application: {getCurrentApplication: function() {
  return {exit: function() { exits++; }, hide: function() { hides++; }};
}}};
eval(TV_SOURCE);
check(TV.exitApplication() === true && exits === 1, 'One explicit exit call');
TV.back(); check(hides === 1 && exits === 1, 'Back still hides');
window.tizen.application.getCurrentApplication = function() { throw new Error('denied'); };
check(TV.exitApplication() === false, 'API exception is safe');
window.tizen.application.getCurrentApplication = function() { return {}; };
check(TV.exitApplication() === false, 'Missing exit method is safe');
document.body.textContent = 'PASS_TOP_ACTIONS';
"""
        script = "try {\n" + tv + setup + actions + render + activate + move + checks
        script += "\nvar TV_SOURCE = " + json.dumps(tv) + ";\n" + adapter_checks
        script += "\n} catch (error) { document.body.textContent = 'FAIL: ' + error.message; }"
        html = '<!doctype html><div id="title"></div><div id="tabs"></div><div id="buttons"></div><div id="tiles"></div><div id="cards"></div><script>'
        html += script.replace("</script", "<\\/script") + '</script>'
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder) / "test.html"
            page.write_text(html, encoding="utf-8")
            result = subprocess.run(
                [browser, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                 "--user-data-dir=" + str(Path(folder) / "profile"), "--dump-dom", page.as_uri()],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            self.assertIn('<body>PASS_TOP_ACTIONS</body>', result.stdout)


if __name__ == "__main__":
    unittest.main()
