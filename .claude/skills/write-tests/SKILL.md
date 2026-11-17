---
name: write-tests
description: Write the failing tests of one milestone in docs/plan.md from the spec's acceptance examples and the design's interfaces, before the code exists and without reading it. Use as the first session of a milestone, or when the user asks to write the tests for a milestone. Do not use to write or fix application code, or to make a failing test pass.
---

# Write Tests

Write the tests that prove one milestone, from what the app must do, not from how it is built.
Another session builds the code afterwards and may not change these tests. Write tests only.

## Read only what the tests come from

- Read `CLAUDE.md`, `docs/workflow.md`, and the milestone's block in `docs/plan.md`.
- Read the spec rows that the block cites in **Refs**, and the acceptance examples (`EX-NNN`) they link.
- Read in `docs/design.md`: the test policy (DEC-013), the interfaces of the modules in **Owner**
  (routes, request and response fields, saved files, public functions), and the decisions in **Refs**.
- Read the test harness: `tests/app_factory.py`, every `conftest.py` under `tests/`, and the fake
  LLM client. Read existing tests only to reuse their fixtures.
- Read the JSON schemas of the model's output in `src/backend/` when a test needs the fake LLM
  client: they are an interface (`docs/design.md`, 2.5.5).
- Do not read the code in `src/` (`*.py`, `*.js`, `*.html`, `*.css`). The tests must come from the spec and the design, so that they catch code
  that drifts from them. If a test needs an interface the design does not name, that is a gap in
  the design. In chat, ask. In a milestone run, choose the most conservative name, use it, and
  report it as a `DECISION:` line (`docs/workflow.md`, Rules).

## Write the tests

1. Write one test for each name under **Tests first**, at the level the block gives it:
   - `unit:` a pure rule module, through its public functions.
   - `route:` the API, through the FastAPI test client from `tests/app_factory.py`.
   - `browser:` the page, through Playwright, against a server that a fixture starts on 127.0.0.1
     with the fake LLM client.
2. Each test checks one behavior and asserts the result its example names: what the server
   answers, what is saved, or what the page shows. Do not assert private functions, log lines, or
   the order of calls.
3. Cover the success case of the example, and its failure or boundary case when the spec row has one.
4. Use invented data. No test calls OpenAI, another network service, or the user's data. Fix the
   clock and any random value, so the test gives the same result on every run.
5. Do not change an existing test, unless its requirement changed in `spec.md`. Then name the test
   and the spec change in the report.

## Run them

1. Run the new tests. Each must fail because the behavior is missing: a 404, a missing module named
   in **Owner**, a wrong value. A syntax error, a broken fixture, or a wrong import path of the test
   itself is not a valid failure: fix the test until it fails for the right reason.
2. Run the whole suite. Every older test must still pass.

## Finish

Do not commit: the pre-commit hook refuses failing tests. Leave the files for the build session.
Report, one line each: the test, the spec ID and example it checks, and how it fails now. Then each
spec ID in **Refs** without a test, and why (`Manual: EX-nnn`). Then the `DECISION:` lines.
