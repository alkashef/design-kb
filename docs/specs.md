# Software Requirements Specification: design-kb

Version 0.4 · 2026-11-20 · Status: Approved

## 1. Introduction

### 1.1 Purpose
This document states the requirements for `design-kb`. Design choices are in `design.md`.

### 1.2 Scope
`design-kb` is a knowledge base for an integrated circuit (IC) design team. It records who has experience in which skills. Users search it to find the right experience.

This is a proof of concept (PoC). It proves the idea. It is not a full product. It also teaches vector stores.

### 1.3 Glossary
| Term | Meaning |
|------|---------|
| Assignment | The work of one engineer on one leaf of one project. |
| Aware | Level 1. General knowledge from coursework or textbooks, with no project work in the leaf. |
| Career level | The engineer's seniority grade, such as junior or senior. |
| EARS | Easy Approach to Requirements Syntax. A set of sentence templates for requirements. |
| Embedding | A list of numbers that represents the meaning of a text. Texts with similar meaning have similar embeddings. |
| Expert | Level 5. Set manually on any leaf. |
| IC | Integrated circuit. |
| Lead | Participation value. The engineer led the design work on a leaf in a project. Also the name of level 3. |
| Leaf | A node with no children. Levels and assignments attach to leaves. |
| Level | The experience of one engineer in one leaf, on a scale of 1 to 5 (section 2.5). |
| Member | Participation value. The engineer worked on a leaf in a project but did not lead it. |
| Node | One item in the skill tree, such as "Circuit design", "PLL" or "VCO". |
| PoC | Proof of concept. A demo that proves an idea. It is not a full product. |
| Process technology | The chip manufacturing process of a project, such as "TSMC 7nm". |
| Seed data | The fake data that the demo loads at the start. |
| Semantic search | Search that matches meaning, not keywords. |
| Skill gap | A skill the engineer lacks or needs to build. Free text, entered manually. |
| Skill tree | The hierarchy of skills that the user defines. It has any number of levels. |
| Vector store | A database that stores embeddings and finds the ones nearest to a query embedding. |

### 1.4 Users
One user type. The user has full access. There is no login (see NFR-02).

## 2. Data Model

### 2.1 Engineer
| Attribute | Notes |
|-----------|-------|
| Engineer ID | Unique. |
| Engineer name | |
| Job title | |
| Career level | |
| Team/group | |
| Skill gaps | Free text. Entered manually. |

### 2.2 Skill tree
- The user defines the skill tree (FR-30).
- A node has one parent, except top-level nodes. A node has any number of children.
- The tree has no fixed depth. Branches may differ in depth.
- Levels and assignments attach to leaves.

| Node attribute | Notes |
|----------------|-------|
| Name | Such as "CDR". |
| Description | Optional free text, such as "Clock and data recovery". |

### 2.3 Project
| Attribute | Notes |
|-----------|-------|
| Project name | |
| Description | Short text. |
| Year | |
| Process technology | One name, such as "TSMC 7nm". An engineer's process experience comes from the projects they worked on. |

### 2.4 Assignment (engineer on a project)
| Attribute | Notes |
|-----------|-------|
| Engineer | |
| Project | |
| Leaf | The one leaf the engineer worked on. An engineer who worked on 2 leaves in a project has 2 assignments. |
| Participation | Lead or member of the design work on that leaf. |
| Assignment description | Free text. |

### 2.5 Skill level
The level is per engineer per leaf.

| Level | Name | Source | Default rule |
|-------|------|--------|--------------|
| 1 | Aware | Manual flag | General knowledge from coursework or textbooks. Applies only when the engineer has no assignment in the leaf. |
| 2 | Hands-on | Computed | Lead in 0 projects, member in 1 or more. |
| 3 | Lead | Computed | Lead in 1 to 2 projects. |
| 4 | Senior lead | Computed | Lead in 3 or more projects. |
| 5 | Expert | Manual flag | Set freely on any leaf. Overrides the computed level. |

## 3. Functional Requirements

Requirements use the EARS (Easy Approach to Requirements Syntax) templates. The Type column shows the template: U = ubiquitous, E = event-driven (When), S = state-driven (While), O = optional feature (Where), X = unwanted behavior (If, then).

### 3.1 Search
The system has two search modes. Experience search looks for people with the experience in the query. Gap search looks for people with the skill gap in the query. Both return a ranked list of engineers.

| ID | Type | Requirement |
|----|------|-------------|
| FR-01 | E | When the user submits a free-text query in experience search, the system shall return engineers ranked by semantic match between the query and their assignments. |
| FR-02 | U | The system shall match a query to engineers by meaning, not by keywords. |
| FR-03 | U | The system shall offer these optional filters: team, career level, and one leaf with a minimum level for that leaf. The Aware and Expert flags count as levels 1 and 5 in this filter. The filters apply to both search modes. |
| FR-04 | S | While one or more filters are set, the system shall rank only the engineers that meet all filters. |
| FR-05 | U | The system shall show each search result with name, job title, team and a short reason for the match. In experience search, the result shall also show the leaves of the engineer's best matching assignments: at most 3 leaves, best first, each leaf one time. |
| FR-06 | E | When the user submits a free-text query in gap search, the system shall return engineers ranked by semantic match between the query and their skill gaps. |
| FR-07 | E | When the user applies one or more filters and enters no query text, the system shall list all engineers that meet the filters. |

### 3.2 Views
| ID | Type | Requirement |
|----|------|-------------|
| FR-10 | E | When the user opens an engineer, the system shall show a profile page for that engineer. |
| FR-11 | U | The profile page shall give a 360 view: all engineer attributes, the level for every leaf, and each project with its assignment details. |
| FR-12 | E | When the user selects a leaf, the system shall list all engineers with a level in that leaf, sorted by level, highest first. |
| FR-13 | E | When the user selects a node, the system shall list all engineers with a level in any leaf under that node, with their level in each leaf. |

