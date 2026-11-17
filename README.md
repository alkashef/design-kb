# design-kb

## What it does

`design-kb` is a knowledge base for an integrated circuit (IC) design team. It records who has experience in which skills. Users search it to find the right experience.

It is a proof of concept (PoC). The app is built in milestones (`docs/plan.md`). Now it starts and shows the Search page in the Graphite style, with the sidebar and no login. The repository also holds the requirements, the design decisions, and the tools of the workflow.

| Document | Content |
| --- | --- |
| [docs/specs.md](docs/specs.md) | The requirements and the data model |
| [docs/design.md](docs/design.md) | The design decisions |
| [docs/workflow.md](docs/workflow.md) | How work goes from a requirement to a pushed commit |
| [CLAUDE.md](CLAUDE.md) | The project rules for the AI |

## Stack

| Part | Technology | Version |
| --- | --- | --- |
| Language | Python | 3.12 |
| Web app | FastAPI, Uvicorn, Jinja2, python-multipart | 0.163.1, 0.54.0, 3.1.6, 0.0.34 |
| Interactive parts | HTMX, as a local file | 2.0.11 |
| Vector store | LanceDB | 0.41.0 |
| Embedding model | `qwen3-embedding:0.6b`, run through Ollama | Install it in Setup, step 5 |
| Tests | pytest, httpx | 9.2.0, 0.28.1 |

`docs/design.md` owns these choices (D-15, D-16, D-20, D-23). `requirements.txt` and `requirements-dev.txt` pin the versions.

## File structure

| Folder | Content |
| --- | --- |
| `.claude/` | The skills of the workflow (`/sdd`, `/write-spec`, `/write-design`, `/write-plan`, `/write-tests`) and the logs of the milestone runner |
| `.githooks/` | The pre-commit hook. It runs the checks |
| `config/` | The settings: `.env.example` is committed, `.env` is not |
| `docs/` | The spec, the design, the plan and the workflow. `docs/ui/` holds a copy of the approved pages of the UI canvas |
| `scripts/` | The check scripts, the cleanup script and the milestone runner |
| `data/` | The files of the vector store at run time. Not committed. Appears with the first run |
| `src/` | The source code of the app, in four layers: `web/`, `services/`, `domain/`, `adapters/`. The entry point `main.py` is in the root |
| `tests/` | The tests, by level: `unit/` and `route/` |

## Setup

1. Create the conda environment and activate it:

   ```
   conda create -n design-kb python=3.12
   conda activate design-kb
   ```

2. Install the dependencies:

   ```
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Copy `config/.env.example` to `config/.env`. The defaults work on one machine. `docs/design.md`, section "Settings", explains each key.
4. Turn the commit hook on, one time for each clone:

   ```
   git config core.hooksPath .githooks
   ```

   Then tell the hook where the Python of the environment is, with the environment active. The hook then also works for a commit from a program that does not have the environment active, such as the Source Control panel of VS Code. In PowerShell:

   ```
   git config hooks.python (python -c "import sys; print(sys.executable.replace(chr(92), '/'))")
   ```

5. Install Ollama from https://ollama.com. Then get the embedding model and make sure that it is in the list:

   ```
   ollama pull qwen3-embedding:0.6b
   ollama list
   ```

   The app embeds each saved change with this model. When Ollama does not answer, the app saves nothing and shows a message. The checks do not use Ollama.

## How to run

Start Ollama first. Then:

```
python main.py
```

Then open `http://127.0.0.1:8000` in a desktop browser. The host and the port come from `config/.env`.

## How to check

Activate the conda environment `design-kb` first.

| Command | What it does |
| --- | --- |
| `python scripts/check.py` | Runs the tests. The pre-commit hook runs the same |
| `python scripts/spec_coverage.py` | Lists each spec ID as tested, manual, planned or missing |
| `python scripts/spec_coverage.py M3` | Makes sure that each spec ID of milestone M3 has a test or a `Manual:` entry |
| `python scripts/cleanup.py --dry-run` | Lists the caches and logs that `python scripts/cleanup.py` removes |
| `python scripts/milestones-runner.py` | Runs the milestones of `docs/plan.md` unattended. See `docs/workflow.md` |
