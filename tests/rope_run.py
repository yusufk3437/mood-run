"""Browser regression checks. Test hooks are injected into the response only."""
import functools
import http.server
import os
from pathlib import Path
import shutil
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/"
hooks = """
window.__inspect=()=>({state,isMulti,round,lives,score,coins,runCoins,bankedCoins,
 team:{...team},targetX,finished:teamFinished,rope:teamRope.visible,
 p:{x:player.position.x,z:player.position.z},o:{x:opp.position.x,z:opp.position.z},
 width:LW*3*platform.scale.x,bound:moveBound(),passed:team.lastGate,
 rows:gates.map(r=>({id:r.userData.id,req:r.userData.req,
 lanes:r.children.filter(c=>c.userData.isGate).map(c=>({...c.userData}))}))});
window.__attach=host=>{isMulti=true;isHost=host;myName=host?'Ada':'Ben';oppName=host?'Ben':'Ada';
 conn={open:true,send:d=>window.__sendPeer(d),on:(event,fn)=>{
 if(event==='data')window.__receivePeer=fn;if(event==='close')window.__closePeer=fn
 },close:()=>{conn.open=false;window.__closePeer()}};setupConn(conn)};
window.__freeTrack=()=>{gates.forEach(g=>scene.remove(g));gates=[];spawned=1000000};
window.__targets=x=>{targetX=clamp(x,-moveBound(),moveBound())};
window.__breakPeer=()=>conn.close();
window.__cross=(hx,gx,req)=>{gates.forEach(g=>scene.remove(g));gates=[];
 const q=constrainTeam(hx,gx);team.hx=q.hx;team.gx=q.gx;targetX=q.hx;team.guestTarget=q.gx;
 player.position.x=q.hx;opp.position.x=q.gx;
 spawnGateRow(team.z-.5,0,{sequence:[req],gates:[['smile','neutral','sad']]},team.lastGate+1)};
window.__soloGate=()=>{gates.forEach(g=>scene.remove(g));gates=[];spawned=1000000;
 player.position.x=targetX=1.61;
 spawnGateRow(player.position.z-.5,0,{sequence:['smile'],gates:[['smile','neutral','sad']]},0)};
"""
html = (ROOT / "index.html").read_text().replace("\ninit();", "\n" + hooks + "\ninit();")

