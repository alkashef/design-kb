# CLAUDE.md

## Project

- Purpose: A knowledge base for an integrated circuit (IC) design team. It records who has experience in which skills, and users search it to find the right experience.
- Stack: Python with FastAPI. The server renders the pages with Jinja templates, and HTMX gives the interactive parts. `docs/design.md` (D-15, D-16, D-20) owns the stack.
- Status: proof of concept (PoC). It proves the idea and is not a full product, so quality measures that only pay back over time are cut.
- Docs: `docs/specs.md` (what to build, owned by the user), `docs/design.md` (how it is built), `docs/plan.md` (the milestones that are left), and `docs/workflow.md` (how the work is done). Read the spec before changing behavior.

## Workflow

- Follow the workflow in @docs/workflow.md exactly.
- Requirements live only in `docs/specs.md`. Never implement one that exists only in chat, code, or memory. If a request is not covered by the spec or contradicts it, stop and ask.
- Cite spec and design IDs. Do not copy their content into this file or into code comments.
- These files are the only spec, design, and plan of this project. A skill that would write one of them to another place writes to these files instead.
- Do not refactor, rename, or move anything outside the current milestone.

## Run

- Environment: the conda environment `design-kb`. Activate it with `conda activate design-kb`.
- Install: `pip install -r requirements.txt`, and `pip install -r requirements-dev.txt` for the tests.
- Start: `python main.py`. It runs the FastAPI app; the host and port come from `config/.env`.
- Test: `python scripts/check.py` runs the tests. The git pre-commit hook runs the same.
- Verify: after a change, start the app, use the changed feature once, and report what you saw. If you cannot run it, say so.

## Communication and reporting

- In general, a reply is only a TLDR: what the user needs to know if they read nothing else. No narration, no recap, no report, no insight or explanation blocks. Give more only when the user asks for it.
- Ask every question in a user dialog (the question tool with options), never in the text of a reply. Put one question in one dialog. Give the options, each with brief pros and cons, and mark the recommended option. When the question comes from something the user asked for, quote the user's own words.
- When the material for a question is too long for a dialog (a directory structure, a table, a draft), put the material in the chat and only the question and the short options in the dialog.
- Walk the user through every open question and every decision that needs them, one dialog after the other, until each is settled. Never settle one silently or bury it in a reply.
- Go top-down, big picture first. Do a multi-part task in one go.
- On requirements, architecture, and security decisions, act as a rigorous critical-thinking partner: challenge assumptions, expose blind spots, test the reasoning, present alternatives, and agree only when the argument is strong. On requirements act as a product manager; on architecture act as a software architect. For small or routine changes, and while executing approved work, do not debate. Flag only blockers and conflicts with the requirements.

End every task with the report: one line, whole line in bold, that starts with `TLDR:`.

- The TLDR always states a test that failed, a check that did not run, and a step that was skipped.
- An open question does not go into the TLDR: it goes into a dialog.
- In a milestone, in chat or unattended, ask only for a blocker of `docs/workflow.md`, step 5. Decide everything else by its Rules, and put each `DECISION:` line above the TLDR.

## Architecture and layers

- `docs/design.md` defines the layers and their modules. Follow them.
- Before writing code, name the module that owns the change. Before creating a module, state its name, layer, and single responsibility.
- One module per concern. Entry points (the main script and the app factory) only import and connect modules. They hold no logic.
- The UI (the Jinja templates and the HTMX attributes in them) contains no business or application logic; it only renders and translates user input into backend requests. All application logic lives in the backend. Business logic is pure: no HTTP, UI, or database imports. The API layer translates requests and delegates to business logic.
- Exactly one module talks to each external system (a file area, a database, a network API). A module exposes only what others need and never reaches into another module's internals.
- Pass anything that touches an external system (repository, API client, file writer) into the code that uses it, so tests can use fakes. Do not use a dependency-injection framework.
- Changing a layer, a module boundary, the data storage, the public API, or the tech stack needs a decision recorded in `docs/design.md`. Outside a milestone it also needs the user's approval; in a milestone, `docs/workflow.md`, Rules, applies.

## Code quality

