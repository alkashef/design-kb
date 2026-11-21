# Plan

Next milestone number: 26

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M25** Engineer term | The code and the tests say "engineer": the page texts, the addresses `/engineers...`, the fields, markers and tables, and the module, template and test file names. No behavior changes | sonnet | low | open |

## Milestones

### M25 — Engineer term

- **Refs:** D-44, D-29, D-25, D-22, and spec 0.4, which names the person "engineer" in section 2 and in FR-01, FR-02, FR-04, FR-05, FR-06, FR-07, FR-10, FR-11, FR-12, FR-13, FR-20, FR-23, FR-24, FR-25, FR-28, FR-29, FR-42, NFR-04 and NFR-06. No behavior changes. Today the code and the tests still say "employee" (the earlier term of D-44) in 46 files under `src/` and `tests/`. `docs/design.md` already has the new names: its sections "Architecture", "Data storage" and "Interfaces" are the reference for each name.
- **Owner:** every module, template and stylesheet under `src/` that names the term ("Architecture" lists the modules), and every file under `tests/`.
- **Tests first:** the test session changes the existing tests, because the requirement text changed (D-44). It reads the names in the design, not in `src/`.
  - In every file under `tests/` (the tests, `conftest.py`, `builders.py`, `fakes.py`), each name and text with the earlier term takes "engineer" in the same case: the routes under `/engineers` and `/search/preview/{engineer_id}`, the form field `engineer_id`, the marker `data-engineer-id`, the store methods (`list_engineers`, `add_engineer` and the others of "Interfaces"), the data class `Engineer` and the fields `engineer_id`, `ranking.rank_engineers`, `seed_data.build().engineers`, the test names (`test_fr_20_create_engineer_...`), the helpers, and the texts that a test reads from a page. `tests/route/test_employees.py` becomes `tests/route/test_engineers.py` (`git mv`). Each test keeps its spec ID, its case and its assertions. No test is removed or weakened. The IDs stay `E-0001`.
  - unit, in a new file: `test_d_44_no_file_under_src_and_tests_holds_the_earlier_term`: it walks `src/` and `tests/`, skips each folder `__pycache__`, and fails with the list of paths when a file name, or the text of a `.py`, `.html`, `.css` or `.js` file, holds the earlier term in any case. The test builds the term from two parts, so its own file passes. It fails today, because of `src/`.
  - route: `test_d_44_sidebar_and_engineers_page_use_the_term`: on `GET /engineers` the sidebar has a link to `/engineers` with the text "Engineers" and a link to `/engineers/new` with the text "Add engineer", and the page heading is "Engineers". It fails today, because the route does not exist.
  - Manual: NFR-01.
- **Build:** rename with `git mv`: `src/services/employees.py` and `src/web/routes/employees.py` to `engineers.py`, and the templates `employees.html`, `employee_form.html` and `employee_profile.html` to `engineers.html`, `engineer_form.html` and `engineer_profile.html`. In every file under `src/`, replace the earlier term with "engineer" in the same case (lower case, capitalized, upper case): identifiers, imports, routes, form fields, markers, table and field names, CSS classes, docstrings, comments, log texts and page texts. Change nothing else: no logic, no layout, and no message wording apart from the term. Add no code that reads or migrates tables with the earlier names (D-44). Change no file in `tests/`.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M25` pass.

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
