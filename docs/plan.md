# Plan

Next milestone number: 27

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M26** Runner reads the human checks | The runner's coverage step counts a spec ID that "Human checks" names as manual, so a finished milestone is not reported as failed | sonnet | low | open |

## Milestones

### M26 — Runner reads the human checks

- **Refs:** `docs/workflow.md` (Execute, step 4, the checks) and the rule in the docstring of `scripts/spec_coverage.py`: a spec ID is manual when a Manual entry of a milestone block or the section "Human checks" of `docs/plan.md` names it. No requirement and no design decision changes, and this entry names no spec ID on purpose. The fault: `coverage_problem` in `scripts/milestones-runner.py` gives the script a plan that holds only the milestone's block. A spec ID that is manual only through "Human checks" then counts as planned, and the runner reports a finished milestone as failed. Seen on 2026-11-21: M25 was committed and pushed, and the runner stopped with "no test and no Manual entry" for two spec IDs of its Refs.
- **Owner:** `scripts/milestones-runner.py` (the function `coverage_problem`).
- **Tests first:** unit, in a new file `tests/unit/test_runner_script.py`. It loads `scripts/milestones-runner.py` by its path with `importlib`, as `tests/unit/test_check_script.py` loads `check.py`; register the module in `sys.modules` before it runs, because it defines data classes. The interface: `coverage_problem(root, milestone_id, block)` takes the root folder as a `Path`, the milestone number and the lines of the milestone's block. It runs `<root>/scripts/spec_coverage.py` over a temporary copy of `<root>/docs/specs.md` and `<root>/tests/`, and returns `None` when the check passes or a text with the reason when it fails.
  - `test_runner_coverage_counts_an_id_of_human_checks_as_manual`: the test makes a temporary root with a copy of `scripts/spec_coverage.py`, an invented `docs/specs.md` with one FR row and one NFR row, a test file under `tests/` whose test name carries the FR ID, and a `docs/plan.md` that has no milestone block and whose section "## Human checks" names the NFR ID. The call with a block whose Refs name both IDs, and whose Tests first has no Manual part, returns `None`. It fails today, because the result says that the NFR ID has no test and no Manual entry.
- **Build:** in `coverage_problem`, write the temporary plan as the block followed by the section "## Human checks" of `<root>/docs/plan.md`: from its heading up to the next heading of level 1 or 2, or to the end of the file, and nothing when the plan has no such section. Update the docstring of the function and the paragraph of the module docstring that describes this check. Change nothing else in the runner.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M26` pass.


## Human checks

Do these after the run. Start Ollama with the model of D-16, then run `python main.py`.

- D-44, M25: before the first start after M25, delete the folder `data/` (`DATA_DIR`) one time. Its tables have the earlier names, and the store does not migrate them. Then start Ollama and the app: the seed data loads again, and the Engineers page lists 40 engineers.
- NFR-01, M25: open each of the 8 pages and compare its texts with its artboard in `docs/ui/`: the sidebar link "Engineers", the button "Add engineer", the headings "Engineers" and "Edit engineer", and the labels "Engineer ID" and "Engineer name".
- FR-02, AC-01: run the 3 example searches of the spec. The expected person is in the top 5 results of each search.
- NFR-01: open each of the 8 pages in a desktop browser and compare it with its artboard on the canvas (D-19).
- NFR-01, M16, M18: on Engineers, Search, Skill tree and Projects, each with a long list, scroll down. The sidebar stays in view, and its Add engineer button stays reachable.
- NFR-01, M19, M20: open Skill tree and select a leaf at depth 2. The add-child text box and button sit in a card like the Name and Description card. The path to the leaf is open, the other branches are folded, and the caret folds and unfolds a branch. Compare with the artboard `docs/ui/SkillTree.dc.html`.
- NFR-01, M17: open Settings and compare the Level thresholds with the artboard `docs/ui/Settings.dc.html`: the table, its 5 columns and its 5 rows.
- NFR-01, M22, M23, M24: open each of the 8 pages and compare its colors and fonts with its artboard in `docs/ui/` (D-43): the dark sidebar, the grey surfaces, the beige cards, the orange accent on fills and edges only, JetBrains Mono on the navigation, the buttons and the filters, and the red Delete buttons and error message. Read the text on each surface: nobody measured the contrast on a screen.
- NFR-03: the app and Ollama run on one machine, and the server listens on `127.0.0.1`.
- NFR-06: read the seed names in `src/domain/seed_data.py`. Each name is invented.
- D-16: `OllamaEmbedder` has no automated test, because no test calls Ollama. Save an assignment while Ollama runs. Then stop Ollama, save one more, and make sure that the page shows the message.
