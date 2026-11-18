# Plan

Next milestone number: 25

The milestones that are left, in build order. `docs/workflow.md` gives the loop and the templates. The libraries of D-23 are installed in the conda environment `design-kb` and pinned in the requirements files.

## Milestones at a glance

| Milestone | Delivers | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M22** Light theme colors | The app shows the colors of D-43: grey surfaces, a dark sidebar, beige cards and fields, the orange accent on fills and edges | sonnet | high | open |
| **M23** Console type | Navigation, buttons, filter controls, crumbs and paths are in JetBrains Mono; names, headings, body text and form values stay in Inter | sonnet | low | open |
| **M24** Red delete and error | The delete buttons of an employee and of a project are a red outline; an error message is red text on a red tint | sonnet | medium | open |

## Milestones

### M22 — Light theme colors

- **Refs:** NFR-01, D-43, D-19, D-31. No requirement changes. The user chose the light style on the canvas on 2026-11-18 ("switch the whole design to the new theme"). The 8 artboards in `docs/ui/` show it, and `docs/design.md`, section "Visual style", gives each color, its use and the rules. Today `src/web/static/app.css` holds the dark colors of D-17 as 13 custom properties in `:root`.
- **Owner:** `src/web/static/app.css`.
- **Tests first:** route, in a new file. Each test reads the `app.css` that the Search page (`/`) links, as `tests/route/test_split_bodies.py` does. Before a value is compared, each `var(--name)` in it is replaced by the value that `:root` gives `--name`, and a color is compared without regard to case. The ground of a selector is the `background` or the `background-color` of its plain rule.
  - `test_nfr_01_stylesheet_has_none_of_the_dark_colors`: the stylesheet holds none of `#0C0D10`, `#14161B`, `#181B21`, `#101216`, `#1E2128`, `#23262E`, `#2A2E38`, `#ECEEF2`, `#D5D8DF`, `#9AA1AD`, `#6EE7B7`, `#04130D`, `#12221D`. It fails today, because `:root` defines all 13.
  - `test_nfr_01_page_ground_is_grey_with_dark_text`: the ground of `body` is `#EDEDED` and its `color` is `#1F1F21`.
  - `test_nfr_01_sidebar_is_graphite_with_light_text`: the ground of `.sidebar` is `#2C2D30` and its `color` is `#F4F4F4`. The ground of `.nav a.active` is `#45464A`.
  - `test_nfr_01_primary_button_is_orange_with_dark_text`: the ground of `.button-accent` is `#F04A0E` and its `color` is `#141416`.
  - `test_nfr_01_cards_are_beige_and_their_fields_white`: the ground of `.panel` is `#FAF6EC`. The ground of the rule whose selector list holds `.panel input` is `#FFFFFF`.
  - `test_nfr_01_accent_is_a_fill_and_never_a_text_color`: one or more declarations other than `color` resolve to `#F04A0E`, and no `color` declaration of any rule resolves to `#F04A0E`. It fails today, because the stylesheet has no `#F04A0E`.
  - Manual: NFR-01.
- **Build:** in `app.css`, replace the 13 colors of `:root` by the custom properties of section "Visual style", and give each rule the property of its use, as the artboard of its page shows. The uses that the tests do not fix:
  - The sidebar: links that are not active in `--sidebar-muted`; the active link in `#FFFFFF` with an inset left edge of 3px in `--accent`; the Add employee button with the border `--sidebar-line` and the text `--sidebar-text`.
  - The split pages: the list columns (`.results`, `.outline`) on `--bg-list`, the detail columns (`.preview`, `.node-detail`) on `--bg-detail`, and the form panel of Projects (`.assignment-panel`) on `--bg`.
  - Cards and tables (`.panel`, `.table`, `.assignment`, `.level-card`, `.preview-projects`) on `--panel` with the border `--line-card` and inner dividers in `--line-soft`. A field on a grey ground (`.query`, the fields of `.filters`, the text box of `.inline-form` in the outline) on `--panel`; a field inside a card on `--field`.
  - A selected row (`.result.selected`, `.outline-row.selected`) on `--panel` with the edge in `--accent`; the text of a selected outline row in `--accent-text`.
  - Level bars: off `--meter-off`, on `--accent`. A level name (`.level-label`) in `--accent-text`. A Lead tag (`.role-tag.lead`) with the border `--accent`, the ground `--accent-bg` and the text `--accent-text`. The rank of a result in `--graphite`. An avatar on `--track` with the text `--graphite`.
  - Links in the page: `--text-muted`, and `--text` on hover.
  - The header comment of the file cites D-43 in place of D-17.

  Change no layout, no font, no template and no artboard. The property names of "Visual style" are a proposal: a different name is a decision of the session (`docs/workflow.md`, Rules).
- **Gate:** `python scripts/check.py` and `python scripts/spec_coverage.py M22` pass.

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
