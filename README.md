# Project Context Manager (PCM)

**Research title:** Project Context Manager: A Lightweight Semantic Framework for
Cross-Application Developer Workspace Restoration

A research prototype investigating whether automatically constructed semantic
representations of a developer's cross-application workspace (VS Code, Git,
Chrome, terminal, filesystem) can reduce the time and effort needed to resume
interrupted development work.

## Research question

> Can automatically constructed semantic representations of a developer's
> cross-application workspace reduce the time and manual effort required to
> resume interrupted development tasks?

## Architecture

```
Developer works
       ↓
Workspace Collector (filesystem, Git, Chrome, terminal)
       ↓
Project Detection (deterministic, explainable scoring)
       ↓
Project Snapshot
       ↓
SQLite storage
       ↓
Semantic indexing (local Sentence-Transformers embedding)
       ↓
User returns later → natural-language request
       ↓
Intent extraction → hybrid semantic/keyword/git/recency retrieval
       ↓
Restoration Preview → user confirmation → Workspace Restoration
```

See `docs/ARCHITECTURE.md` for how each module maps to the research question,
and `docs/RESEARCH.md` for hypotheses, metrics, and how to run experiments.

## Requirements

- Python 3.10+
- Node.js 18+ (for the frontend)
- Windows recommended for full restoration support (VS Code / terminal /
  Chrome launch commands); the backend, retrieval, and evaluation code run
  fine cross-platform.
- CPU only — no GPU required. `all-MiniLM-L6-v2` runs comfortably on a laptop.

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env     # adjust if needed
uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).
The SQLite database (`pcm.db`) is created automatically on first run.

The first request that needs embeddings will download `all-MiniLM-L6-v2`
(~80MB) from Hugging Face — this requires an internet connection once; after
that it's cached locally and everything runs offline.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Layout is three columns:

- **Left sidebar** — every saved project. Click one to resume it instantly.
- **Center** — the chat.
- **Right panel** — live system status (CPU, memory, disk, battery),
  refreshed every 15s, plus whatever project is currently active.

Talk to it directly:

- `save C:\Projects\MyApp` — captures files, Git branch, browser tabs, terminal
  context for that folder and remembers it.
- `resume MyApp` — finds the closest matching saved project and restores it
  immediately (opens VS Code, files, browser tabs, terminal) without a
  confirmation dialog; anything genuinely risky (like re-running a shell
  command) is skipped and mentioned in the reply rather than silently run.
- `save` with no path given — auto-detects your currently open VS Code
  folder by checking which workspace was actually touched most recently
  (compares file modified-times inside VS Code's `workspaceStorage`
  folders, not just "some workspace VS Code has ever seen"), so it picks
  up the project you're actually looking at rather than an old one.
- `what files are in MyApp` / `what branch is MyApp on` / `what projects do
  I have` — answered directly from what's saved.
- `find file report.docx` — searches Desktop, Documents, Downloads (and
  drive roots on Windows) for a matching name.
- `how much disk space do I have` / `system info` / `what's using the most
  memory` — basic OS assistant checks (disk, CPU, RAM, battery, top
  processes) using `psutil`.
- `open C:\Projects\MyApp` — opens any file or folder path directly.
- `what's on my desktop` / `what's in Documents` — lists a folder's contents.
- `give me the resume file I applied to Microsoft with` — semantic recall:
  every file and browser tab from every saved snapshot is embedded
  individually (not just the project as a whole), so vague, descriptive
  queries can find and open a specific file without you knowing its exact
  name or which project it belongs to.
- "Clear memory" in the header wipes everything PCM has stored, including
  this per-file semantic index.
- `what did I work on today` / `what did I work on this week` — a digest
  across every project touched in that window.
- `forget project MyApp` — deletes just that one project, not everything.
- Persistent history, separate from snapshots: every save/resume logs
  events (files created/modified/renamed/deleted, Git commits and branch
  changes, Chrome tabs opened, terminal commands run) to an `events` table
  that survives independently of any single snapshot. Ask things like
  "what did I commit when I implemented OAuth", "where's the PNG I added
  yesterday", or "what documentation was I looking at" — these search
  across **all** saved projects (with a boost, not a filter, for whichever
  project is currently active), not just the one you're currently in.
