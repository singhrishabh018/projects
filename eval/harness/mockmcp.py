#!/usr/bin/env python3
"""Stdlib-only stdio MCP server that serves a case's connectors/*.json fixtures.

Each fixture file is one source role, e.g. connectors/tickets.json:
  {"role": "tickets", "failure": null | "timeout" | "error",
   "items": [{"id": "142", "title": "...", "body": "...", "author": "...",
              "updated": "2026-09-01", "url": "tracker://142", ...}]}
For every role it exposes two tools: <role>_search(query) and <role>_get(id).
A role with failure "timeout" answers every call with a timeout error.
Every call is appended as one JSON line to $MOCKMCP_LOG (if set).

Usage: mockmcp.py <connectors-dir>
"""
import json
import os
import sys
import time

PROTOCOL = "2025-06-18"


def load(dirpath):
    roles = {}
    if dirpath and os.path.isdir(dirpath):
        for name in sorted(os.listdir(dirpath)):
            if name.endswith(".json"):
                with open(os.path.join(dirpath, name)) as f:
                    data = json.load(f)
                roles[data.get("role") or name[:-5]] = data
    return roles


def tools_for(roles):
    tools = []
    for role, data in roles.items():
        desc = data.get("description", f"{role} source")
        tools.append({
            "name": f"{role}_search",
            "description": f"Search the {desc}. Returns matching items (id, title, updated).",
            "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}},
                            "required": ["query"]},
        })
        tools.append({
            "name": f"{role}_get",
            "description": f"Get one item from the {desc} by id, with full body and metadata.",
            "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}},
                            "required": ["id"]},
        })
    return tools


def call(roles, name, args):
    role, _, op = name.rpartition("_")
    data = roles.get(role)
    if data is None or op not in ("search", "get"):
        return True, f"Unknown tool {name}"
    failure = data.get("failure")
    if failure == "timeout":
        time.sleep(float(data.get("delay_seconds", 2)))
        return True, f"Request to {role} source timed out after 30000 ms (upstream unavailable). Retry later."
    if failure == "error":
        return True, f"{role} source returned HTTP 503 Service Unavailable."
    items = data.get("items", [])
    if op == "get":
        want = str(args.get("id", "")).lstrip("#")
        for it in items:
            if str(it.get("id")) == want:
                return False, json.dumps(it, indent=2)
        return True, f"No {role} item with id {want!r}."
    q = str(args.get("query", "")).lower()
    words = [w for w in q.split() if w]
    hits = [it for it in items
            if not words or any(w in json.dumps(it).lower() for w in words)]
    summary = [{k: it.get(k) for k in ("id", "title", "updated")} for it in hits]
    return False, json.dumps(summary, indent=2)


def main():
    roles = load(sys.argv[1] if len(sys.argv) > 1 else None)
    log = os.environ.get("MOCKMCP_LOG")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        if mid is None:  # notification
            continue
        if method == "initialize":
            result = {"protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL),
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "sources", "version": "0.1"}}
        elif method == "tools/list":
            result = {"tools": tools_for(roles)}
        elif method == "tools/call":
            p = msg.get("params", {})
            is_err, text = call(roles, p.get("name", ""), p.get("arguments") or {})
            if log:
                with open(log, "a") as f:
                    f.write(json.dumps({"t": time.time(), "tool": p.get("name"),
                                        "args": p.get("arguments"), "error": is_err}) + "\n")
            result = {"content": [{"type": "text", "text": text}], "isError": is_err}
        elif method == "ping":
            result = {}
        else:
            out = {"jsonrpc": "2.0", "id": mid,
                   "error": {"code": -32601, "message": f"method not found: {method}"}}
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()
            continue
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": result}) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
