# Plan

Next milestone number: 22

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M19** Add child card | The Add child text box and button sit in a card like the Name and Description card | haiku | low | open |
| **M20** Foldable skill tree | Each node with children folds. On load, the selected node and its ancestors are open and the other branches are folded | sonnet | medium | open |
| **M21** Skip tests for docs-only commits | The pre-commit check skips pytest when every staged file is under `docs/` | sonnet | low | open |

## Milestones

### M19 — Add child card

- **Refs:** NFR-01, FR-30, D-19.
- **Owner:** `src/web/templates/skill_tree.html`.
- **Tests first:** route: `test_nfr_01_add_child_form_is_in_a_card`: on the Skill tree page of a selected node (`/skill-tree/{id}`), the text box for the name of the new child and the Add child button are both inside an element with the class `panel`, the class of the Name and Description card. It fails today, because the add-child form sits outside any `.panel`.
- **Build:** put the add-child form in its own card with the class `panel`, below the Name and Description card, so it looks like that card.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M19` pass.

### M20 — Foldable skill tree

- **Refs:** NFR-01, FR-30, D-19.
- **Owner:** `src/domain/skill_tree.py` (which nodes are open: the selected node and its ancestors), `src/services/skill_tree.py`, `src/web/templates/skill_tree.html`, `src/web/static/app.css`.
- **Tests first:** route, with the seed data:
  - `test_fr_30_outline_folds_each_parent_node`: on `/skill-tree`, each node with children is a `<details>` element whose `<summary>` holds the row of that node, and the rows of its children are inside that `<details>`. A leaf is not a `<details>`.
  - `test_fr_30_outline_opens_path_to_selected_node`: on `/skill-tree/{id}` of a leaf at depth 2 or more, the `<details>` of each ancestor of the leaf has the `open` attribute, and the `<details>` of a top-level node that is not an ancestor does not.
  - `test_fr_30_outline_folded_without_selection`: on `/skill-tree`, no `<details>` has the `open` attribute, and the row of every top-level node is in the page.
- **Build:** render the outline as nested `<details>`/`<summary>` (native folding, no JavaScript). The backend gives the template the set of open nodes: the selected node and its ancestors. The caret toggles the fold and the name still opens the node. Keep the existing row links and their data attributes. Style the carets as on the artboard: ▾ open, ▸ folded, · leaf.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M20` pass.

### M21 — Skip tests for docs-only commits

- **Refs:** D-30.
- **Owner:** `scripts/check.py`.
- **Tests first:** unit, against a new pure function `needs_tests(staged_paths)` in `scripts/check.py` that returns whether the tests must run:
  - `test_check_skips_tests_when_only_docs_staged`: `["docs/plan.md", "docs/specs.md"]` gives False.
  - `test_check_runs_tests_when_code_staged`: `["docs/plan.md", "src/app.py"]` gives True.
  - `test_check_runs_tests_when_nothing_staged`: `[]` gives True, so a run by hand and the checks of a milestone still run the tests.
- **Build:** `main()` reads the staged paths with `git diff --cached --name-only --no-renames` and runs pytest only when `needs_tests` returns True. When it skips, it logs one line that says so. `--no-renames` lists both the old and the new path of a moved file, so a move from `src/` into `docs/` still runs the tests.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M21` pass. `docs/design.md`, Test policy, says that a commit whose staged files are all under `docs/` skips the tests.

## Human checks

Do these after the run. Start Ollama with the model of D-16, then run `python main.py`.

- FR-02, AC-01: run the 3 example searches of the spec. The expected person is in the top 5 results of each search.
- NFR-01: open each of the 8 pages in a desktop browser and compare it with its artboard on the canvas (D-19).
- NFR-01, M16, M18: on Employees, Search, Skill tree and Projects, each with a long list, scroll down. The sidebar stays in view, and its Add employee button stays reachable.
- NFR-01, M19, M20: open Skill tree and select a leaf at depth 2. The add-child text box and button sit in a card like the Name and Description card. The path to the leaf is open, the other branches are folded, and the caret folds and unfolds a branch. Compare with the artboard `docs/ui/SkillTree.dc.html`.
- NFR-01, M17: open Settings and compare the Level thresholds with the artboard `docs/ui/Settings.dc.html`: the table, its 5 columns and its 5 rows.
- NFR-03: the app and Ollama run on one machine, and the server listens on `127.0.0.1`.
- NFR-06: read the seed names in `src/domain/seed_data.py`. Each name is invented.
- D-16: `OllamaEmbedder` has no automated test, because no test calls Ollama. Save an assignment while Ollama runs. Then stop Ollama, save one more, and make sure that the page shows the message.
