"""Offline browser checks: mock AniList, never contact its servers or write dist/."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AnimeTests(unittest.TestCase):
    def test_cache_failure_and_favorites(self):
        browser = Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"
        if not browser.is_file():
            self.skipTest("Installed Chrome required for offline JS checks")
        source = (ROOT / "web/anime.js").read_text(encoding="utf-8")
        home = (ROOT / "web/home.js").read_text(encoding="utf-8")
        pick = home[home.index("  function pickShelf()"):home.index("  // MARK: - Focus")]
        priority = home[home.index("  var PRIORITY_APPS"):home.index(";", home.index("  var PRIORITY_APPS")) + 1]
        tv = (ROOT / "web/tv.js").read_text(encoding="utf-8")
        samsung = tv[tv.index("  function samsungApp(a)"):tv.index("\n  /**", tv.index("  function samsungApp(a)"))]
        js = r"""
function check(ok, message) { if (!ok) throw Error(message); }
var record = null, calls = 0, behavior = 'success', denied = false, timeout = 0, payload, styled = true;
var reduced = false, clock, page, imageLoads = 0;
var root = document.createElement('section');
root.innerHTML = '<img class="anime-art"><h2></h2><p class="anime-info"></p><div class="anime-dots"></div>';
root.nodes = {};
['h2', '.anime-info'].forEach(function(s) { root.nodes[s] = root.querySelector(s); });
function FakeImage() {
  var image = document.createElement('img');
  Object.defineProperty(image, 'src', {get: function() { return this.testSrc; }, set: function(v) {
    this.testSrc = v; imageLoads++; this.onload();
  }});
  return image;
}
var storage = {getItem: function() { if (denied) throw Error('denied'); return record; },
 setItem: function(key, value) { if (denied) throw Error('denied'); record = value; }};
