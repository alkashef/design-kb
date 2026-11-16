# Software Requirements Specification: design-kb

Version 0.1 · 2026-11-16 · Status: Draft

## 1. Introduction

### 1.1 Purpose
This document states the requirements for `design-kb`. Design choices are in `design.md`.

### 1.2 Scope
`design-kb` is a knowledge base for an integrated circuit (IC) design team. It records who has experience in which skills. Users search it to find the right experience.

This is a proof of concept (PoC). It proves the idea. It is not a full product. It also teaches vector stores.

### 1.3 Definitions
| Term | Meaning |
|------|---------|
| Skill category | A group of skills, such as circuit design, system design, coding or leadership. |
| Skill block | A skill inside a category, such as PLL or ADC. |
| Assignment | The work of one employee on one project. |
| Semantic search | Search that matches meaning, not keywords. |

### 1.4 Users
One user type. The user has full access. There is no login (see NFR-02).

## 2. Data Model

### 2.1 Employee
| Attribute | Notes |
|-----------|-------|
| Employee ID | Unique. |
| Employee name | |
| Job title | |
| Career level | |
| Team/group | |
| Process technologies | List of process names, such as "TSMC 7nm". No level or count. |
| Skill gaps | Free text. Entered manually. |

### 2.2 Skill category and skill block
- A skill block belongs to one skill category.
- The user manages both in Settings (FR-30).

### 2.3 Project
| Attribute | Notes |
|-----------|-------|
| Project name | |
| Description | Short text. |
| Year | |

### 2.4 Assignment (employee on a project)
| Attribute | Notes |
|-----------|-------|
| Employee | |
| Project | |
| Skill block | The block the employee worked on. |
| Participation | Lead or member of the block design. |
| Role description | Free text. |

### 2.5 Skill level
The level is per employee per skill block.

| Level | Name | Source | Default rule |
|-------|------|--------|--------------|
| 1 | Aware | Manual flag | General knowledge from coursework or textbooks. Applies only when the employee has no assignment in the block. |
| 2 | Hands-on | Computed | Lead in 0 projects, member in 1 or more. |
| 3 | Lead | Computed | Lead in 1 to 2 projects. |
| 4 | Senior lead | Computed | Lead in 3 or more projects. |
| 5 | Expert | Manual flag | Set freely on any block. Overrides the computed level. |

## 3. Functional Requirements

### 3.1 Search
| ID | Requirement |
|----|-------------|
| FR-01 | The system shall accept a free-text query. |
| FR-02 | The system shall match the query to employees by meaning (semantic search), not by keywords. |
| FR-03 | The system shall allow optional filters: team, career level and minimum skill level. |
| FR-04 | The system shall apply the filters first, then rank the remaining employees by semantic match. |
| FR-05 | The system shall show a ranked list. Each result shall show name, job title, team, top matching skills and a short reason for the match. |

### 3.2 Profile
| ID | Requirement |
|----|-------------|
| FR-10 | The system shall show a profile page for one employee. |
| FR-11 | The profile shall show all employee attributes, the skill level for each block, and each project with its assignment details. |

### 3.3 Data entry
| ID | Requirement |
|----|-------------|
| FR-20 | The user shall create and edit employees. |
| FR-21 | The user shall create and edit projects. |
| FR-22 | The user shall create and edit assignments. |
| FR-23 | The user shall set the Aware flag and the Expert flag on a skill block for an employee. |
| FR-24 | The system shall allow the Aware flag only when the employee has no assignment in that block. |
| FR-25 | The system shall compute levels 2, 3 and 4 from assignments. The user shall not enter them. |

### 3.4 Settings
| ID | Requirement |
|----|-------------|
| FR-30 | The user shall create, rename and delete skill categories and skill blocks. |
| FR-31 | The user shall set the number of lead and member assignments required for each computed level (2, 3, 4). |
| FR-32 | The default thresholds shall be those in section 2.5. |

## 4. Non-Functional Requirements
| ID | Requirement |
|----|-------------|
| NFR-01 | The user interface shall be a web UI for desktop browsers only. Mobile is not supported. |
| NFR-02 | The system shall have no login and no roles. One local user has full access. |
| NFR-03 | The system shall run on one machine. |
| NFR-04 | The system shall include fake seed data: 40 employees, 15 projects, 6 skill categories and about 30 skill blocks. |
| NFR-05 | The seed data shall give levels that match the assignments. |
| NFR-06 | The seed data shall have no real employee data. |

## 5. Constraints
- The system stores data in a vector store and uses embeddings (see `design.md`).
- The data is entered manually.

## 6. Out of Scope
- Staffing engineers into projects.
- Target role profiles and computed skill gaps.
- A team skill-gap report.
- Login, roles and access control.
- Mobile support.
- Success criteria for the PoC. The product owner chose not to define them. Without them, the team cannot show that the PoC worked.

## 7. Open Items
| ID | Item | Proposed default |
|----|------|------------------|
| OI-01 | One assignment may cover one block or several blocks. | One or more blocks. |
| OI-02 | The "minimum skill level" filter needs a skill block to apply to. | The user picks a block, then a minimum level. |
| OI-03 | The filter set (team, career level, minimum skill level) was inferred, not confirmed. | As in FR-03. |
| OI-04 | Delete rules for employees, projects and assignments are not defined. | Allow delete. |
