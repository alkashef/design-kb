---
name: write-tests
description: Write the failing tests of one milestone in docs/plan.md from the spec's requirements and acceptance criteria and the design's interfaces, before the code exists and without reading it. Use as the first session of a milestone, or when the user asks to write the tests for a milestone. Do not use to write or fix application code, or to make a failing test pass.
---

# Write Tests

Write the tests that prove one milestone, from what the app must do, not from how it is built.
Another session builds the code afterwards and may not change these tests. Write tests only.

## Read only what the tests come from

- Read `CLAUDE.md`, `docs/workflow.md`, and the milestone's block in `docs/plan.md`.
- Read the rows of `docs/specs.md` that the block cites in **Refs**, the parts of the data model
  (section 2) that they use, and the acceptance criteria (`AC-NN`) with their examples (section 6).
- Read in `docs/design.md`: the test policy, the interfaces of the modules in **Owner** (routes,
  request and response fields, stored records, public functions), and the decisions in **Refs**.
- Read the test harness that the design names: the shared fixtures and helpers under `tests/`, and
  the fake embedding client. Read existing tests only to reuse their fixtures.
- Do not read the code in `src/` (`*.py`, `*.js`, `*.html`, `*.css`). The tests must come from the
  spec and the design, so that they catch code that drifts from them. If a test needs an interface the design does not name, that is a gap in
  the design. In chat, ask. In a milestone run, choose the most conservative name, use it, and
  report it as a `DECISION:` line (`docs/workflow.md`, Rules).

## Write the tests

1. Write one test for each name under **Tests first**, at the level the block gives it:
   - `unit:` a pure rule module, through its public functions.
   - `route:` a route, through the FastAPI test client of the test harness. A route answers with a
     page or a part of a page (`docs/design.md`, D-20).
   - `browser:` the page, through the browser test tool that the design names, against a server
     that a fixture starts on 127.0.0.1 with the fake embedding client.
2. Each test checks one behavior and asserts the result its requirement or example names: what the
   server answers, what is stored, or what the page shows. Do not assert private functions, log lines, or
   the order of calls.
3. Cover the success case of the requirement, and the failure or boundary case when the spec states
   one (a row of Type X is one).
4. Use invented data. No test calls the embedding model in Ollama, a network service, or the user's
   data. A test keeps its vector store in a temporary folder. Fix the clock and any random value, so
   the test gives the same result on every run.
5. Do not change an existing test, unless its requirement changed in `specs.md`. Then name the test
   and the spec change in the report.

## Run them

1. Run the new tests. Each must fail because the behavior is missing: a 404, a missing module named
   in **Owner**, a wrong value. A syntax error, a broken fixture, or a wrong import path of the test
   itself is not a valid failure: fix the test until it fails for the right reason.
2. Run the whole suite. Every older test must still pass.

## Finish

Do not commit: the pre-commit hook refuses failing tests. Leave the files for the build session.
Report, one line each: the test, the spec ID it checks, and how it fails now. Then each spec ID in
**Refs** without a test, and why (`Manual: <spec ID>`). Then the `DECISION:` lines.
