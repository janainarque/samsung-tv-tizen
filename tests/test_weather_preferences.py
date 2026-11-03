"""Weather defaults and saved city behavior in an isolated Chrome profile."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WeatherPreferencesTests(unittest.TestCase):
    def test_default_manual_city_and_persistence(self):
        browser = Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"
        if not browser.is_file():
            self.skipTest("Installed Chrome required")
        source = (ROOT / "web/data.js").read_text(encoding="utf-8")
        preferences = source[:source.index("var Data = (function")]
        weather = source[source.index("  function place()"):source.index("  /** Places with this name")]
        script = "var SOURCE = " + json.dumps(preferences) + ";\n"
        script += "var WEATHER = " + json.dumps(weather) + ";\n"
        script += r"""
function check(ok, message) { if (!ok) throw Error(message); }
var record = null, writes = 0;
var storage = {getItem: function(key) { check(key === 'fmtv.prefs', 'Preferences key'); return record; },
 setItem: function(key, value) { record = value; writes++; }};
function load(config, zone) {
 return new Function('window', 'TV', 'I18N', 'localStorage', 'navigator', SOURCE + '\nreturn Prefs;')(
  {CONFIG: config || {}, ZONES: {'America/Sao_Paulo': 'BR,-23.53,-46.62,São Paulo'}},
  {zone: function() { return zone || 'America/Sao_Paulo'; }}, {}, storage, {language: 'pt-BR'});
}
var prefs = load();
check(prefs.city() === 'Brasília' && prefs.latitude() === '-15.7939' && prefs.longitude() === '-47.8828', 'Brasilia default');
check(writes === 0 && record === null, 'Default never writes preferences');
check(prefs.ambientEnabled() && prefs.ambientMinutes() === 5, 'Ambient defaults without preference migration');
prefs.set('ambientEnabled', false); prefs.set('ambientMinutes', 10);
check(!load().ambientEnabled() && load().ambientMinutes() === 10, 'Ambient settings persist');
check(load({}, 'Unknown/Zone').city() === 'Brasília', 'Default independent of zone city');
record = JSON.stringify({city: 'São Paulo', latitude: '-23.53', longitude: '-46.62', theme: 'dark', tmdbKey: 'test-marker'});
prefs = load();
check(prefs.city() === 'São Paulo' && prefs.latitude() === '-23.53', 'Saved Sao Paulo is not migrated');
var before = JSON.parse(record);
prefs.setCity('Brasília', '-15.7939', '-47.8828');
var saved = JSON.parse(record);
check(saved.tmdbKey === before.tmdbKey && saved.theme === before.theme, 'City change preserves other preferences');
prefs = load();
check(prefs.city() === 'Brasília' && prefs.longitude() === '-47.8828', 'Manual choice survives reload');
prefs.setCity('Recife', '-8.0476', '-34.8770');
prefs = load({city: 'Configured', latitude: '1', longitude: '2'});
check(prefs.city() === 'Recife' && prefs.latitude() === '-8.0476', 'Saved custom city wins over build config');
record = null;
prefs = load({city: 'Configured', latitude: '1', longitude: '2'});
check(prefs.city() === 'Configured' && prefs.longitude() === '2', 'Explicit build config preserved');
prefs = load();
var url = '';
new Function('Prefs', 'stored', 'getMeteo', 'changed', WEATHER + '\nrefreshWeather();')(
 prefs, function() { return null; }, function(value) { url = value; }, function() {});
check(url.indexOf('latitude=-15.7939&longitude=-47.8828') >= 0 && url.indexOf('timezone=auto') >= 0, 'Existing weather API uses Brasilia coordinates');
document.body.textContent = 'PASS_WEATHER';
"""
        page_html = "<!doctype html><body><script>try {\n" + script + "\n} catch(e) { document.body.textContent = 'FAIL: ' + e.message; }</script>"
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder) / "test.html"
            page.write_text(page_html, encoding="utf-8")
            result = subprocess.run(
                [str(browser), "--headless", "--disable-gpu", "--no-first-run",
                 "--user-data-dir=" + str(Path(folder) / "profile"), "--dump-dom", page.as_uri()],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.assertEqual(result.returncode, 0, result.stderr[-1000:])
            self.assertIn("<body>PASS_WEATHER</body>", result.stdout)
