#!/usr/bin/env python3
"""
Append-only huddle event writer. Fire-and-forget.

Usage:
    python huddle_writer.py <huddle_dir> '<event_json>'

Writes a single timestamped JSON file to <huddle_dir>/raw/ and exits.
No reads, no merges, no locks. Each invocation is independent.

Event JSON example:
    {"type":"decision","topic":"...","content":"...","personas":["Shaama"],"by":"User","rejected":[],"open":[]}
"""
import json, sys, time
from pathlib import Path

huddle_dir, event_json = sys.argv[1], sys.argv[2]
raw_dir = Path(huddle_dir) / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)
event = json.loads(event_json)
ts = int(time.time() * 1000)
etype = event.get("type", "event")
Path(raw_dir / f"{ts}_{etype}.json").write_text(json.dumps(event, indent=2))
