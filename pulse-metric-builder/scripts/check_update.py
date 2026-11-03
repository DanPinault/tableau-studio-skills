#!/usr/bin/env python3
"""Update checker for a Tableau Studio skill. Python 3, standard library only.

Lives in <skill folder>/scripts/ and is identical in every skill. The skill name
is the name of the folder two levels up from this file, so nothing is configured
per skill.

Commands (each prints one JSON object and exits 0 unless noted):
  check   Compare the local VERSION with the one on GitHub.
          status: up_to_date | update_available | unknown | snoozed
  apply   Replace this skill's folder with the latest copy. The old folder is
          moved to ~/.tableau-studio-skills-backups/ first.
  snooze  Remember the latest version so check stays quiet until a newer one.
  sums    Maintainers: write SHA256SUMS for this skill folder (run before release).

Where updates come from: the latest GitHub release tag if the repository has one
(so a release is a deliberate, reviewable pin), otherwise the main branch. Set
SKILL_UPDATE_REF to force a tag, branch or commit. `apply` refuses a copy that is
not newer, is for a different skill, has links, is too large, or fails SHA256SUMS.

`check` never fails the caller: any network or parse problem returns "unknown".
"""
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

REPO = "DanPinault/tableau-studio-skills"
BRANCH = "main"
MAX_FILES = 300
MAX_BYTES = 25 * 1024 * 1024
SUMS = "SHA256SUMS"
TIMEOUT = 4  # seconds; a slow network must never stall the skill
SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL = SKILL_DIR.name
STATE = Path.home() / ".tableau-studio-skills-state.json"
BACKUPS = Path.home() / ".tableau-studio-skills-backups"
# Testing hook: point at a local checkout of the repo instead of GitHub.
LOCAL_REPO = os.environ.get("SKILL_UPDATE_LOCAL_REPO")


def out(obj, code=0):
    print(json.dumps(obj, indent=2))
    sys.exit(code)


def vkey(v):
    return tuple(int(p) for p in re.findall(r"\d+", v)[:3])


_REF = []


def resolve_ref():
    """The tag, branch or commit to read: forced, else the latest release, else main."""
    if not _REF:
        _REF.append(_find_ref())
    return _REF[0]


def _find_ref():
    forced = os.environ.get("SKILL_UPDATE_REF")
    if forced:
        return forced
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            tag = json.load(r).get("tag_name")
        if tag and re.fullmatch(r"[A-Za-z0-9._/-]+", tag):
            return tag
    except Exception:
        pass
    return BRANCH


def fetch_text(path):
    """Read <skill>/<path> from the repo (GitHub raw, or the local test checkout)."""
    if LOCAL_REPO:
        return (Path(LOCAL_REPO) / SKILL / path).read_text()
    url = f"https://raw.githubusercontent.com/{REPO}/{resolve_ref()}/{SKILL}/{path}"
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8")


def local_version():
    return (SKILL_DIR / "VERSION").read_text().strip()


def read_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def changes_since(changelog, local):
    """Changelog sections for versions newer than `local`, each capped for chat."""
    sections = re.split(r"(?m)^(?=## )", changelog)
    keep = []
    for s in sections:
        m = re.match(r"## +v?(\d+\.\d+\.\d+)", s)
        if m and vkey(m.group(1)) > vkey(local):
            lines = s.strip().splitlines()
            keep.append("\n".join(lines[:14]))
    return "\n\n".join(keep)


def cmd_check():
    local = local_version()
    try:
        remote = fetch_text("VERSION").strip()
        vkey(remote)
    except Exception:
        out({"status": "unknown", "skill": SKILL, "local": local})
    if vkey(remote) <= vkey(local):
        out({"status": "up_to_date", "skill": SKILL, "local": local, "remote": remote})
    if read_state().get(SKILL) == remote:
        out({"status": "snoozed", "skill": SKILL, "local": local, "remote": remote})
    try:
        changes = changes_since(fetch_text("CHANGELOG.md"), local)
    except Exception:
        changes = ""
    out({"status": "update_available", "skill": SKILL, "local": local,
         "remote": remote, "changes": changes})


def cmd_snooze():
    try:
        remote = fetch_text("VERSION").strip()
    except Exception:
        out({"ok": False, "error": "could not reach the repository"})
    state = read_state()
    state[SKILL] = remote
    STATE.write_text(json.dumps(state, indent=2))
    out({"ok": True, "snoozed_version": remote})


