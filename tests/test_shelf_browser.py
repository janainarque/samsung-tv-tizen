"""Full Home keyboard checks with explicitly simulated discovery, never TV access."""
import functools
import http.server
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ShelfBrowserTests(unittest.TestCase):
    def test_selector_focus_and_manual_favorites(self):
        browser = Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"
        if not browser.is_file():
            self.skipTest("Installed Chrome required")
        sys.path.insert(0, str(ROOT / "scripts"))
        import webapp
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            for name, data in webapp.files(dict(webapp.GENERIC), "shelf-test").items():
                target = out / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            page = out / "index.html"
            page.write_text(page.read_text(encoding="utf-8").replace(
                '<script src="tv.js"></script>',
                '<script src="tv.js"></script><script>'
                'window.XMLHttpRequest=function(){this.open=function(){};this.setRequestHeader=function(){};'
                'this.send=function(){if(this.onerror)this.onerror();};};'
                '</script>'), encoding="utf-8")
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=folder))
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                for width, height in [(1920, 1080), (1280, 720)]:
                    with self.subTest(resolution=(width, height)):
                        script = r"""
f.onload=function(){var w=f.contentWindow,d=f.contentDocument;
function check(ok,message){if(!ok)throw Error(message);}
function key(k){d.dispatchEvent(new w.KeyboardEvent('keydown',{keyCode:k,which:k,bubbles:true}));}
setTimeout(function(){try{
var tiles=d.querySelectorAll('#tiles .tile');
check(tiles.length===7,'Six apps plus separate action');
check(tiles[0].textContent==='YouTube'&&tiles[4].textContent==='Amazon Alexa'&&tiles[5].textContent==='Browser','Priority order');
check(tiles[6].classList.contains('all-apps'),'Last tile is action');
var rect=tiles[1].getBoundingClientRect();
check(Math.abs(rect.width-178*WIDTH/1920)<1,'Approved tile width preserved');
for(var i=0;i<6;i++)key(39);key(13);
check(d.querySelector('#apps').classList.contains('open'),'Selector opens');
check(d.querySelectorAll('#apps .cell').length>6,'Selector includes other demo apps');
check(d.querySelector('#apps h2').textContent.indexOf('Chrome')>=0,'Demo source identified');
key(39);key(40);check(!!d.querySelector('#apps .cell.focus'),'Selector arrow navigation');
key(27);check(tiles[6].classList.contains('focus'),'Back restores all-apps focus');
check(w.Prefs.shelf()===null,'Opening selector does not save favorites');
// Use the existing editor via Settings, reached through the top actions.
key(38);key(38);key(38);key(39);key(39);key(13);
check(d.querySelector('#settings').classList.contains('open'),'Settings reachable');
var rows=d.querySelectorAll('#settings .row'),target=-1;
for(var i=0;i<rows.length;i++)if(rows[i].textContent.indexOf('Prateleira')>=0||rows[i].textContent.indexOf('Shelf')>=0)target=i;
check(target>=0,'Shelf editor exists');
for(var i=0;i<target;i++)key(40);key(13);key(13);
var saved=w.Prefs.shelf();check(saved.length===5&&saved.every(function(id){return id.indexOf('all-apps')<0;}),'Action never saved as favorite');
check(d.querySelectorAll('#tiles .all-apps').length===1,'Action survives manual edits');
key(27);key(27);
// Apply the preset deliberately, preserving unrelated settings.
w.Prefs.set('city','Preserved city'); w.Prefs.set('theme','dark');
d.querySelectorAll('#buttons .round')[2].click();
var preset=Array.prototype.filter.call(d.querySelectorAll('#settings .row'),function(row){return row.textContent.indexOf('Aplicar os seis')>=0;})[0];
check(!!preset,'Preset action offered');preset.click();
check(w.Prefs.shelf().length===6,'Preset restores six available examples');
check(w.Prefs.city()==='Preserved city'&&w.Prefs.theme()==='dark','Other preferences preserved');
check(d.querySelectorAll('#tiles .tile').length===7,'Six examples plus fixed action');
var order=Array.prototype.map.call(d.querySelectorAll('#tiles .tile'),function(tile){return tile.textContent;});
check(order.slice(0,6).join('|')==='YouTube|Crunchyroll|Globoplay|Prime Video|Amazon Alexa|Browser','Actual Chrome SAMPLE default order');
var savedOrder=w.Prefs.shelf().join('|');
check(JSON.parse(w.localStorage.getItem('fmtv.prefs')).shelf.join('|')===savedOrder,'Preset is persisted');
check(savedOrder.indexOf('preview:amazon-alexa')>=0,'Preview Alexa uses demo identifier');
key(27);

check(d.querySelectorAll('#featured-games .game').length===3,'Three internal demo games');
check(d.querySelector('#featured-games').textContent.indexOf('Demonstra')>=0,'Demo games explicitly labeled');
key(40);key(40);check(w.FreeMyTV.state.zone==='games'&&d.body.classList.contains('drawer-games'),'Empty watch list allows down into games');
key(39);check(d.querySelectorAll('#featured-games .game')[1].classList.contains('focus'),'Game horizontal focus');
key(13);check(d.querySelector('#toast').textContent.indexOf('Exemplo interno')>=0,'OK only explains demo');
key(27);check(w.FreeMyTV.state.zone==='drawer'&&!d.body.classList.contains('drawer-games'),'Back restores drawer scroll');
key(27);check(w.FreeMyTV.state.zone==='shelf','Second back restores shelf');
w.ContinueWatching.save({title:'Manual test entry',category:'movies'},-1);
key(40);key(40);check(w.FreeMyTV.state.zone==='watch','Watch navigation preserved');
key(40);check(w.FreeMyTV.state.zone==='games','Watch down reaches games');
key(38);check(w.FreeMyTV.state.zone==='watch','Game up returns watch list');
key(40);
setTimeout(function(){try{
var rects=Array.prototype.map.call(d.querySelectorAll('#featured-games .game'),function(e){return e.getBoundingClientRect();});
check(rects.every(function(r){return r.left>=0&&r.right<=WIDTH&&r.top>=0&&r.bottom<=HEIGHT;}),'All games fit after controlled scroll '+w.FreeMyTV.state.zone+' '+d.body.className+' '+w.getComputedStyle(d.querySelector('#drawer')).transform+': '+JSON.stringify(rects.map(function(r){return [r.x,r.y,r.width,r.height];})));
var p=document.createElement('pre');p.id='result';p.textContent='PASS_SHELF';document.body.appendChild(p);
}catch(e){document.body.textContent='FAIL: '+e.message;}},500);

}catch(e){document.body.textContent='FAIL: '+e.message;}},1200);};
""".replace("WIDTH", str(width)).replace("HEIGHT", str(height))
                        wrapper = '<body style="margin:0"><iframe id="f" src="index.html" style="border:0;width:%dpx;height:%dpx"></iframe><script>%s</script>' % (width, height, script)
                        (out / "check.html").write_text(wrapper, encoding="utf-8")
                        result = subprocess.run([str(browser), "--headless", "--disable-gpu", "--no-first-run", "--force-prefers-reduced-motion",
                                                 "--user-data-dir=" + str(out / ("profile" + str(width))),
                                                 "--window-size=%d,%d" % (width + 22, height + 154),
                                                 "--virtual-time-budget=3500", "--dump-dom",
                                                 "http://127.0.0.1:%d/check.html" % server.server_port],
                                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45,
                                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                        self.assertIn('<pre id="result">PASS_SHELF</pre>', result.stdout)
            finally:
                server.shutdown()
                server.server_close()
