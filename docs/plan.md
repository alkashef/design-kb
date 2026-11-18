# Plan

Next milestone number: 18

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M16** Pinned sidebar | The left sidebar stays in view while the page scrolls | sonnet | medium | open |
| **M17** Thresholds table | The Level thresholds on the Settings page are a table, as on the artboard: one row for each of the 5 levels | sonnet | medium | open |

## Milestones

### M16 — Pinned sidebar

- **Refs:** NFR-01, D-19. No spec row states this behavior: the user asked for it in chat on 2026-11-18 ("the left panel is frozen, it doesn't scroll with the rest of the page"; answer: "Sidebar stays in view"). The sidebar of every page is pinned to the top of the window while the rest of the page scrolls. The look at the top of the page stays the same as the artboards in `docs/ui/`, so no agreed page changes.
- **Owner:** `src/web/static/app.css` (the rule of `.sidebar`).
- **Tests first:** route: `test_nfr_01_sidebar_rule_pins_sidebar_to_window` (the client gets the stylesheet that the pages link; the `.sidebar` rule has `position: sticky`, `top: 0`, a height of the window, and `overflow-y: auto` so that a sidebar taller than the window scrolls by itself; it fails while the rule has none of them). Manual: NFR-01.
- **Build:** add those declarations to the `.sidebar` rule, and `align-self: flex-start` so that the flex row does not stretch it to the page height. Change no template, no artboard and no other rule.
- **Gate:** the tests and the checks in `CLAUDE.md` pass.

### M17 — Thresholds table

- **Refs:** FR-31, NFR-01, D-19. No requirement changes. The user asked for it in chat on 2026-11-18 ("settings > Level thresholds: use a table"). Today `settings.html` shows the thresholds as rows of loose text with one mono line as header. The agreed artboard `docs/ui/Settings.dc.html` shows a table with the columns LEVEL, NAME, SOURCE, LEAD PROJECTS (FROM · TO), MEMBER PROJECTS (FROM · TO), and a row for each of the levels 1 to 5. Levels 1 and 5 have a note in place of the two ranges. This milestone brings the page to the artboard; it does not change the artboard.
- **Owner:** `src/web/templates/settings.html`, `src/web/static/app.css`, and `src/web/routes/settings.py` if the page needs the rows of levels 1 and 5 in its context.
- **Tests first:** route: `test_fr_31_settings_thresholds_are_a_table_with_the_five_columns` (`GET /settings` has a `<table>` whose header cells are Level, Name, Source, Lead projects, Member projects; fails today because the page has no table), `test_fr_31_settings_table_has_a_row_for_each_of_the_five_levels` (5 body rows, in the order 1 to 5, with the level names of the app), `test_fr_31_settings_table_edits_levels_2_to_4_only` (the rows of the levels 2, 3 and 4 hold the 4 text fields each, with the field names of `docs/design.md`, section "Routes"; the rows of the levels 1 and 5 hold no field), `test_fr_31_settings_table_shows_the_saved_values` (after a save, `GET /settings` shows each saved number in its field). The tests of FR-35 and FR-36 stay as they are. Manual: NFR-01.
- **Build:** replace the rows of `settings.html` by a `<table>` with a header row and one body row for each level. Levels 2 to 4 hold the 4 fields; levels 1 and 5 hold the note of the artboard. Keep the form, the field names, the two buttons and the message. Style the table in `app.css` as the artboard does (the `.table` look, with a horizontal scroll on a narrow window). Change no other page.
- **Gate:** the tests and the checks in `CLAUDE.md` pass. The routes and the field names do not change.

## Human checks

Do these after the run. Start Ollama with the model of D-16, then run `python main.py`.

- FR-02, AC-01: run the 3 example searches of the spec. The expected person is in the top 5 results of each search.
- NFR-01: open each of the 8 pages in a desktop browser and compare it with its artboard on the canvas (D-19).
- NFR-01, M16: on a page with a long list, scroll down. The sidebar stays in view, and its Add employee button stays reachable.
- NFR-01, M17: open Settings and compare the Level thresholds with the artboard `docs/ui/Settings.dc.html`: the table, its 5 columns and its 5 rows.
- NFR-03: the app and Ollama run on one machine, and the server listens on `127.0.0.1`.
- NFR-06: read the seed names in `src/domain/seed_data.py`. Each name is invented.
- D-16: `OllamaEmbedder` has no automated test, because no test calls Ollama. Save an assignment while Ollama runs. Then stop Ollama, save one more, and make sure that the page shows the message.
