# AGENTS.md

## Purpose

This repository is designed for AI-assisted development.

Agents must prioritize:

- correctness
- clarity
- minimal scope changes
- testability
- maintainability
- optimization for AI-agent workflows

---

## Required Reading Before Any Task

Always read:

1. `docs/ARCHITECTURE.md`
2. relevant feature in `product/features/`
3. relevant task in `project/backlog/`
4. `context/test-strategy.md` (if exists)

---

## Core Rules

- Do not implement anything outside task scope.
- Do not refactor unrelated code.
- Do not invent requirements not present in task or feature.
- Prefer minimal, safe changes over large rewrites.
- Keep module boundaries defined in `docs/ARCHITECTURE.md`.

---

## Agent Optimization Rules

This repository is optimized for AI-assisted and agent-based development.

Agents should minimize unnecessary future context consumption.

Rules:

- Write documentation continuously during development.
- Document architecture decisions, module responsibilities, important flows, and non-obvious behavior.
- Prefer creating or updating local documentation near the code instead of relying on future code re-reading.
- Keep documentation concise, structured, and easy for another agent to scan quickly.
- Add examples where they significantly reduce future reasoning cost.
- Maintain clear public APIs and module boundaries.

When possible:

- Prefer mature third-party libraries over custom implementations.
- Avoid reinventing standard infrastructure or utility logic.
- Minimize total code volume while preserving clarity and maintainability.
- Choose solutions that reduce future cognitive load for agents.

Goal:

- reduce token usage
- reduce repeated repository scanning
- reduce duplicated reasoning
- improve implementation consistency between agents

---

## Code Quality

- Follow clean, explicit, and maintainable style.
- Prefer clarity over cleverness.
- Use type hints where reasonable.
- Every module, class, and function must include a docstring.
- Keep functions small and single-purpose.
- Avoid implicit behavior and magic values.

---

## Documentation Standards

Documentation is mandatory.

Agents should document:

- module responsibilities
- architecture boundaries
- public APIs
- important data flows
- assumptions
- limitations
- integration points
- non-obvious implementation details

Preferred documentation locations:

- module-level docstrings
- `docs/`
- ADRs
- README files near complex modules

Documentation should optimize future agent understanding and reduce the need for full codebase traversal.

---

## Dependencies

- Use Poetry.
- Do not add dependencies unless clearly justified.
- Prefer standard library when possible.
- However, if a stable and widely adopted third-party library significantly reduces custom code, prefer the library solution.
- Favor libraries that improve maintainability and reduce implementation complexity.

---

## Language

This project is **English-only**:

- code
- comments
- docstrings
- commits
- documentation
- agent communication

---

## Task Workflow

Tasks are stored in `project/backlog/`.

When implementing a task:

1. Read the task and related feature.
2. Implement only what is defined in **Scope**.
3. After completion:
   - update task status to `done`
   - move file to `project/done/`

Do not modify unrelated tasks.

Agents should follow `docs/TASK_SEQUENCE.md` to determine correct execution order.

## Task Sequence Consistency

When tasks in `project/backlog/` change, update `docs/TASK_SEQUENCE.md`.

Trigger conditions:

- a task is added
- a task is removed
- a task identifier changes

Rules:

- keep `Order` aligned with backlog
- update `Dependencies` if needed
- do not leave references to non-existing tasks

---

## Testing

Run tests via:

```bash
poetry run pytest
```

Rules:

- Add or update tests for any behavior change.
- Tests must be deterministic and fast.
- Test behavior, not implementation details.

---

## Versioning & Change Management (MANDATORY)

After every code change:

### 1. Commit

Use Conventional Commits:

```bash
type(scope): short description
```

Examples:

- `feat(api): add PDF text extraction`
- `fix(cli): handle empty input`
- `refactor(core): simplify pipeline`

---

### 2. Version bump

Follow Semantic Versioning:

- MAJOR → breaking changes
- MINOR → new features
- PATCH → fixes/refactors

Update version in `pyproject.toml`.

---

### 3. Changelog

Update `CHANGELOG.md`:

- describe change clearly
- group under: Added / Changed / Fixed

---

## What NOT to Do

- Do not expand task scope.
- Do not refactor unrelated code.
- Do not skip tests.
- Do not skip version bump or changelog.
- Do not write vague commit messages.
- Do not introduce undocumented behavior.
- Do not create large custom utility layers when a stable library already solves the problem well.

---

## When in Doubt

- Ask or make the smallest safe assumption.
- Document assumptions explicitly.
- Prefer small, well-defined changes.

---

## Definition of Done

A task is done only if:

- implementation matches Scope
- all Done criteria in task are satisfied
- tests pass
- no unrelated code was modified
- version and changelog were updated
- relevant documentation was updated