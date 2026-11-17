# Design Choices

Design decisions for `design-kb`, a proof of concept (PoC). Requirements are in `specs.md`.

Status: **Decided** means the product owner chose it. **Proposed** means Claude derived it from a requirement. The product owner has not confirmed it.

## Decisions

Keep one current decision per topic. Never reuse or renumber a decision ID. Keep the row of a replaced decision with the Status `Superseded`.

| ID | Status | Decision | Reason |
|----|--------|----------|--------|
| D-NN | <Decided, Proposed or Superseded> | <chosen approach> | <reason, requirement IDs, alternatives and validation when they affect the choice> |

## Open Design Questions

| ID | Question |
|----|----------|
| DQ-NN | <question that the design cannot settle, and who decides it> |

Write "None." below the table when no question is open.

<The sections below are optional. Add one when the design first needs it, and cite the decisions that own its content. Remove the ones that are not used.>

## Architecture

| Layer or module | Responsibility and owned state | Allowed dependencies | References |
|-----------------|--------------------------------|----------------------|------------|

## Directory structure

Create a folder only when it is listed here. Keep the layout consistent with the modules.

| Path | Purpose and owner |
|------|-------------------|

## Settings

| Setting | Default | Meaning and references |
|---------|---------|------------------------|

## Data storage

<Define the tables of the vector store, the text of each vector, identities, and links between records. The data model is in `specs.md`, section 2: cite it and do not copy it.>

## Interfaces

<Define the routes, request and response fields, stored records, and public functions that a test needs. Cite the requirement IDs.>

## Test policy

<State which requirements and modules get automated tests, the test level of each requirement (unit, route or browser), the test harness, and the fake for each external system.>