- Snapshots are also taken automatically in the background every
  `PCM_SNAPSHOT_INTERVAL` seconds (default 30 min) for whichever project
  you last saved or resumed, so you don't lose progress between explicit
  "save" commands.

### Optional: Chrome tab collection

Chrome tabs are read via the Chrome DevTools Protocol, which only listens on
localhost. Launch Chrome once with:

```
chrome.exe --remote-debugging-port=9222
```

**Important:** Chrome is a single-process app. If Chrome was already
running when you add this flag, the flag is silently ignored — a new
window just opens inside the existing process, which was never started
with debugging on. Close every Chrome window completely (check Task
Manager for a lingering `chrome.exe`) before relaunching with the flag.

If PCM still can't see any tabs, ask it directly — `check chrome` — and
it'll tell you exactly what's wrong (port unreachable vs. connected but
genuinely no tabs open) instead of failing silently.

When tabs are found, "save" doesn't grab all of them silently — it lists
every open tab and asks which ones belong to this project (numbers, "all",
or "none"), with a checklist in the UI to pick from. Only the tabs you pick
get saved and later reopened on resume.

### Optional: LLM-backed understanding

By default, chat messages are understood by keyword matching — reliable,
but literal ("save this project" works; "yo remember what I'm doing" might
not). If you have an Anthropic or xAI (Grok) API key, PCM can use it to
understand more casual phrasing, and will use it to hold an actual
conversation for anything that isn't a real command:

```
PCM_LLM_ENABLED=true
PCM_LLM_PROVIDER=anthropic     # or "grok"
ANTHROPIC_API_KEY=sk-ant-...
GROK_API_KEY=xai-...
```

This is tried first on every message and only ever falls back to the
deterministic keyword matcher — if the key's missing, the API call fails,
or it's just disabled, everything keeps working exactly as before. Nothing
about save/resume/restore behavior changes; this only affects how a message
gets routed to that existing behavior, and what happens when nothing
matches a real command.

### What "save" actually captures now

Beyond files, browser tabs, and basic Git metadata, save also captures the
things that are genuinely hard to reconstruct by hand:

- **Uncommitted Git changes** — the actual diff of modified files and the
  full content of untracked files, not just their names. On resume, PCM
  applies this back onto the working tree (flagged as requiring
  confirmation, since it writes to disk).
- **Terminal state** — active virtualenv/conda environment, and any
  non-shell processes currently running with a working directory under
  the project.
- **Chrome tab warnings** — each tab's domain is checked against a small
  static list of known low-credibility/satire sites first (instant, no
  network needed). If `GOOGLE_FACTCHECK_API_KEY` is set, PCM also queries
  Google's Fact Check Tools API with the tab's title, so a specific claim
  can get flagged even on a domain that isn't on any blocklist — e.g. a
  false claim shared on an otherwise-ordinary blog. Flagged tabs show a
  warning right in the picker before you decide what to save.

### Optional: access control

Say "set pin 1234" (any 4-8 digit code) to require that PIN before PCM
will show saved projects, files, git status, or history — saving is never
gated, so you can't lock yourself out of capturing new work. Once unlocked
for a session it stays unlocked; you're not asked again until you restart
the app.

### OS control — beyond files and projects

PCM can also act directly on your machine through the same chat, in
natural language:

- `open notepad` / `launch spotify` — starts a known app by name (a small
  built-in alias map, e.g. "notepad" → `notepad.exe`), or tries the name
  as given for anything else.
- `close chrome` / `quit spotify` — asks for confirmation first, since it
  terminates the matching process(es).
- `lock my screen`
- `take a screenshot` — saved to `Pictures/PCM_Screenshots`, requires
  Pillow (already in requirements.txt).
