"""Build a fresh, git-initialised workspace for one run, and collect what changed after it."""
import os
import shutil
import subprocess

GIT_ENV = {"GIT_AUTHOR_NAME": "dev", "GIT_AUTHOR_EMAIL": "dev@example.test",
           "GIT_COMMITTER_NAME": "dev", "GIT_COMMITTER_EMAIL": "dev@example.test"}


def _git(repo, *args, check=True):
    env = dict(os.environ, **GIT_ENV)
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          env=env, check=check)


def build(case, ws_dir):
    """Copy base + overlay into ws_dir, apply removals, git-init each top-level folder."""
    os.makedirs(ws_dir, exist_ok=True)
    base = case.base_dir()
    if base:
        shutil.copytree(base, ws_dir, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".git"))
    overlay = case.overlay_dir()
    if overlay:
        shutil.copytree(overlay, ws_dir, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
    for rel in case.removals():
        path = os.path.join(ws_dir, rel)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)
    repos = []
    for name in sorted(os.listdir(ws_dir)):
        repo = os.path.join(ws_dir, name)
        if not os.path.isdir(repo):
            continue
        if not os.path.isdir(os.path.join(repo, ".git")):
            _git(repo, "init", "-q", "-b", "main")
            with open(os.path.join(repo, ".gitignore"), "a") as f:
                f.write("__pycache__/\n*.pyc\n")
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "initial")
        repos.append(name)
    return repos


def collect(ws_dir, repos):
    """Per-repo diff against the initial commit (untracked files included), plus new files."""
    out = {}
    for name in repos:
        repo = os.path.join(ws_dir, name)
        if not os.path.isdir(repo):
            out[name] = {"missing": True}
            continue
        _git(repo, "add", "-A", "-N", check=False)  # intent-to-add so untracked files diff
        # paths in the diff are workspace-relative (<repo>/<file>) so checks can glob them
        diff = _git(repo, "diff", "--no-color", "--no-ext-diff", f"--src-prefix=a/{name}/",
                    f"--dst-prefix=b/{name}/", check=False).stdout
        stat = _git(repo, "diff", "--numstat", check=False).stdout
        status = _git(repo, "status", "--porcelain", "--untracked-files=all", check=False).stdout
        log = _git(repo, "log", "--oneline", check=False).stdout.strip().splitlines()
        new_files = [f"{name}/{line[3:]}" for line in status.splitlines()
                     if line.startswith("?? ") or line.startswith(" A ") or line.startswith("A  ")]
        added = removed = 0
        files = []
        for line in stat.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                a, r, f = parts
                added += int(a) if a.isdigit() else 0
                removed += int(r) if r.isdigit() else 0
                files.append(f"{name}/{f}")
        out[name] = {"diff": diff, "files_changed": files, "new_files": new_files,
                     "lines_added": added, "lines_removed": removed,
                     "commits_after_initial": max(len(log) - 1, 0)}
    return out


def added_lines(diff_text, path_glob=None):
    """Yield (file, line) for '+' lines in a unified diff, optionally filtered by glob."""
    import fnmatch
    current = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and not line.startswith("+++") and current:
            if path_glob is None or fnmatch.fnmatch(current, path_glob):
                yield current, line[1:]


def removed_lines(diff_text, path_glob=None):
    import fnmatch
    current = None
    for line in diff_text.splitlines():
        if line.startswith("--- "):
            current = line[6:] if line.startswith("--- a/") else None
        elif line.startswith("+++ "):
            pass
        elif line.startswith("-") and not line.startswith("---") and current:
            if path_glob is None or fnmatch.fnmatch(current, path_glob):
                yield current, line[1:]


def list_files(root):
    out = []
    if root and os.path.isdir(root):
        for dp, _, fns in os.walk(root):
            for fn in fns:
                out.append(os.path.relpath(os.path.join(dp, fn), root))
    return sorted(out)