### 3.3 Data entry
| ID | Type | Requirement |
|----|------|-------------|
| FR-20 | U | The system shall allow the user to create and edit engineers. |
| FR-21 | U | The system shall allow the user to create and edit projects. |
| FR-22 | U | The system shall allow the user to create and edit assignments. |
| FR-23 | U | The system shall allow the user to set the Aware flag and the Expert flag on a leaf for an engineer. |
| FR-24 | X | If the user sets the Aware flag on a leaf where the engineer has an assignment, then the system shall reject the change and show a message. |
| FR-25 | U | The system shall compute levels 2, 3 and 4 from assignments: an engineer has, in a leaf, the highest of these levels whose lead range and member range (FR-31) both contain the engineer's number of lead projects and number of member projects in that leaf. |
| FR-26 | X | If the user tries to enter level 2, 3 or 4 directly, then the system shall not accept the entry. |
| FR-27 | S | While the Expert flag is set on a leaf, the system shall show level 5 for that leaf, whatever the computed level. |
| FR-28 | U | The system shall allow the user to delete engineers, projects and assignments. |
| FR-29 | E | When the user deletes an engineer or a project, the system shall also delete the assignments and the flags that refer to it. |
| FR-40 | U | The system shall offer only leaves when the user selects the leaf of an assignment or of a flag. |
| FR-41 | X | If the user enters an assignment or a flag on a node that has children, then the system shall reject the entry and show a message. |
| FR-42 | X | If the user enters an assignment for an engineer, a project and a leaf that already have an assignment, then the system shall reject the entry and show a message. |

### 3.4 Settings
| ID | Type | Requirement |
|----|------|-------------|
| FR-30 | U | The system shall provide an outline editor (an indented list with add, rename, describe and delete actions) for the user to define the skill tree, including the optional description of each node. |
| FR-31 | U | The system shall allow the user to set, for each computed level (2, 3 and 4), a range of lead projects and a range of member projects. A range has a "from" value and a "to" value. An empty "to" value means no upper limit. |
| FR-32 | U | The system shall use the default thresholds in section 2.5 until the user changes them. |
| FR-33 | X | If the user deletes a node that has children, or a leaf that has assignments or flags, then the system shall refuse the deletion and show a message. |
| FR-34 | X | If the user adds a child to a leaf that has assignments or flags, then the system shall refuse the change and show a message. |
| FR-35 | X | If the user enters a threshold that is not a whole number of 0 or more, or a "from" value that is greater than its "to" value, then the system shall reject the change and show a message. |
| FR-36 | E | When the user resets the thresholds, the system shall restore the default thresholds in section 2.5. |

## 4. Non-Functional Requirements
| ID | Type | Requirement |
|----|------|-------------|
| NFR-01 | U | The system shall provide a web UI for desktop browsers only. |
| NFR-02 | U | The system shall not require login or roles. One local user shall have full access. |
| NFR-03 | U | The system shall run on one machine. |
| NFR-04 | U | The system shall include fake seed data: 40 engineers, 15 projects, a skill tree with 6 top-level nodes and about 30 leaves. |
| NFR-05 | U | The seed data shall give skill levels that match the assignments. |
| NFR-06 | U | The system shall contain no real engineer data. |

## 5. Constraints
- The system stores data in a vector store and uses embeddings (see `design.md`).
- The data is entered manually.

## 6. Acceptance Criteria
| ID | Type | Criterion |
|----|------|-----------|
| AC-01 | E | When the demo runs the 3 example searches below, the system shall show the expected person in the top 5 results of each search. |

The PoC passes when AC-01 is met.

### Example searches for AC-01
| # | Query | Expected person |
|---|-------|-----------------|
| 1 | Who has led a PLL design in a 7nm process? | A seed engineer with level 3 or 4 in PLL who worked on a 7nm project. |
| 2 | Who has experience recovering a clock from a serial data stream? | A seed engineer with level 2 or higher in the CDR leaf. The query does not contain the word "CDR". |
| 3 | Query: low-noise amplifier design. Filters: team = Analog, career level = Senior. | A senior seed engineer in the Analog team with a level in a low-noise amplifier leaf. |

## 7. Out of Scope
- Staffing engineers into projects.
- Target role profiles and computed skill gaps.
- A team skill-gap report.
- Login, roles and access control.
- Mobile support.
- Matrix view (any axes, any value). Dropped for the PoC.

## 8. Assumptions
Source: **Owner** means the product owner stated it. **Inferred** means Claude derived it. The product owner has not confirmed it.

| ID | Assumption | Source |
|----|------------|--------|
| A-01 | A project has one process technology. | Owner |
| A-02 | An engineer's process experience comes only from the projects they worked on. | Owner |
| A-03 | One assignment covers one leaf. | Owner |
| A-04 | Each node in the skill tree has one parent. | Owner |
| A-05 | Only leaves have levels. Parent nodes have none. | Owner |
| A-06 | Skill gaps are free text. They are not linked to the skill tree. | Owner |
| A-07 | An engineer has one job title, one career level and one team. | Inferred |
| A-08 | An engineer has at most one assignment for each project and leaf. So the number of assignments equals the number of projects in the level rules. | Inferred |
| A-09 | The data is small (about 40 engineers). The PoC has no performance target. | Inferred |
| A-10 | The system keeps no change history or audit trail. | Inferred |

## 9. Open Items
| ID | Item | Proposed default |
|----|------|------------------|
