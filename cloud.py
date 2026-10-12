import sys
import json
import asyncio

import urllib.request
import urllib.parse

SUPABASE_URL = "https://pylaigisttoxsekqzrvk.supabase.co"
SUPABASE_KEY = "sb_publishable_8qijECqC6rfKeT7rlnqhsw_9CJ4JmFB"

TABLE = SUPABASE_URL + "/rest/v1/kv"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

cache = {}
_counter = 0
_tasks = set()

def isWeb():
    return sys.platform == "emscripten"

def _desktopRequest(method, url, body):
    try:
        data = body.encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data = data, method = method, headers = HEADERS)
        with urllib.request.urlopen(req, timeout = 10) as r:
            return r.read().decode("utf-8")
    except Exception:
        return None

async def _webRequest(method, url, body):
    global _counter
    
    import platform
    _counter += 1
    rid = json.dumps(f"r{_counter}")

    platform.window.eval(f"""
    window.__cloud = window.__cloud || {{}};
    fetch({json.dumps(url)}, {{
        method: {json.dumps(method)},
        headers: {json.dumps(HEADERS)},
        body: {json.dumps(body)}
    }}).then(r => r.text().then(t => {{
        window.__cloud[{rid}] = JSON.stringify({{ok: r.ok, text: t}});
    }})).catch(e => {{
        window.__cloud[{rid}] = JSON.stringify({{ok: false, text: ""}});
    }});
    """)

    for _ in range(500):
        await asyncio.sleep(0.02)
        res = platform.window.eval(f"window.__cloud[{rid}]")
        if res:
            parsed = json.loads(str(res))
            return parsed["text"] if parsed["ok"] else None
    return None

async def _request(method, url, body = None):
    if isWeb():
        return await _webRequest(method, url, body)
    return await asyncio.to_thread(_desktopRequest, method, url, body)

def _run(coro):
    task = asyncio.create_task(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)

async def pull(key, default):
    text = await _request("GET", f"{TABLE}?key=eq.{urllib.parse.quote(key)}&select=value")
    try:
        rows = json.loads(text)
        cache[key] = json.loads(rows[0]["value"]) if rows else default
    except Exception:
        cache.setdefault(key, default)

def get(key, default):
    return cache.get(key, default)

def put(key, value):
    cache[key] = value
    _run(_request("POST", TABLE, json.dumps({"key": key, "value": json.dumps(value)})))

def remove(key):
    cache.pop(key, None)
    _run(_request("DELETE", f"{TABLE}?key=eq.{urllib.parse.quote(key)}"))