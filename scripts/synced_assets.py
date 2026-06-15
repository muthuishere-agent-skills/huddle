"""
Shared, stdlib-only reader for externally-synced persona assets.

Producer-agnostic: ANY tool, CLI, or agent (huddle-store, Codex, a cron job,
a hand-authored file) may drop persona directories into the config tree. This
module only READS them — it never writes, and never raises on bad input
(one malformed file is skipped, not fatal).

On-disk contract (read-only):

    <personas_dir>/
        <persona-name>/
            <persona-name>.md        # optional definition (the lone *.md in the dir)
            memories/
                <slug>.md            # optional, one memory per file

`<persona-name>` is the persona id/key. A dir keyed to a built-in id (e.g.
`shaama/`, `suren/`) that contains ONLY a `memories/` folder augments that
built-in with accrued memories — no definition needed. Absent dirs yield [].

Frontmatter is the same YAML subset the bundled persona files already use:
`key: value`, quoted scalars (`icon: "x"`), inline lists (`domains: [a, b]`),
and `- item` block lists. No `yaml` import.

Usage (debugging):
    python3 synced_assets.py scan <personas_dir> [source]
"""

from __future__ import annotations

import json
import pathlib
import sys


# ---------------------------------------------------------------------------
# Frontmatter parsing (stdlib-only YAML subset)
# ---------------------------------------------------------------------------

def _scalar(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _parse_value(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p) for p in inner.split(",") if p.strip()]
    return _scalar(v)


def _parse_yaml_subset(lines):
    meta = {}
    key = None
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and key is not None:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(_scalar(stripped[2:]))
            continue
        if ":" not in raw:
            continue
        k, _, v = raw.partition(":")
        k = k.strip()
        v = v.strip()
        key = k
        meta[k] = _parse_value(v) if v else ""
    return meta


def parse_frontmatter(text):
    """Return (meta_dict, body_str). Tolerates a missing frontmatter block."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    meta = _parse_yaml_subset(lines[1:end])
    body = "\n".join(lines[end + 1:])
    return meta, body


def _as_list(v):
    if isinstance(v, list):
        return v
    if v in (None, ""):
        return []
    return [v]


# ---------------------------------------------------------------------------
# Asset parsing
# ---------------------------------------------------------------------------

def parse_persona_file(path):
    """Parse a synced persona definition .md. Returns a partial entry dict
    (the caller fills id/source/file/memories), or None if unreadable."""
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8")
    except Exception:
        return None
    meta, _ = parse_frontmatter(text)
    return {
        "name": meta.get("displayName") or meta.get("name") or "",
        "title": meta.get("title", ""),
        "icon": meta.get("icon", ""),
        "domains": _as_list(meta.get("domains")),
        "role": meta.get("role", ""),
        "primaryLens": meta.get("primaryLens", ""),
        "communicationStyle": meta.get("communicationStyle", ""),
        "principles": meta.get("principles", ""),
    }


def parse_memory_file(path, persona_id):
    """Parse a memory note's frontmatter into a lightweight index entry.
    Bodies are loaded on demand (by the step docs), never inlined here.
    Returns None if unreadable."""
    p = pathlib.Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return None
    meta, _ = parse_frontmatter(text)
    return {
        "title": meta.get("title") or p.stem,
        "tags": _as_list(meta.get("tags")),
        "corpus": meta.get("corpus", ""),
        "source": meta.get("source", ""),
        "persona": persona_id,
        "file": str(p.resolve()),
    }


def _scan_memories(persona_dir, persona_id):
    mem_dir = persona_dir / "memories"
    if not mem_dir.is_dir():
        return []
    out = []
    for md in sorted(mem_dir.glob("*.md")):
        if not md.is_file():
            continue
        entry = parse_memory_file(md, persona_id)
        if entry is not None:
            out.append(entry)
    return out


def _build_persona_entry(persona_dir, source):
    """Build one roster entry for a persona directory, or None if the dir
    has neither a definition nor any memories."""
    key = persona_dir.name

    # Definition = the lone *.md directly in the dir (name-agnostic).
    # Prefer `<key>.md` if present, else the first .md by sorted name.
    candidates = sorted(p for p in persona_dir.glob("*.md") if p.is_file())
    definition = None
    preferred = persona_dir / f"{key}.md"
    if preferred in candidates:
        definition = preferred
    elif candidates:
        definition = candidates[0]

    memories = _scan_memories(persona_dir, key)

    if definition is None and not memories:
        return None

    entry = {
        "id": key,
        "name": key,
        "title": "",
        "icon": "",
        "domains": [],
        "role": "",
        "primaryLens": "",
        "communicationStyle": "",
        "principles": "",
        "file": None,
        "source": source,
        "memories": memories,
    }

    if definition is not None:
        parsed = parse_persona_file(definition)
        if parsed is not None:
            entry.update(parsed)
            entry["file"] = str(definition.resolve())
        if not entry["name"]:
            entry["name"] = key

    return entry


def scan_personas(personas_dir, source):
    """Scan a `personas/` directory of per-persona subfolders. Returns a list
    of roster entries (each carrying its own `memories` index). Absent dir or
    any read error yields []. One malformed file is skipped, never fatal."""
    try:
        base = pathlib.Path(personas_dir)
        if not base.is_dir():
            return []
        out = []
        for d in sorted(base.iterdir()):
            if not d.is_dir():
                continue
            try:
                entry = _build_persona_entry(d, source)
            except Exception:
                entry = None
            if entry is not None:
                out.append(entry)
        return out
    except Exception:
        return []


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2 or args[0] != "scan":
        print(__doc__)
        sys.exit(1)
    src = args[2] if len(args) > 2 else "synced"
    print(json.dumps(scan_personas(args[1], src), indent=2))