def get_new_copy(tmp):
    """Put the latest copy of this skill at tmp/<SKILL>; return that path."""
    dest = tmp / SKILL
    if LOCAL_REPO:
        shutil.copytree(Path(LOCAL_REPO) / SKILL, dest,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"))
        return dest
    url = f"https://codeload.github.com/{REPO}/tar.gz/{resolve_ref()}"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = r.read(MAX_BYTES * 4 + 1)
    if len(data) > MAX_BYTES * 4:
        raise RuntimeError("archive is too large")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        prefix = None
        members = [m for m in tf.getmembers() if len(Path(m.name).parts) >= 2
                   and Path(m.name).parts[1] == SKILL]
        if len(members) > MAX_FILES or sum(m.size for m in members) > MAX_BYTES:
            raise RuntimeError("skill folder is larger than expected")
        for m in tf.getmembers():
            parts = Path(m.name).parts
            if len(parts) >= 2 and parts[1] == SKILL:
                prefix = parts[0]
                # refuse anything that could escape the temp folder
                if m.islnk() or m.issym() or ".." in parts or Path(m.name).is_absolute():
                    raise RuntimeError(f"unsafe path in archive: {m.name}")
                if hasattr(tarfile, "data_filter"):  # Python 3.12+ (and patched 3.9-3.11)
                    tf.extract(m, tmp, filter="data")
                else:
                    tf.extract(m, tmp)
        if prefix is None:
            raise RuntimeError(f"{SKILL} not found in the repository")
    return tmp / prefix / SKILL


def file_sums(root):
    """sha256 of every file under root except SHA256SUMS, keyed by relative path."""
    sums = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in (SUMS, ".DS_Store") and "__pycache__" not in p.parts:
            sums[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return sums


def verify_copy(new, old_version):
    """Raise unless the downloaded copy is this skill, is newer, and matches SHA256SUMS."""
    head = (new / "SKILL.md").read_text()
    if not re.search(rf"(?m)^name:\s*{re.escape(SKILL)}\s*$", head):
        raise RuntimeError("downloaded copy is not this skill")
    new_version = (new / "VERSION").read_text().strip()
    if vkey(new_version) <= vkey(old_version):
        raise RuntimeError(f"downloaded copy ({new_version}) is not newer than {old_version}")
    listed = new / SUMS
    if listed.exists():
        want = {}
        for line in listed.read_text().splitlines():
            if line.strip():
                digest, name = line.strip().split(None, 1)
                want[name.strip()] = digest
        have = file_sums(new)
        bad = [k for k in have if want.get(k) != have[k]]
        if bad:
            raise RuntimeError(f"checksum mismatch: {bad[:3]}")


def cmd_sums():
    sums = file_sums(SKILL_DIR)
    (SKILL_DIR / SUMS).write_text("".join(f"{h}  {k}\n" for k, h in sums.items()))
    out({"ok": True, "files": len(sums)})


def cmd_apply():
    old = local_version()
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        try:
            new = get_new_copy(tmp)
            verify_copy(new, old)
            new_version = (new / "VERSION").read_text().strip()
        except Exception as e:
            out({"ok": False, "error": f"download failed: {e}"}, 1)
        BACKUPS.mkdir(exist_ok=True)
        backup = BACKUPS / f"{SKILL}-{old}-{time.strftime('%Y%m%d-%H%M%S')}"
        staged = SKILL_DIR.parent / f".{SKILL}.incoming"
        if staged.exists():
            shutil.rmtree(staged)
        shutil.copytree(new, staged)
        # swap: old folder to backup, new folder into place
        shutil.move(str(SKILL_DIR), str(backup))
        try:
            shutil.move(str(staged), str(SKILL_DIR))
        except Exception as e:
            shutil.move(str(backup), str(SKILL_DIR))  # put the old copy back
            out({"ok": False, "error": f"install failed, old copy restored: {e}"}, 1)
    out({"ok": True, "skill": SKILL, "from": old, "to": new_version,
         "backup": str(backup)})


if __name__ == "__main__":
    cmds = {"check": cmd_check, "apply": cmd_apply, "snooze": cmd_snooze, "sums": cmd_sums}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        out({"error": "usage: check_update.py check|apply|snooze|sums"}, 2)
    cmds[sys.argv[1]]()