function XHR() {}
XHR.prototype.open = function(method, url) { check(method === 'POST' && url === 'https://graphql.anilist.co', 'Endpoint'); };
XHR.prototype.setRequestHeader = function() {};
XHR.prototype.getResponseHeader = function() { return '60'; };
XHR.prototype.send = function(body) {
  calls++; timeout = this.timeout; payload = JSON.parse(body);
  if (behavior === 'waiting') return;
  if (behavior === 'network') { this.onerror(); return; }
  if (behavior === 'timeout') { this.ontimeout(); return; }
  this.status = behavior === '429' ? 429 : 200;
  this.responseText = behavior === 'malformed' ? '{}' : JSON.stringify({data: {Page: {media: [{
    title: {english: '   ', romaji: '<Anime>'}, bannerImage: 'javascript:bad', coverImage: {large: 'https://s4.anilist.co/test.jpg'},
    genres: ['Action'], episodes: 12, averageScore: 80
  }]}}});
  if (behavior === 'success') {
    var data = JSON.parse(this.responseText);
    for (var i = 1; i < 5; i++) data.data.Page.media.push({title: {romaji: 'Anime ' + (i + 1)}, bannerImage: 'https://s4.anilist.co/' + i + '.jpg', genres: ['Drama'], episodes: 12 + i, averageScore: 80 + i});
    this.responseText = JSON.stringify(data);
  }
  if (behavior === 'single') {
    var data = JSON.parse(this.responseText); data.data.Page.media = data.data.Page.media.slice(0, 1);
    this.responseText = JSON.stringify(data);
  }
  if (behavior === 'empty') this.responseText = JSON.stringify({data: {Page: {media: []}}});
  this.onload();
};
function freshModule() {
  clock = {intervals: {}, timeouts: {}, next: 0};
  var c = clock;
  page = {hidden: false, getElementById: function() { return null; }, createElement: document.createElement.bind(document),
    addEventListener: function(name, fn) { this[name] = fn; }};
  return new Function('localStorage', 'XMLHttpRequest', 'window', 'document', SOURCE + '\nreturn SeasonAnime;')(
    storage, XHR, {getComputedStyle: function() { return {position: styled ? 'absolute' : 'static'}; },
      Image: FakeImage, matchMedia: function() { return {matches: reduced}; },
      setInterval: function(fn, delay) { check(delay === 10000, 'Ten second rotation'); c.intervals[++c.next] = fn; return c.next; },
      clearInterval: function(id) { delete c.intervals[id]; },
      setTimeout: function(fn, delay) { check(delay === 160, 'Short transition'); c.timeouts[++c.next] = fn; return c.next; },
      clearTimeout: function(id) { delete c.timeouts[id]; }}, page);
}
function rotate() {
  Object.keys(clock.intervals).forEach(function(id) { clock.intervals[id](); });
  Object.keys(clock.timeouts).forEach(function(id) { var fn = clock.timeouts[id]; delete clock.timeouts[id]; fn(); });
}
root.hidden = true; styled = false; freshModule().init(root);
check(root.hidden && calls === 0, 'Missing CSS cannot expose unstyled content');
styled = true;
var module = freshModule(); module.init(root); module.init(root);
check(calls === 1 && timeout === 8000, 'Single query and timeout');
check(root.nodes.h2.textContent === '<Anime>', 'Text rendered safely');
check(root.querySelector('.anime-art').src === 'https://s4.anilist.co/test.jpg', 'Safe artwork fallback');
check(payload.variables.year === new Date().getFullYear(), 'Current seasonal query');
check(payload.query.indexOf('isAdult: false') >= 0, 'Adult filter');
check(payload.query.indexOf('perPage: 5') >= 0 && JSON.parse(record).items.length === 5, 'Five-item query and cache');
check(JSON.parse(record).items[0].languageAvailability.length === 0, 'AniList cannot confirm PT-BR tracks');
check(root.querySelector('.anime-dots').children.length === 5, 'Five indicators');
check(Object.keys(clock.intervals).length === 1, 'No duplicate rotation timer');
var requestsBefore = calls, imagesBefore = imageLoads;
module.setSuspended(true); module.setSuspended(true);
check(Object.keys(clock.intervals).length === 0, 'Ambient suspends carousel');
module.setFocused(false); page.visibilitychange();
check(Object.keys(clock.intervals).length === 0, 'Ambient remains paused across focus and visibility');
module.setSuspended(false); module.setSuspended(false);
check(Object.keys(clock.intervals).length === 1 && root.nodes.h2.textContent === '<Anime>', 'Ambient resumes one timer without changing index');
rotate();
check(root.nodes.h2.textContent === 'Anime 2' && root.nodes['.anime-info'].textContent.indexOf('13 episódios') >= 0, 'Metadata advances together');
check(root.querySelector('.anime-art').src === 'https://s4.anilist.co/1.jpg', 'Artwork advances with metadata');
check(root.querySelector('.anime-dots').children[1].className === 'current', 'Current indicator');
for (var i = 0; i < 4; i++) rotate();
check(root.nodes.h2.textContent === '<Anime>', 'List wraps in order');
check(calls === requestsBefore && imageLoads === imagesBefore, 'Rotation makes no API or image requests');
module.setFocused(true); module.setFocused(true);
check(Object.keys(clock.intervals).length === 0, 'Focus pauses timer');
module.step(-1); rotate();
check(root.nodes.h2.textContent === 'Anime 5' && root.querySelector('.anime-dots').children[4].className === 'current', 'Manual previous wraps and updates indicator');
module.step(1); rotate();
check(root.nodes.h2.textContent === '<Anime>' && root.classList.contains('anime-focused'), 'Manual next wraps and preserves focus');
check(calls === requestsBefore && imageLoads === imagesBefore, 'Manual navigation has no requests');
page.hidden = true; page.visibilitychange(); page.hidden = false; page.visibilitychange();
check(Object.keys(clock.intervals).length === 0, 'Visible focused page stays paused');
module.setFocused(false); module.setFocused(false);
check(Object.keys(clock.intervals).length === 1, 'Blur resumes exactly one timer');
var films = [{title: 'Filme A', genres: ['Drama'], year: '2026', score: 82, image: ''}, {title: 'Filme B', genres: [], year: '2025', score: null, image: ''}];
films[0].languageAvailability = [{region: 'BR', language: 'pt-BR', audio: true, subtitles: true}];
module.movies(films); module.setFocused(true); module.select('movies');
check(root.textContent.indexOf('Dublado PT-BR') < 0 && root.textContent.indexOf('Legendado PT-BR') < 0, 'Unverified claims never render badges');
check(root.nodes.h2.textContent === 'Filme A' && root.nodes['.anime-info'].textContent.indexOf('2026') >= 0, 'Movies metadata');
module.step(1); rotate(); check(root.nodes.h2.textContent === 'Filme B', 'Movies manual navigation');
module.select('anime'); check(root.nodes.h2.textContent === '<Anime>', 'Anime index preserved');
module.select('movies'); check(root.nodes.h2.textContent === 'Filme B', 'Movie index preserved');
check(root.querySelector('.anime-dots').children.length === 2 && Object.keys(clock.intervals).length === 0, 'Category indicators and focus pause');
module.series([{title: 'Serie A', genres: [], year: '2024', score: 90, image: ''}, {title: 'Serie B', genres: [], year: '2025', score: 80, image: ''}]);
module.select('series'); module.step(1); rotate();
check(root.nodes.h2.textContent === 'Serie B' && root.querySelector('.anime-dots').children[1].className === 'current', 'Series navigation and indicator');
module.select('movies'); check(root.nodes.h2.textContent === 'Filme B', 'Movie index retained after series');
module.select('series'); check(root.nodes.h2.textContent === 'Serie B', 'Independent series index');
module.select('anime'); module.setFocused(false);
check(calls === requestsBefore, 'Category changes make no queries');
page.hidden = true; page.visibilitychange();
check(Object.keys(clock.intervals).length === 0, 'Hidden page stops timer');
page.hidden = false; page.visibilitychange(); page.visibilitychange();
check(Object.keys(clock.intervals).length === 1, 'Visible page resumes one timer');
// Hiding mid-transition cancels the pending swap too.
Object.keys(clock.intervals).forEach(function(id) { clock.intervals[id](); });
page.hidden = true; page.visibilitychange();
check(Object.keys(clock.timeouts).length === 0, 'Hidden page cancels transition');
freshModule().init(root); check(calls === 1, 'Fresh cache avoids request');
var cache = JSON.parse(record); cache.at -= 7 * 3600000; record = JSON.stringify(cache);
behavior = 'timeout'; freshModule().init(root);
check(calls === 2 && root.nodes.h2.textContent === '<Anime>', 'Stale cache survives timeout');
freshModule().init(root); check(calls === 2, 'Failure cooldown');
record = null; behavior = '429'; freshModule().init(root); freshModule().init(root);
check(calls === 3, '429 cooldown across page loads');
check(root.className === 'anime-rate', 'Rate limit is distinct from network failure');
record = null; behavior = 'malformed'; freshModule().init(root);
check(root.nodes.h2.textContent === 'Animes da temporada', 'Invalid response fallback');
denied = true; behavior = 'success'; freshModule().init(root);
check(root.nodes.h2.textContent === '<Anime>', 'Storage denial is safe');
denied = false; record = null; behavior = 'waiting'; freshModule().init(root);
check(root.className === 'anime-loading', 'Loading has its own state');
record = null; behavior = 'empty'; var emptyModule = freshModule(); emptyModule.init(root);
emptyModule.setFocused(true); emptyModule.step(-1); emptyModule.step(1); emptyModule.setFocused(false);
check(Object.keys(clock.intervals).length === 0, 'Empty list never rotates');
check(root.className === 'anime-empty', 'Empty season is distinct from errors');
record = null; behavior = 'network'; freshModule().init(root);
check(root.className === 'anime-network', 'Network or CORS failure is distinct from timeout');
record = null; behavior = 'timeout'; freshModule().init(root);
check(root.className === 'anime-timeout', 'Timeout has its own state');
record = null; behavior = 'single'; var singleModule = freshModule(); singleModule.init(root);
singleModule.setFocused(true); singleModule.step(-1); singleModule.step(1); singleModule.setFocused(false);
check(root.nodes.h2.textContent === '<Anime>', 'Single result ignores manual steps');
check(root.querySelector('.anime-dots').children.length === 1 && Object.keys(clock.intervals).length === 0, 'One result has one indicator and no timer');
record = null; behavior = 'success'; reduced = true; freshModule().init(root); rotate();
check(root.nodes.h2.textContent === 'Anime 2' && Object.keys(clock.timeouts).length === 0, 'Reduced motion swaps without transition');
var st = {}, CONFIG = {}, WANTED = [], SHELF = [], FEW_APPS = 8;
var selection = null, Prefs = {shelf: function() { return selection; }};
var apps = [{id: 'real-c', title: 'Crunchyroll'}, {id: 'real-m', title: 'YouTube Music'}, {id: 'real-y', title: 'YouTube'}];
var shelf, others;
"""
        js = "var SOURCE = " + json.dumps(source) + ";\n" + js + priority + pick
        js += r"""
