---
name: compare-map
description: Compare a curriculum map from this app with the ChatGPT reference map (docs/references/Grade_6_ELA_Curriculum_Map_2026-2027 - v2.html). Shows the options first - the whole workflow (generate a map with python main.py --generate, export it with python main.py --html, compare) or compare only (latest generated map, no cost). Outputs two cards, a table of quality dimensions with the better side and how to close each gap with smaller models, four measures, and open questions. Use whenever the user asks to run the app and compare, or to compare, benchmark, score, or diff an app map (or a map version) against ChatGPT or the reference, asks how good a build or model is against the reference, or asks how to get cheaper or smaller models to match ChatGPT quality, even if they do not say "skill" or name the file.
---

# Compare map

## Start: show the options

Before any other action, ask one question (AskUserQuestion) that lists what the skill can do:

1. **Whole workflow.** Generate a new map, export it as HTML, compare. Give the cost and time from the newest full-generation report in `log/cost/` (skip the `reads` reports): its `Cost (USD, approximate)` row, and the time from its first to its last call. Never quote a remembered figure. If no report exists, say the cost is unknown.
2. **Compare only.** Compare an existing map. Name the default: the newest folder in `data/maps/` that has a saved `vNNN.json`, its newest version, and its saved time. A newer folder with no version is a run in progress or a failed run; say so. The user can type another map id and version under "Other". No cost.

Skip the question only when the user's message or argument already chose: `full`, `compare-only [map id] [version]`, or plain words such as "generate and compare" or "compare the latest". A map id means compare only. Choosing option 1 approves the spend. Do not ask again.

## Steps

Use the `meas3` environment: `C:/Users/aa186095/AppData/Local/miniconda3/envs/meas3/python.exe` (`python` is not on the shell PATH). Run from the project root. Do not touch another program's process.

1. **Generate** (option 1 only). Make sure `config/.env` has the key and `LLM_ENABLED=true`, and that the example map is in `data/defaults/sources/` (README, Setup step 4). If not, name what is missing and stop. Run `python main.py --generate --needs "ADHD,ADD"` in the background, because it outlasts the tool limit. Do not poll. The output has `Map: <id>` and `Version: <n>`; exit code 0 means the map is ready. On exit 1, stop. Give the message and the map id, and say that Retry in the app resumes the map. Do not compare a half-finished map.
2. **Export.** Run `python main.py --html <map id> --version <n>`. Option 2 runs it only if `vNNN.html` is missing or has no `data-id="week:` (an export made before Build 8); it costs nothing. If it fails, give the error and go on with the JSON; say the HTML was not checked.
3. **Compare**, after step 2 ends:
   - Run `python -I .claude/skills/compare-map/scripts/metrics.py --map-id <id> --version <n>`. It prints the counts, the four measures, the models, the cost, the generation minutes, the integrity checks, the review issues, and the facts about the HTML file.
   - Read both maps side by side. Run the helper with `--front`, and with `--week N` for an early teaching week, a mid-term week, and a test or project week. Match weeks by date, not by number.
   - Read `prompts/README.md`, the prompt file of each stage you name (`stage1_front_matter.md` to `stage4_review.md`), and `src/backend/curriculum_map_schema.json`. Name a real prompt, schema field, stage, or code check in the "How to get closer" column.
   - Compare the map's `saved_at` with `git log -3 --format='%cI %s' -- prompts src/backend`. If the prompts changed after the map, write "already in prompt since <commit>; regenerate to confirm" and do not propose the same fix again.

## Output

Load `/asd-ste100` (skill `anthropic-skills:asd-ste100`) before you write. Follow both layers for all text below, in the flavored mode. Lint a draft of more than 60 words before you send it. Do not paste teacher content: use counts and quotes of at most 12 words.

Give each fact once. The card holds identity. The table holds the judgment. The measures hold the numbers. If a measure covers a row (rows 4 to 7 and 14 to 16), the row says the finding in words and does not repeat the number.

Output these five parts in this order, then save them to `log/compare/<map id>_vNNN.md` (create the folder; `log/` is not committed).