- `create a folder called X at <path>`
- `delete file <path>` / `empty the recycle bin` — both require typing
  "yes" to confirm, same pattern as every other destructive action in PCM.

With `PCM_LLM_ENABLED=true`, the exact app/file name is pulled out of
whatever you actually typed via the LLM (so "hey can you close spotify
for me, don't need it anymore" still works) rather than requiring a
rigid phrase. Without an LLM key, a simpler word-stripping fallback
handles common phrasings directly.

### Project memory timeline

`what did I work on Tuesday` (or "yesterday", any weekday) reconstructs
that day chronologically from the persistent event log — files touched,
commits made, tabs opened — grouped by project, not just a flat list.

### Natural-language code search

`find the code responsible for sending email notifications` searches
actual function and class names (extracted from `.py`/`.js`/`.ts`/etc.
files at save time, embedded the same way saved files and tabs are) and
returns matches as a file → function tree, not a text-match on file
contents.

### Developer productivity dashboard

`show me the project health dashboard` reports real, computed numbers:
open TODOs (regex count across recent files), uncommitted changes (real
git count), recent commits, and most-modified files. Failed tests and
documentation coverage are reported as **not available** rather than
guessed — PCM doesn't run your test suite or do deep code analysis, and
won't pretend it does.

### AI project mentor

After every save, PCM checks a few simple heuristics and mentions
anything worth knowing: an auth-related file changed with no test file
touched, several code files changed with the README untouched, or
uncommitted changes carried over from your last session. These are
pattern-matching heuristics, not real code understanding.

### Human-in-the-loop safety on resume

Resuming now restores everything safe immediately, then — if there's
anything risky (like reapplying uncommitted Git changes) — shows an
`⚠ ACTION REQUIRED` preview and waits for you to say "yes" before doing
it, instead of doing it automatically. Genuinely dangerous single
actions (like re-running a shell command) get their own `⚠ HIGH-RISK
ACTION` framing. Say "no" at any point and it leaves your files alone.

## Running tests

```bash
cd backend
pytest -q
```

## Running experiments

```bash
cd experiments/datasets
python generate_benchmark.py        # writes benchmark.json (25 tasks)

cd ../baselines
python keyword_baseline.py          # standalone keyword-only accuracy

cd ../evaluation
python run_retrieval_eval.py --no-semantic   # drop --no-semantic once a model is cached
python run_ablation.py --no-semantic
```

Results are written to `experiments/results/`. No numbers in this repository
are fabricated — everything is produced by actually running the scripts
above against the real retrieval code, using synthetic benchmark projects
(the field `--no-semantic` disables the embedding model for fully offline
runs; drop it once `all-MiniLM-L6-v2` is cached locally to get real semantic
retrieval numbers).

## Privacy

- All data stays local in SQLite by default.
- File contents and browser history are never uploaded.
- Only short text (project name + a locally generated description) is used
  for embeddings, computed locally — no external API calls are required for
  core functionality.
- `DELETE /data` (also available as a button in the Dashboard) wipes all
  stored projects, snapshots, and logs.

## Safety

Terminal commands recorded in a snapshot are never executed automatically.
The restoration plan separates safe components (opening files/folders/tabs)
from ones needing explicit confirmation (running a command, checking out a
branch with modified files present). Dangerous patterns (`rm -rf`, `format`,
etc.) are filtered out entirely and never offered for restoration.

## Project structure

```
project-context-manager/
├── backend/            FastAPI + SQLite + collectors + retrieval + restoration
├── frontend/            React UI (Dashboard, Search/Restore, Project view)
├── experiments/         Benchmark, baselines, evaluation, ablation, results
├── scripts/              (placeholder for future automation)
├── docs/                 Architecture + research documentation
├── .env.example
└── README.md
```

## What this is not

Per the project's scope constraints: no multi-agent architecture, no custom
LLM training/fine-tuning, no cloud infrastructure, no authentication, no
voice/vision features, no general-purpose chatbot. The LLM is optional and
only used (if enabled) for intent extraction/description enrichment — the
system fully functions without any external API.