pickShelf(); check(shelf.map(function(a) { return a.id; }).join(',') === 'real-y,real-c', 'Discovered-only priority');
selection = ['real-c', 'real-y']; pickShelf(); check(shelf[0].id === 'real-c' && shelf.length === 2, 'Manual favorites win');
selection = []; pickShelf(); check(shelf.length === 0, 'Empty manual selection preserved');
WANTED = ['music']; selection = null;
Prefs.shelfConfig = function() { return 'music'; };
pickShelf(); check(shelf[0].id === 'real-m', 'Explicit config wins');
selection = ['real-c']; Prefs.shelfConfig = function() { return ''; }; Prefs.set = function() { throw Error('Manual favorites must not be reset'); };
pickShelf(); check(shelf.length === 1 && shelf[0].id === 'real-c', 'Build changes never erase saved favorites');
WANTED = []; selection = null; apps = PRIORITY_APPS.map(function(p, i) { return {id: p[0], title: 'Discovered ' + i}; }).reverse();
pickShelf(); check(shelf.map(function(a) { return a.id; }).join(',') === PRIORITY_APPS.map(function(p) { return p[0]; }).join(','), 'Exact DU8000 ID priority');
apps = [apps[0]]; pickShelf(); check(shelf.length === 1, 'Missing apps never fabricated');
apps = [{id: 'netflix', title: 'Netflix'}, {id: 'disney', title: 'Disney+'}];
WANTED = ['missing']; pickShelf(); check(shelf.length === 0, 'Unmatched explicit config never fills vacancies');
WANTED = []; pickShelf(); check(shelf.length === 0, 'Nonpriority apps never fill defaults');
selection = ['netflix']; pickShelf(); check(shelf.length === 1 && shelf[0].id === 'netflix', 'Explicit extra favorite is respected');
selection = null;
apps = []; pickShelf(); check(shelf.length === 0 && others.length === 0, 'Empty discovery stays empty');
"""
        maps = tv[tv.index("  var SAMSUNG_ICONS ="):tv.index("  // Samsung's settings menu")]
        js += maps + "\nvar samsungDial = {};\n" + samsung
        js += r"""