with sync_playwright() as p:
    chromium = os.environ.get("MOOD_CHROMIUM") or shutil.which("chromium")
    browser = p.chromium.launch(
        **({"executable_path": chromium} if chromium else {}),
        headless=True,
        args=["--no-sandbox", "--enable-unsafe-swiftshader"],
    )
    contexts = [browser.new_context(viewport={"width": 390, "height": 844}, ignore_https_errors=True) for _ in range(2)]
    pages = []
    errors = []
    for context in contexts:
        context.add_init_script("localStorage.setItem('mood_terms_version','2026-10-24');localStorage.setItem('kado_name','Runner')")
        page = context.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route(url, lambda route: route.fulfill(body=html, content_type="text/html"))
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector("#s-menu.on")
        pages.append(page)
    host, guest = pages
    queues = [[], []]
    for i, page in enumerate(pages):
        page.expose_function("__sendPeer", lambda d, i=i: queues[i].append(d))
        page.evaluate("__attach", i == 0)

    def pump(delay=0):
        # Controls remain ordered; consecutive realtime snapshots/inputs coalesce.
        for _ in range(3):
            for sender, recipient in [(0, guest), (1, host)]:
                queued, queues[sender] = queues[sender], []
                latest = {}
                messages = []
                for message in queued:
                    if message["type"] in ("team", "input"):
                        latest[message["type"]] = message
                    else:
                        messages.append(message)
                messages.extend(latest.values())
                if messages:
                    recipient.evaluate("messages=>messages.forEach(d=>__receivePeer(d))", messages)
        if delay:
            host.wait_for_timeout(delay)

    def inspect(page=host):
        return page.evaluate("__inspect()")

    def start_pair():
        host.evaluate("startMultiplayer()")
        pump()
        assert inspect()["state"] == inspect(guest)["state"] == "READY"
        assert inspect()["lives"] == inspect(guest)["lives"] == 1
        assert inspect()["width"] >= 5.5 * 3.2
        assert inspect()["rows"] == inspect(guest)["rows"]
        for page in pages:
            page.evaluate("__freeTrack()")
        host.evaluate("beginRun()")
        pump()
        assert inspect()["state"] == "READY"
        guest.evaluate("beginRun()")
        pump()
        assert inspect()["state"] == inspect(guest)["state"] == "PLAYING"

    start_pair()
    print("PASS: wider matching track, one life each, both players tap to start", flush=True)
    # Real drag events feed the production input listeners on both pages.
    for page, end in [(host, 20), (guest, 370)]:
        page.mouse.move(195, 720)
        page.mouse.down()
        page.mouse.move(end, 720, steps=4)
        page.mouse.up()
    for _ in range(12):
        pump(60)
        for page in pages:
            s = inspect(page)
            assert s["state"] == "PLAYING", s
            assert abs(s["p"]["z"] - s["o"]["z"]) < 1e-6, s
            assert abs(s["p"]["x"] - s["o"]["x"]) <= 6.401, s
            assert max(abs(s["p"]["x"]), abs(s["o"]["x"])) <= s["bound"] + .001, s
    s = inspect()
    assert s["team"]["gx"] - s["team"]["hx"] > 5.8, s
    assert s["rope"]
    host.screenshot(path="/tmp/mood-rope-stretched.png")
    print("PASS: opposite drags stretch the rope to two tiles; no forward/back drift", flush=True)

    for page in pages:
        page.evaluate("__targets(8.4)")
    for _ in range(10):
        pump(70)
    assert inspect()["team"]["hx"] > 5 and inspect()["team"]["gx"] <= 8.401
    host.screenshot(path="/tmp/mood-rope-edge.png")
    print("PASS: tethered pair can move together across the wider platform", flush=True)

    host.evaluate("__cross(-.7,.7,'neutral')")
    host.wait_for_function("__inspect().score===1")
    pump()
    assert inspect(guest)["score"] == 1 and inspect(guest)["runCoins"] >= 5
    host.evaluate("__cross(2.6,3.8,'neutral')")
    host.wait_for_selector("#s-over.on")
    pump()
    for page in pages:
        page.wait_for_selector("#s-over.on")
        assert page.locator("#over-title").inner_text() == "LOSER"
        assert page.locator("#fail-blame").inner_text() == "Ben MADE MISTAKE"
        assert page.locator("#over-icon svg").get_attribute("aria-label") == "Cheeky smiling face"
        assert inspect(page)["state"] == "GAMEOVER"
        before = inspect(page)
        page.evaluate("reviveRun();finishRun()")
        assert inspect(page)["state"] == "GAMEOVER"
        assert inspect(page)["coins"] == before["coins"]
    guest.set_viewport_size({"width": 320, "height": 568})
    guest.screenshot(path="/tmp/mood-rope-loser.png")
    guest.set_viewport_size({"width": 390, "height": 844})
    print("PASS: same-gate success; guest mistake ends both with identical LOSER name/smile; no revive or double bank", flush=True)

    s = inspect()
    stale = {"type":"team","rd":s["round"],"tick":999999,"z":s["team"]["z"],"hx":s["team"]["hx"],"gx":s["team"]["gx"],"lastGate":s["passed"],"score":s["score"],"streak":0,"bestStreak":0,"seq":0,"st":"GAMEOVER","blame":"Ben","reason":"mistake"}
    before = inspect(guest)["coins"]
    guest.evaluate("d=>__receivePeer(d)", stale)
    assert inspect(guest)["coins"] == before
    start_pair()
    guest.evaluate("d=>__receivePeer(d)", stale)
    assert inspect(guest)["state"] == "PLAYING"
    guest.evaluate("pauseRun()")
    pump()
    assert inspect()["state"] == inspect(guest)["state"] == "PAUSED"
    z = inspect()["p"]["z"]
    host.wait_for_timeout(250)
    assert inspect()["p"]["z"] == z
    host.evaluate("resumeRun()")
    pump()
    assert inspect()["state"] == inspect(guest)["state"] == "PLAYING"
    host.evaluate("__cross(-6.9,-5.6,'sad')")
    host.wait_for_selector("#s-over.on")
    pump()
    assert guest.locator("#fail-blame").inner_text() == "Ada MADE MISTAKE"
    print("PASS: synchronized pause/restart, stale packets ignored, host mistake has one authoritative name", flush=True)

    start_pair()
    host.evaluate("__breakPeer()")
    assert host.locator("#over-title").inner_text() == "CONNECTION LOST"
    host.evaluate("leaveMenu();startSolo('endless')")
    s = inspect()
    assert s["lives"] == 3 and s["width"] < 5.5 * 3.2 and not s["rope"]
    host.evaluate("beginRun()")
    for remaining in [2, 1, 0]:
        host.evaluate("__soloGate()")
        host.wait_for_function(f"__inspect().lives==={remaining}")
    assert inspect()["state"] == "REVIVE"
    host.evaluate("window.MoodRunAds={showRewarded:async()=>({rewarded:true})};reviveRun()")
    host.wait_for_selector("#s-ready.on")
    assert inspect()["lives"] == 1
    assert not errors, errors
    print("PASS: disconnect ends rope run; solo retains three lives and rewarded revival; no browser errors", flush=True)
    browser.close()
server.shutdown()
