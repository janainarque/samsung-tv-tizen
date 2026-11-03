"""Ambient timing/input behavior, using production functions with a virtual clock."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AmbientTests(unittest.TestCase):
    def test_idle_wake_and_suspension(self):
        browser = Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"
        if not browser.is_file():
            self.skipTest("Installed Chrome required")
        home = (ROOT / "web/home.js").read_text(encoding="utf-8")
        ambient = home[home.index("  var ambientOn ="):home.index("  var highlightTabs =")]
        keys = home[home.index("  document.addEventListener('keydown'"):home.index("  /**\n   * In a text field")]
        js = r"""
function check(ok,message){if(!ok)throw Error(message);}
var realDocument=document, NativeDate=window.Date, now=1000000, next=0, jobs={};
var Date=function(){return new NativeDate(now);};Date.now=function(){return now;};
function setTimeout(fn,ms){jobs[++next]={fn:fn,at:now+ms,period:0};return next;}
function clearTimeout(id){delete jobs[id];}
function setInterval(fn,ms){jobs[++next]={fn:fn,at:now+ms,period:ms};return next;}
function clearInterval(id){delete jobs[id];}
function advance(ms){var end=now+ms;while(true){var id=null;
 Object.keys(jobs).forEach(function(k){if(jobs[k].at<=end&&(id===null||jobs[k].at<jobs[id].at))id=k;});
 if(id===null)break;var job=jobs[id];now=job.at;if(job.period)job.at+=job.period;else delete jobs[id];job.fn();}now=end;}
var listeners={},document={hidden:false,addEventListener:function(name,fn){listeners[name]=fn;}};
function $(id){return realDocument.getElementById(id);}
function el(tag,cls,parent){var n=realDocument.createElement(tag);n.className=cls;parent.appendChild(n);return n;}
function setClass(node,name,on){node.classList.toggle(name,on);}
function formatDate(pattern,time){return pattern.indexOf('h:mm')>=0?'12:34':'segunda-feira';}
var enabled=true, minutes=5, modal=false, attentionPending=0, focused={zone:'shelf',shelf:3};
var Prefs={ambientEnabled:function(){return enabled;},ambientMinutes:function(){return minutes;},weather:function(){return true;},saverWatch:function(){return false;}};
var Data={city:'Brasília',weather:{temp:22,code:0,isDay:1},degrees:function(t){return t+' C';},condition:function(){return 'Limpo';},symbol:function(){return 'clear_day';}};
var pauses=[],SeasonAnime={setSuspended:function(value){pauses.push(value);}};
var saverOn=false,saverPick=null,idleAt=now,idleTimer=0,actions=0,updates=0;
function sheetOpen(){return modal;}function hideSaver(){saverOn=false;}
function renderClock(){}
function updateFocus(){updates++;}function renderAll(){updates++;}
var TV={keys:{left:37,right:39,up:38,down:40,ok:13,back:10009}};
function typing(){return false;}function activate(){actions++;}function move(){actions++;}function back(){actions++;}
function event(code){return {keyCode:code,prevented:false,stopped:false,preventDefault:function(){this.prevented=true;},stopImmediatePropagation:function(){this.stopped=true;}};}
""" + ambient + keys + r"""
scheduleAmbient();advance(299999);check(!ambientOn,'Not before five minutes');
advance(1);check(ambientOn&&pauses[0]===true,'Five-minute activation pauses highlights');
check($('ambient').textContent.indexOf('12:34')>=0&&$('ambient').textContent.indexOf('Limpo')>=0,'Existing clock/weather rendered');
check($('ambient').querySelector('.shift').firstChild.className==='date' && $('ambient').querySelector('.city').textContent==='Brasília','Centered composition content order and city');
var position=$('ambient').querySelector('.shift').style.transform;advance(60000);
check(position!==$('ambient').querySelector('.shift').style.transform,'Minute drift');
var first=event(13);listeners.keydown(first);
check(!ambientOn&&first.prevented&&actions===0&&focused.shelf===3,'First OK consumed and focus retained');
listeners.keydown(event(13));check(actions===0,'Held wake key cannot activate');
listeners.keyup(event(13));listeners.keydown(event(13));check(actions===1,'Next press works');
advance(240000);poke();advance(299999);check(!ambientOn,'Interaction resets deadline');advance(1);check(ambientOn,'New idle deadline');
poke();modal=true;advance(300000);check(!ambientOn,'Modal blocks activation');modal=false;
attentionPending=1;advance(300000);check(!ambientOn,'Pending operation blocks activation');attentionPending=0;
document.hidden=true;scheduleAmbient();advance(300000);check(!ambientOn,'Hidden page cannot activate');
document.hidden=false;idleAt=now;scheduleAmbient();advance(300000);check(ambientOn,'Visible page resumes fresh countdown');
var home=event(10182);listeners.keydown(home);check(!ambientOn&&!home.prevented,'Home system key not prevented');listeners.keyup(home);
showAmbient();var pointer=event();listeners.mousedown(pointer);check(!ambientOn&&pointer.prevented&&pointer.stopped,'Pointer wake consumed');
var click=event();listeners.click(click);check(click.stopped,'First click suppressed');
advance(701);var normal=event();listeners.click(normal);check(!normal.stopped,'Later click allowed');
enabled=false;scheduleAmbient();advance(300000);check(!ambientOn,'Disabled Ambient stays off');
enabled=true;idleAt=now;scheduleAmbient();scheduleAmbient();
check(Object.keys(jobs).length===1,'Single idle timer');
realDocument.body.textContent='PASS_AMBIENT';
"""
        with tempfile.TemporaryDirectory() as folder:
            page = Path(folder) / "test.html"
            page.write_text('<!doctype html><body><div id="ambient"></div><script>(function(document){try {' + js + "} catch(e) {realDocument.body.textContent='FAIL: '+e.message;}})(document)</script>", encoding="utf-8")
            result = subprocess.run([str(browser), "--headless", "--disable-gpu", "--no-first-run",
                                     "--user-data-dir=" + str(Path(folder) / "profile"), "--dump-dom", page.as_uri()],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.assertIn("<body>PASS_AMBIENT</body>", result.stdout)