var installed = samsungApp({id: 'real-y', name: 'YouTube', iconPath: '/opt/apps/icon.png'});
check(installed.icon === 'icons/youtube.png', 'Approved local YouTube logo takes priority');
check(installed.fallbackIcon === 'icons/youtube.png', 'Local fallback retained');
check(samsungApp({id: 'real-y', name: 'YouTube', iconPath: 'javascript:bad'}).icon === 'icons/youtube.png', 'Unsafe icon rejected');
[['9Ur5IzDKqV.TizenYouTube','icons/youtube.png'],['OGLLvqej7u.CrunchyrollWebApp','icons/crunchyroll.svg'],['org.tizen.primevideo','icons/prime.png']].forEach(function(pair){
 var app=samsungApp({id:pair[0],name:'Generic name',iconPath:'/opt/generic-tizen.png'});
 check(app.id===pair[0]&&app.icon===pair[1],'Real ID retained with local logo');
});
['LnLzvqrcEY.globo','AQKO41xyKP.AmazonAlexa','org.tizen.browser'].forEach(function(id){
 var app=samsungApp({id:id,name:'Generic name',iconPath:'/opt/generic-tizen.png'});
 check(app.id===id&&app.icon===''&&app.title!=='Generic name','Known app without local logo uses readable name');
});
check(samsungApp({id:'unknown.installed',name:'Other app',iconPath:'/opt/valid.png'}).icon==='file:///opt/valid.png','Unknown app keeps valid Tizen icon');
check(samsungApp({id:'unknown.installed',name:'YoutubeTV',iconPath:'https://outside.invalid/icon.png'}).icon==='','No external icon or partial-name match');

"""
        data_source = (ROOT / "web/data.js").read_text(encoding="utf-8")
        movie_source = data_source[data_source.index("  // Independent editorial highlights:"):data_source.index("  var cache = stored('recs')")]
        js += r"""
