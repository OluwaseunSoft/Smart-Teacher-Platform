# Data Model

SQLAlchemy 2.0 declarative models live in `backend/app/models.py`. SQLite for the
MVP; types chosen to remain Postgres-compatible.

## Entities

### Student
Auto-created single MVP user.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| name | str | default "Student" |
| created_at | datetime | |

### Material
An uploaded source of study content.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| student_id | FK → Student | |
| title | str | |
| source_type | str | `pdf` \| `text` |
| filename | str? | original name |
| raw_text | Text | full extracted text |
| status | str | `uploaded` → `processing` → `ready` \| `failed` |
| error | Text? | failure reason |
| created_at / updated_at | datetime | |

### Chunk
A retrievable slice of a material; carries its embedding.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| material_id | FK → Material | |
| index | int | position in source |
| content | Text | chunk text |
| embedding | JSON | list[float], nullable |

### Concept
A teachable unit discovered by structuring.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| material_id | FK → Material | |
| parent_id | FK → Concept? | supports sub-concepts |
| title | str | |
| summary | Text | one-paragraph description |
| order_index | int | curriculum order |
| difficulty | str | `intro` \| `core` \| `advanced` |

### Lesson
Generated teaching content for a concept.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| material_id | FK → Material | |
| concept_id | FK → Concept | |
| title | str | |
| objectives | JSON | list[str] |
| content | Text | markdown |
| status | str | `pending` \| `ready` \| `failed` |
| created_at | datetime | |

### Question
A generated assessment item.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| lesson_id | FK → Lesson | |
| concept_id | FK → Concept | |
| type | str | `mcq` \| `short` |
| prompt | Text | |
| options | JSON? | list[str] for mcq |
| answer | Text | correct option/answer |
| explanation | Text | why |
| difficulty | int | 1 (easy) – 5 (hard) |

### Attempt
A student's answer to one question.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| student_id | FK → Student | |
| question_id | FK → Question | |
| response | Text | |
| is_correct | bool | |
| created_at | datetime | |

### Mastery
Rolling per-concept mastery for a student.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| student_id | FK → Student | |
| concept_id | FK → Concept | |
| score | float | 0.0 – 1.0 |
| attempts | int | |
| correct | int | |
| updated_at | datetime | |

Unique constraint on `(student_id, concept_id)`.

### StudySession
Tracks a student's position in a material.

| Field | Type | Notes |
|---|---|---|
| id | int PK | |
| student_id | FK → Student | |
| material_id | FK → Material | |
| current_concept_id | FK → Concept? | |
| status | str | `active` \| `completed` |
| created_at / updated_at | datetime | |

## Relationships

```
Student 1─* Material 1─* Chunk
Student 1─* Material 1─* Concept 1─* Lesson 1─* Question
Concept 1─* Concept (self, parent_id)
Student 1─* Attempt *─1 Question
Student 1─* Mastery *─1 Concept
Student 1─* StudySession *─1 Material
```

## Mastery update rule (MVP)

Per attempt, with an exponential moving average and a difficulty weight:

```
weight   = 0.6 + 0.1 * difficulty          # harder question moves more
observed = 1.0 if correct else 0.0
score    = (1 - alpha) * score + alpha * (weight * observed + (1 - weight) * 0.5)
alpha    = 0.35
```

Clamped to `[0, 1]`. This is deliberately simple and testable; a Bayesian
Knowledge Tracing model can replace `services/adaptive.py::update_mastery` later.
