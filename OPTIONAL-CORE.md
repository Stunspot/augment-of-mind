# Optional MIND Core

MIND Core `0.2.0` is a persona-neutral local Python runtime for capability
metadata, lifecycle evidence, associative capability cards, and explicit H0
queries. It is included in the release archive as a wheel. The Codex plugin
does not install, start, or depend on it.

## What Core can do

- initialize one local SQLite metadata database;
- record explicit capability, distribution, host-session, mount, and evidence
  metadata supplied through its administrative interfaces;
- ingest a complete immutable associative-index manifest;
- issue scoped session capabilities;
- compile exact radius, exhaustive lexical, and one-hop associative reminder
  fields;
- return canonical and compact representations with identical membership;
- serve a framed, query-only stdio protocol.

Core does not crawl your computer, infer a capability estate from filenames,
retain raw task text, generate embeddings, select a tool, activate a Faculty,
or intercept Codex turns.

## Install from the release archive

Prerequisite: Python 3.11 or newer.

From the extracted release root on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --find-links .\optional-core cd-mind-core==0.2.0
```

On macOS or Linux, use `.venv/bin/python` instead of
`.venv\Scripts\python.exe` throughout this guide.

Release qualification for `0.2.0` is executed on Windows. The POSIX commands
use Python's standard virtual-environment layout, but this release does not
claim an independently observed macOS or Linux host run.

Expected result: pip reports `cd-mind-core-0.2.0` installed without contacting
a package index.

## Initialize and inspect a database

Choose a path you own. Core creates the database if it is absent. On Windows:

```powershell
.\.venv\Scripts\python.exe -m mind_core init --database .\mind-data\mind-core.sqlite3
```

On macOS or Linux:

```sh
.venv/bin/python -m mind_core init --database ./mind-data/mind-core.sqlite3
```

Expected result: one JSON object containing, among other fields,
`"runtime_version":"0.2.0"`, `"schema_version":2`,
`"persona_required":false`, and
`"mode":"phase2_associative_disclosure_h0"`.

Read the same state later. On Windows:

```powershell
.\.venv\Scripts\python.exe -m mind_core status --database .\mind-data\mind-core.sqlite3
```

On macOS or Linux:

```sh
.venv/bin/python -m mind_core status --database ./mind-data/mind-core.sqlite3
```

Completion proof: `status` exits successfully and reports the same Core
instance without changing its record counts.

## Administrative and query commands

Run `python -m mind_core --help` from the active environment, or append
`--help` to a subcommand, for its exact arguments. The installed `mind-core`
console script is equivalent when it is on your shell's path.

| Command | Purpose |
|---|---|
| `init` | Initialize migrations and report Core state. |
| `status` | Report versions, mode, instance identity, and table counts. |
| `bootstrap` | Ingest explicit Phase 1 metadata from a JSON manifest. |
| `index` | Ingest one complete associative-index generation. |
| `issue-session-capability` | Issue one scoped opaque query capability. |
| `revoke-session-capability` | Revoke an issued query capability. |
| `query` | Execute one JSON request file through the H0 service. |
| `serve` | Run the length-prefixed query-only stdio service. |

The manifest and request schemas are strict. This release intentionally does
not ship a real inventory of your capabilities or an embedding model.

## Safe stopping and removal

Stop any `serve` process before copying or removing its database. Uninstall the
wheel from the environment with:

```powershell
.\.venv\Scripts\python.exe -m pip uninstall cd-mind-core
```

Uninstalling the wheel does not delete databases. Remove those separately only
after you have resolved the exact paths and retained any copy you need.

For symptoms and recovery, see [Troubleshooting](TROUBLESHOOTING.md#mind-core).