var movieStored = {}, movieCalls = [], movieFault = false, updates = 0, missingFields = false;
var KEY = true;
function stored(key) { return movieStored[key] || null; }
function store(key, value) { movieStored[key] = JSON.parse(JSON.stringify(value)); }
function changed() { updates++; }
function tmdb(path, done) {
 movieCalls.push(path);
 if (movieFault) { done(Error('network')); return; }
 if (path.indexOf('/genre/') === 0) done(null, {genres: [{id: 18, name: 'Drama'}]});
 else done(null, {results: [{name: missingFields ? null : 'Serie de teste', first_air_date: '2024-02-01',
   title: missingFields ? ' ' : 'Filme de teste', original_title: 'Original movie', original_name: 'Original series',
   overview: missingFields ? null : 'Uma sinopse retornada em portugues.',
   original_language: 'pt', spoken_languages: [{iso_639_1: 'pt'}],
   languageAvailability: [{region: 'BR', language: 'pt-BR', audio: true}],
   backdrop_path: '/test.jpg', genre_ids: missingFields ? null : [18], release_date: '2026-01-01', vote_average: 8.2}]});
}
""" + movie_source + r"""
movies.refresh();
check(movieCalls.length === 2 && movies.read().items[0].genres[0] === 'Drama' && movies.read().items[0].year === '2026', 'Movie metadata');
check(movies.read().items[0].overview === 'Uma sinopse retornada em portugues.' && movies.read().items[0].languageAvailability.length === 0, 'Localized overview retained without inferring tracks');
series.refresh();
check(movieCalls.length === 4 && series.read().items[0].title === 'Serie de teste' && series.read().items[0].year === '2024', 'Series name and first air year');
check(series.read().items[0].score === 82 && movieCalls.every(function(p) { return p.indexOf('language=pt-BR') >= 0; }), 'Portuguese metadata');
check(movieCalls.some(function(p) { return p.indexOf('/genre/tv/') === 0; }), 'Series genres use tv endpoint');
movies.refresh(); series.refresh(); check(movieCalls.length === 4, 'Both six-hour caches');
var reloaded = highlights('tv'); reloaded.refresh();
check(reloaded.read().items.length === 1 && movieCalls.length === 4, 'Persistent series cache');
movieStored.tvHighlights.at -= 7 * 3600000; movieFault = true;
var staleSeries = highlights('tv'); staleSeries.refresh();
check(staleSeries.read().items.length === 1 && staleSeries.read().error && movieCalls.length === 5, 'Stale series survive failure');
staleSeries.refresh(); check(movieCalls.length === 5, 'Series failure cooldown');
KEY = false; movies.refresh(); series.refresh();
check(movies.read().items.length === 0 && series.read().items.length === 0 && movieCalls.length === 5, 'No key means no TMDB requests');
KEY = true; movieFault = false; missingFields = true;
movies.reset(); series.reset();
check(movies.read().items[0].title === 'Original movie' && series.read().items[0].title === 'Original series', 'Original title fallback without translating');
check(movies.read().items[0].overview === '' && movies.read().items[0].genres.length === 0, 'Missing overview and genres stay empty');
movieStored.tvHighlights.items[0].languageAvailability = [{region: 'BR', language: 'pt-BR', subtitles: true}];
var untrusted = highlights('tv'); untrusted.refresh();
check(untrusted.read().items[0].languageAvailability.length === 0, 'Cached track claims rejected');
"""
        html = '<!doctype html><script>try {\n' + js + "\ndocument.body.textContent = 'PASS_ANIME'; } catch(e) { document.body.textContent = 'FAIL: ' + e.message; }</script>"
        # The body must exist before the synchronous harness runs.
        html = html.replace('<script>', '<body><script>', 1)
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "test.html"
            page.write_text(html, encoding="utf-8")
            result = subprocess.run([str(browser), '--headless', '--disable-gpu', '--no-first-run',
                                     '--user-data-dir=' + str(Path(directory) / 'profile'), '--dump-dom', page.as_uri()],
                                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=45,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertEqual(result.returncode, 0, result.stderr[-1000:])
            self.assertIn('<body>PASS_ANIME</body>', result.stdout)
