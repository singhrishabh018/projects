"""Run headless Claude Code (`claude -p`) with a clean profile and capture stream-json."""
import json
import os
import subprocess
import threading
import time

# Parent-session variables that leak into children (session id reuse, debug output,
# extra working directories that would let the run see this repo).
STRIP_ENV = ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_REMOTE_SESSION_ID", "CLAUDE_CODE_DEBUG",
             "CLAUDE_ADDITIONAL_DIRECTORIES", "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD",
             "CLAUDE_EFFORT", "GROUNDWORK_HOME", "GROUNDWORK_WORKSPACE", "MOCKMCP_LOG")

# The only built-in tools an eval agent gets. Host extras (publishing, notifications,
# scheduling) are removed so a run can't act outside its workspace.
AGENT_TOOLS = ["Bash", "Read", "Edit", "Write", "Glob", "Grep", "Skill", "Agent"]


def child_env(config_dir, extra=None):
    env = {k: v for k, v in os.environ.items() if k not in STRIP_ENV}
    env["CLAUDE_CONFIG_DIR"] = config_dir
    env.update(extra or {})
    return env


def agent_cmd(claude_bin, prompt, model, *, effort=None, max_turns=80, max_budget=6.0,
              resume=None, add_dir=None, mcp_config=None, disallowed=()):
    tools = [t for t in AGENT_TOOLS if t not in disallowed]
    allowed = list(tools) + (["mcp__sources"] if mcp_config else [])
    cmd = [claude_bin, "-p", prompt, "--model", model, "--output-format", "stream-json",
           "--verbose", "--max-turns", str(max_turns), "--max-budget-usd", f"{max_budget:.2f}",
           "--permission-mode", "acceptEdits", "--tools", ",".join(tools),
           "--allowedTools", ",".join(allowed)]
    if disallowed:
        cmd += ["--disallowedTools", ",".join(disallowed)]
    if effort:
        cmd += ["--effort", effort]
    if resume:
        cmd += ["--resume", resume]
    if add_dir:
        cmd += ["--add-dir", add_dir]
    if mcp_config:
        cmd += ["--mcp-config", mcp_config, "--strict-mcp-config"]
    return cmd


def run_stream(cmd, cwd, env, transcript_path, timeout_s):
    """Run cmd, write each stdout line as {"t": recv_time, "e": event} to transcript_path.

    Returns (events, result_event_or_None, returncode, stderr_text, timed_out).
    """
    events, result = [], None
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    timed_out = {"v": False}

    def _kill():
        timed_out["v"] = True
        proc.kill()

    timer = threading.Timer(timeout_s, _kill)
    timer.start()
    stderr_chunks = []
    t_err = threading.Thread(target=lambda: stderr_chunks.append(proc.stderr.read()))
    t_err.start()
    with open(transcript_path, "a") as out:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                ev = {"type": "raw", "text": line}
            if ev.get("type") == "stream_event":  # token deltas: large and not needed
                continue
            rec = {"t": time.time(), "e": ev}
            out.write(json.dumps(rec) + "\n")
            events.append(rec)
            if ev.get("type") == "result":
                result = ev
    proc.wait()
    timer.cancel()
    t_err.join(timeout=5)
    return events, result, proc.returncode, "".join(c for c in stderr_chunks if c), timed_out["v"]


def oneshot_json(claude_bin, prompt, model, config_dir, cwd, schema, timeout_s=600, effort=None):
    """No-tools `claude -p` with a JSON schema; prompt goes on stdin. Returns (obj, result)."""
    cmd = [claude_bin, "-p", "--model", model, "--output-format", "json", "--tools", "",
           "--max-turns", "3", "--json-schema", json.dumps(schema)]
    if effort:
        cmd += ["--effort", effort]
    env = child_env(config_dir)
    proc = subprocess.run(cmd, input=prompt, cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=timeout_s)
    try:
        res = json.loads(proc.stdout)
    except ValueError:
        return None, {"error": "unparseable output", "stdout": proc.stdout[-2000:],
                      "stderr": proc.stderr[-2000:]}
    obj = res.get("structured_output")
    if obj is None and isinstance(res.get("result"), str):
        try:
            obj = json.loads(res["result"])
        except ValueError:
            obj = None
    return obj, res
