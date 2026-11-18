# Plan

Next milestone number: 25

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M23** Console type | Navigation, buttons, filter controls, crumbs and paths are in JetBrains Mono; names, headings, body text and form values stay in Inter | sonnet | low | open |
| **M24** Red delete and error | The delete buttons of an employee and of a project are a red outline; an error message is red text on a red tint | sonnet | medium | open |

## Milestones

### M23 — Console type

- **Refs:** NFR-01, D-43, D-19. No requirement changes. D-43 sets the navigation, the buttons, the filter controls, the metadata lines and the paths in JetBrains Mono, and the names, headings, body text and form values in Inter. Today `app.css` sets the navigation, the buttons, the query, the filters and the crumbs in `--font-sans`.
- **Owner:** `src/web/static/app.css`, and `src/web/templates/partials/search_body.html` for one class.
- **Tests first:** route, in a new file. Each test reads the `app.css` that the Search page (`/`) links, and resolves `var(--name)` through `:root` as the tests of M22 do. The font family of a rule is the family in its `font-family`, or in its `font` shorthand.
  - `test_nfr_01_console_font_on_controls_and_inter_on_text`: one test of the font roles of D-43. The font family starts with `"JetBrains Mono"` in the plain rule of each of `.nav`, `.button-outline`, `.button-accent`, `.query input` and `.crumbs`. A rule whose selector list holds `.filters input` sets a font family that starts with `"JetBrains Mono"`, and so does one whose selector list holds `.filters select`. The font family of `body` starts with `"Inter"`, and so does the font family of the rule whose selector list holds `.panel input`. No rule for `.result-name`, `.result-reason`, `.preview-name` or `.assignment-text` has a font family that starts with `"JetBrains Mono"`. It fails today, because the first 7 rules use Inter or set no family.
  - Manual: NFR-01.
- **Build:** in `app.css`, set `var(--font-mono)` on `.nav`, `.button-outline` (and `.actions .button-outline`, which sets its own font), `.button-accent`, `.query input`, `.crumbs`, the fields of `.filters`, the role and team line of a result and of a person row, and the skill path of a level card (`.path-text`), with the sizes of the artboards (13px for a button and a link of the navigation, 15px for the query, 12px for a chip, a metadata line and a path). The rule `.filters input, .filters select, .panel select` is shared: split it, so that a `select` inside a card keeps Inter. The role and team line of a result has only the class `muted`: give it a class of its own in `src/web/templates/partials/search_body.html`. Change no color, no layout and no other template.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M23` pass.

### M24 — Red delete and error

- **Refs:** NFR-01, D-43, D-19, D-29 (the marker `role="alert"`). No requirement changes. The rule of D-43: a destructive action and an error are red as an outline or as text, never as a fill. The artboards `Profile`, `EmployeeForm` and `Projects` show a red Delete button, and `EmployeeForm` shows a red error message. Today the Delete buttons have the look of every outline button, and an element with `role="alert"` has the neutral look of `.message`.
- **Owner:** `src/web/static/app.css`, and the templates `src/web/templates/employee_profile.html` and `src/web/templates/projects.html`.
- **Tests first:** route, in a new file. The stylesheet tests read the `app.css` that the Search page links and resolve `var(--name)` as the tests of M22 do.
  - `test_nfr_01_error_message_is_red_text_on_a_red_tint`: a rule whose selector list holds `[role="alert"]` has the `color` `#B42318`, the ground `#FBEAE7` and a border in `#E5A9A2`. It fails today, because no rule names `[role="alert"]`.
  - `test_nfr_01_delete_buttons_of_employee_and_project_are_marked`: with the seed data, on `GET /employees/E-0001` the submit button of the form that posts to `/employees/E-0001/delete` has the class `button-danger`. On `GET /projects` the submit button of the form whose action ends in `/delete` and starts with `/projects/` has the class `button-danger`. It fails today, because no element has that class.
  - `test_nfr_01_delete_button_is_a_red_outline`: the plain rule of `.button-danger` has the `color` `#B42318` and a border in `#D9A098`, and its ground is `transparent` or not set.
  - Manual: NFR-01.
- **Build:** add the custom properties `--danger`, `--danger-line` and `--danger-bg` of "Visual style" if M22 did not, a rule `.button-danger` after `.button-outline`, and a rule for `[role="alert"]` after `.message`. Give the class `button-danger` to the Delete button of the employee profile and of the selected project. The Delete button of an assignment and the remove button of a flag stay neutral, as on the artboards. The session decides the Delete button of the skill tree, which the artboard shows only when it is disabled. Change no route, no field name and no message text.
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M24` pass.

## Human checks

Do these after the run. Start Ollama with the model of D-16, then run `python main.py`.

- FR-02, AC-01: run the 3 example searches of the spec. The expected person is in the top 5 results of each search.
- NFR-01: open each of the 8 pages in a desktop browser and compare it with its artboard on the canvas (D-19).
- NFR-01, M16, M18: on Employees, Search, Skill tree and Projects, each with a long list, scroll down. The sidebar stays in view, and its Add employee button stays reachable.
- NFR-01, M19, M20: open Skill tree and select a leaf at depth 2. The add-child text box and button sit in a card like the Name and Description card. The path to the leaf is open, the other branches are folded, and the caret folds and unfolds a branch. Compare with the artboard `docs/ui/SkillTree.dc.html`.
- NFR-01, M17: open Settings and compare the Level thresholds with the artboard `docs/ui/Settings.dc.html`: the table, its 5 columns and its 5 rows.
- NFR-01, M22, M23, M24: open each of the 8 pages and compare its colors and fonts with its artboard in `docs/ui/` (D-43): the dark sidebar, the grey surfaces, the beige cards, the orange accent on fills and edges only, JetBrains Mono on the navigation, the buttons and the filters, and the red Delete buttons and error message. Read the text on each surface: nobody measured the contrast on a screen.
- NFR-03: the app and Ollama run on one machine, and the server listens on `127.0.0.1`.
- NFR-06: read the seed names in `src/domain/seed_data.py`. Each name is invented.
- D-16: `OllamaEmbedder` has no automated test, because no test calls Ollama. Save an assignment while Ollama runs. Then stop Ollama, save one more, and make sure that the page shows the message.
