# Software Requirements Specification: design-kb

Version <n.n> · <date> · Status: Draft

## 1. Introduction

### 1.1 Purpose
State what this document holds. Design choices are in `design.md`.

### 1.2 Scope
Record the business problem, the users, and the limits of the proof of concept.

### 1.3 Glossary
| Term | Meaning |
|------|---------|

Define each domain term one time. Keep the terms in alphabetical order.

### 1.4 Users
Define the user types and their access.

## 2. Data Model

One subsection for each entity, with a table of its attributes.

| Attribute | Notes |
|-----------|-------|

## 3. Functional Requirements

Requirements use the EARS templates. The Type column shows the template: U = ubiquitous, E = event-driven (When), S = state-driven (While), O = optional feature (Where), X = unwanted behavior (If, then).

One subsection for each area, with its own block of ten IDs.

| ID | Type | Requirement |
|----|------|-------------|
| FR-NN | <U, E, S, O or X> | <one required behavior> |

## 4. Non-Functional Requirements
| ID | Type | Requirement |
|----|------|-------------|
| NFR-NN | <U, E, S, O or X> | <one required behavior, with measurable limits> |

Keep unknown limits in the open items. Do not invent values.

## 5. Constraints
List the binding constraints. Cite `design.md` for a design choice.

## 6. Acceptance Criteria
| ID | Type | Criterion |
|----|------|-----------|
| AC-NN | <U, E, S, O or X> | <what the demo must show> |

State which criteria the proof of concept must meet to pass.

### Examples for AC-NN
| # | Situation and input | Expected result |
|---|---------------------|-----------------|

Use invented data. Cite the requirement that an example checks.

## 7. Out of Scope
List what the proof of concept excludes.

## 8. Assumptions
Source: **Owner** means the product owner stated it. **Inferred** means Claude derived it. The product owner has not confirmed it.

| ID | Assumption | Source |
|----|------------|--------|
| A-NN | <assumption> | <Owner or Inferred> |

## 9. Open Items
| ID | Item | Proposed default |
|----|------|------------------|
| OI-NN | <open question> | <the answer that applies until the product owner decides> |

Delete the row of an item when the product owner closes it. Do not prefill approval or treat silence as consent.