- Each class has one responsibility. Each function does one thing.
- Avoid complex patterns: prefer plain functions and simple classes. No metaclasses, no inheritance deeper than one level, and no design patterns unless the code needs one.
- Write at the level of an intermediate programmer. Write clear, readable code.
- Put all imports at the top of the file.
- Python code uses docstrings. A class docstring states the class's responsibility.
- Python follows PEP 8. Each JavaScript function has a one-line JSDoc comment.
- Use Python's `logging` module. Log each API request and error with context. Never log secrets or user data.
- Avoid these code smells (https://refactoring.guru/refactoring/smells):
  - long method
  - large class
  - long parameter list
  - duplicate code
  - dead code

## Testing

- Follow the test policy in `docs/design.md`. It says which code needs tests and how the app under test is built.
- Test public behavior: one behavior per test, and every test asserts something. Tests are deterministic, and they use invented data.
- Never weaken or edit an existing test to make it pass. Change one only when its requirement changed, and say so in the TLDR.

## Directory structure

- `README.md` (File structure) lists the top-level folders, and `docs/design.md` lists the modules and the folders below. Put a file where they say.
- All source code lives under `src/`, except the entry point `main.py`.
- `docs/specs.md`, `docs/workflow.md` and the files in `docs/ui/` change only after the user explicitly confirms that change; an earlier confirmation does not cover a later change. The AI keeps `docs/design.md` and `docs/plan.md` under the workflow. The app never reads or writes a file in `docs/`.
- Never edit a generated file by hand. Regenerate it with the script that makes it.
- `scripts/cleanup.py` removes caches and generated artifacts by name (for example `__pycache__`, tool caches, logs). It never deletes source, docs, config, input data, or dependencies.

## Configuration and constants

- Settings live in `config/.env`, which is never committed. `config/.env.example` is committed and lists every key; secret keys are empty. `config.py` is the only module that reads `config/.env` or the environment. A real environment variable overrides `config/.env`.
- Only the entry point imports `config`. It passes values down as arguments.
- Never write a behavior-affecting value inline: URLs, ports, file paths, thresholds, limits, timeouts. They come from config.
- To add a setting, add the key to `config/.env.example` and `config/.env`, read it in `config.py`, and explain it in `docs/design.md`.

## Dependencies

- Prefer the standard library. Ask before adding a new framework or large library. Install only into the project's environment, never globally. A library that `docs/design.md` names in a `Decided` decision is approved and needs no further ask.
- List direct dependencies in `requirements.txt`, pinned to the installed version. `requirements-dev.txt` lists what only the tests and the check scripts need.

## Git and destructive actions

- Work on `main` unless told otherwise. Never commit `config/.env`, secrets, user data, exports, logs, or caches. Before the first commit, check that `.gitignore` covers them.
- Never force-push, and never run `reset --hard`, `git clean`, or `git restore`. Ask the user before recursive deletes, installs, killing processes, or editing `CLAUDE.md` or `.claude/settings.json`. Never get around these rules with a different command. `.claude/settings.json` enforces them.
- Never skip the pre-commit hook.
- Clear caches with `scripts/cleanup.py`. Never touch files outside this repo (except scratch folders you make and delete) or another program's process.

## Security and privacy

- Secrets (API keys, tokens, passwords, database IDs) live only in `config/.env` or the platform's secret store. They never appear in code, committed files, logs, error messages, reports, or browser-side code.
- User data stays on the machine. A flow of user data to an external service must be approved by the user. Servers listen on `127.0.0.1` unless the user approves otherwise. Telemetry is off. At run time the app calls only the services the user has approved.
- Never run or debug against the user's real data. Copy it to a scratch folder, point the process at the copy through environment variables of that process only, and delete the copy afterwards. Reports give counts, never content. Never put real personal data in source or docs. Use invented data.

## Living docs

- Update every doc in the table below that a change makes inaccurate in the same change, and be specific: "Added `src/backend/search.py`: ranks employees", not "updated code". Each doc owns one kind of fact. Link to the owner; do not copy.

  | Change | Update |
  | --- | --- |
  | Behavior or a requirement | `docs/specs.md`, with the user's approval |
  | The data model (`docs/specs.md`, section 2) | `docs/specs.md`, with the user's approval |
  | Architecture, modules, data storage, interfaces, settings, approved libraries | `docs/design.md` |
  | What the app does, setup, how to run, top-level folders | `README.md` |
  | A setting added or changed | `config/.env` and `config/.env.example` |
  | A library added or removed | `requirements.txt`, in the same change as the import |

- `README.md` always has: What it does, Stack (with versions), File structure (top-level folders, one line each), Setup, How to run, How to check. Setup explains how to install dependencies, configure `config/.env`, and set up and check every external dependency before the first run.
- Never edit `CLAUDE.md` without the user's approval. When a fact in it goes stale (stack, run command) or a rule needs to change, flag it, propose the exact change, and edit only after approval.