**1. Cards.** Two lists of `Title: value` pairs, with no table.
- *Reference map:* File, Weeks, Plan rows, Sections.
- *Other map:* Map id, Version, Models (per stage when several), Saved, Source (generated now, or existing), HTML file (size, rows drawn, details, inline assumption notes and screening notes, switches, tabs, search toolbar), Weeks, Plan rows.

**2. Table.** Use these columns: `No. | Quality dimension | App (<map id> vNNN) | Reference | Better | How to get closer to ChatGPT with smaller models`.
- App and Reference cells: one short observation each.
- Better: `App`, `Reference`, or `Tie`. If the evidence is thin, write `Tie` and say why in the cell.
- How to get closer: a concrete change when `Reference` is better. When `App` is better, say how to keep the lead on a smaller model, or write `Keep as is`.
- Dimensions, in this order. Add a row only for a gap the list misses; drop none.
  1. Structure and completeness of sections
  2. Calendar fidelity (weeks, breaks, exam windows)
  3. Lesson slots and row types
  4. Standards alignment (accuracy, not volume)
  5. Learning objectives
  6. Classwork detail
  7. Differentiation and support
  8. Texts, materials, and source use
  9. Assessments, tests, and projects
  10. Grading criteria (match the source, sum to 100)
  11. Writing types and progression
  12. Cultural and content suitability
  13. Internal consistency (ids, dates, references; integrity checks and review issues)
  14. Plain language
  15. Teacher usability (scannability, edits needed; the HTML export: size, contents panel, row and details panel, switches, tabs, search; scripts allowed)
  16. Honesty about gaps (assumptions and notes; whether assumptions are tied to an item of the map)
  17. Cost (money for one map: USD, models)
  18. Effort (time and calls to produce one map; the reference is `n/a` if it was not measured)

**3. Measures.** One table: `Measure | App | Reference | Better`. Take every number from `measures` in the helper output; do not compute by hand. Lower is better, except where the list says higher. Add a comment line for a group only if the table does not already say it.
- *Precision:* `standard_codes_in_catalog_share` (higher), `lessons_over_4_codes_share`, and the repeated shares of standards lists, objectives, classwork, and support text. A high repeated share means copy-paste, not coverage.
- *Length:* `classwork_chars_avg`, `classwork_share_over_100_chars` (the rule in `prompts/stage3_weeks.md`), `words_per_row_avg`, `words_in_weekly_plan`. Short is better only while the row stays usable.
- *Plain English* (`prompts/style.md`): `words_per_sentence_avg`, `sentences_over_20_words_share`, `sentences_with_passive_share` (a rough pattern, so call it a signal), `long_words_share`.
- *Assumptions noise:* `assumptions`, `per_10_lessons`, `words_avg`, `repeated_share`, `with_source_citation_share`, `assumptions_anchored_share` (higher; the share about an item of the map, not the course), and `by_kind` and `by_target` for the app. A large count with a low repeated share is volume, not duplication. Read ten items and say which kind it is.

**4. Open questions.** A numbered section, and the only place for them. Include what you could not judge (and why), each assumption that changes a verdict, and each decision the user must make. For each decision, give the options with one pro and one con, and your recommendation. Write `None` if there are no open questions.

**5. Report.** Then give the `CLAUDE.md` task report. In "Assumptions and open questions", write `See Open questions.` Do not repeat them.

## Judging

- **Be honest, not loyal.** Inflating the app hides the work. Inflating the reference sends the user after the wrong gap. Call out a reference weakness even if its numbers look complete, such as one standards list copied to every row.
- **Volume is not quality.** More words, codes, or entries count only if they are specific and correct. Check a sample before you credit either side.
- **Compare like with like.** If the week counts or row counts differ, find the cause (breaks, exam weeks, placeholder rows) before you call it a gap.
- **Smaller models fail in known ways:** they drop constraints in long outputs, repeat text, invent page numbers and codes, skip sections, and lose consistency across blocks. Prefer fixes that take load off the model: split a stage, shrink the schema, fill a field in code, add one gold example, run a validator with a repair call, or review one block at a time.
- **Spend once.** The only spend is the one `--generate` run in option 1. Do not call the OpenAI API in any other way, start the app server, or generate a second map without asking.
