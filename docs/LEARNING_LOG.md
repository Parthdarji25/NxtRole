# Learning log

One entry per task: what was built, the key idea in plain words, and one interview question with a short answer.
Newest entry last. Read it before an interview: it is your own record of why NxtRole is built the way it is.

---

## Entry 1 · Phase 0 · What a PRD is (and why we wrote one before any code)

**What was built.** `docs/PRD.md`: the Product Requirements Document for NxtRole. It says who the product is for, which problems it solves,
the journeys a person follows, 220 numbered requirements (FR-001 to FR-220), how well it must work (non-functional requirements), what is in
and out of the first release, how success is measured, and what could go wrong. No code was written.

**Key concept: a PRD.** A PRD is a written agreement about *what* to build and *why*, before deciding *how*. It is the document that every later
phase checks its work against. If the PRD is vague, every phase argues about what "done" means. If it is precise, "done" is a test that passes.

**1. What are we building?** A document of requirements, journeys and decisions.
**2. Why do we need it?** Code is expensive to change. A wrong idea costs a sentence to fix in a document and weeks to fix in code. The PRD also
catches contradictions early: in Phase 0 we found 11 more mock conflicts than the roadmap listed (for example mocks that read LinkedIn, which
our own rule forbids).
**3. Which technology, and why?** Plain Markdown (readable anywhere, tracked by git like code) and Mermaid for small diagrams. No special tool.
**4. How does it work?** Each requirement has an ID, a priority (MVP or Later), a screen or background job that delivers it, and where it helps,
a Given / When / Then test. A traceability table proves every screen has requirements and every requirement has a screen or job.
**5. How does it connect to the rest of NxtRole?** Phase 1 turns it into architecture and a database schema. Phases 2 to 16 build against it.
Phase 13 uses it to design the test suite. The decisions behind it live in `docs/DECISIONS.md`.
**6. What should I understand as a founder?** You decide *what and why*; engineering decides *how*. A decision you make once, in writing, saves
you from re-deciding it in every phase. "MVP" is about scope, not quality: the first release is small but must be correct.

**Four terms from this task**
- *User journey*: the steps one person takes to reach a goal, naming each screen they use (for example "morning: open Today, open a job, apply").
- *MVP scope*: the smallest set of features that makes the product genuinely useful. Everything else is "Later".
- *Non-functional requirement*: how well it must work (speed, security, privacy, accessibility), not what it does.
- *Traceability*: a table showing that each requirement links to a screen or job, so nothing is promised without being built, and nothing is built without a reason.

**Interview question.** "How do you decide what goes into the first release of a product, and how do you stop scope from growing?"
**Short answer.** Start from the user's main journeys and the smallest set of features that completes them. Write every feature as a testable
requirement with a priority. Anything that is not on a main journey becomes "Later" and is recorded as a decision with its reason (we did this for
jobs abroad, voice, `.docx` export and Telegram). Scope changes only through a new recorded decision, never silently.

---

## Entry 2 · Phase 0 · Decision records

**What was built.** `docs/DECISIONS.md`: 23 short records (D-001 to D-023). Each says the date, the decision, why, and what else was considered.

**Key concept: a decision record** (also called an architecture decision record, or ADR). It captures *why* a choice was made at the time. Code
shows what the system does; it cannot show what was rejected or what constraint forced the choice. Six months later, "why did we not use Google
sign-in?" has a one-line answer instead of a debate.

**Why it matters for you.** A decision is never edited to change its meaning. If you change your mind, a new record says which one it replaces.
That keeps the history honest. Two examples from this phase: D-004 (cards may be auto-moved by code rules for clear rejections or interview invites,
with undo) is a deliberate, narrow exception to "AI suggests, I approve"; D-023 records that you chose the full Google Calendar connection even
though a smaller option was recommended, with the extra security work written down.

**Interview question.** "Tell me about a technical decision you made and what you gave up."
**Short answer.** Name the decision (for example email and password with our own tokens instead of Google sign-in), the constraint (free hosting, no
email service, wanting full control and learning), what was given up (no "forgot password by email", so a recovery method must be designed), and
how it was recorded so the trade-off stays visible.


---

## Entry 3 · Phase 1 · Architecture

**What was built.** `docs/ARCHITECTURE.md` and `docs/TECH_STACK.md`: how the pieces fit (web app, API, worker, database, AI gateway), six diagrams, the folder layout, and the checked stack with real versions.

**Key concept: architecture.** The big shape of the system: which parts exist, what each is responsible for, and how they talk. It is the answer to "where does this code go?" before there is any code.

1. **What are we building?** A plan for two programs (`web/`, `api/`) and a background worker sharing one PostgreSQL database.
2. **Why?** Free hosting has hard limits (a request body of 4.5 MB, short requests, a monthly allowance of scheduler minutes). Finding them now cost one document; finding them in Phase 8 would have cost a rewrite. Phase 1 also found that LiteLLM was compromised twice this year, Cerebras stopped being free, and arq stopped being developed, so those three were replaced.
3. **Which technology and why?** FastAPI for the API (types check every request), Next.js for screens, PostgreSQL for everything (data, search and AI memory in one place), a small queue table instead of an extra library.
4. **How does it work?** Layers: router (HTTP) → service (rules) → repository (SQL). Slow work becomes a row in a queue table, so a closed tab loses nothing.
5. **How does it connect?** Every later phase builds one slice of this plan; the traceability table proves each requirement has a place in it.
6. **As a founder:** an architecture decision is cheap to change on paper and expensive in code. The "what changed and why" table in `docs/TECH_STACK.md` shows how verification protects you.

**Interview question.** "Why did you not use library X?" **Answer.** For the AI layer I verified the dependency first and found it had two compromised releases in one year, so I wrote a thin gateway (about 150 lines) on the provider's official client. It also gave me one place for redaction, retries and budgets.

---

## Entry 4 · Phase 1 · Database schema and migrations

**What was built.** `docs/DATABASE_SCHEMA.md`: 50 tables, entity diagrams, indexes, retention rules, row-level security.

**Key concepts.** A **schema** is the list of tables and columns the database holds and the rules between them (this column is required, this one points at another table). A **migration** is a small versioned file that changes the schema one step (add a column). Alembic runs them in order, so every database, yours or production, ends up identical, and a change can be reviewed like code.

**Why two sides (global and per-user).** A job posting is the same fact for everyone, so it is stored once; what you think of it (score, saved, notes) is yours, with a `user_id`. That keeps personal data in tables that can be exported or deleted in one step.

**Row-level security** is a rule inside PostgreSQL: "this connection may see only rows where `user_id` equals mine". Even if the code forgets a filter, another person's rows cannot leak.

**Expand then contract.** To rename a column safely: add the new one, write to both, move readers over, then drop the old one in a later migration.

**Interview question.** "How do you change a database schema with no downtime?" **Answer.** In small backward-compatible steps (expand, migrate, contract), each as a versioned migration tested on an empty database and on a copy of real data, with a backup taken first.

---

## Entry 5 · Phase 1 · The API contract

**What was built.** `docs/API_DOCUMENTATION.md`: conventions, 150 endpoints, 16 background jobs and commands, and a table that traces all 220 requirements to tables, endpoints, screens and phases.

**Key concept: an API.** A menu of requests one program can make to another. The web app never touches the database; it asks the API, which checks who you are, applies the rules and answers in a fixed shape. A **contract** written first means the screen and the server can be built independently and then tested against the same document.

**Ideas worth knowing:** one error shape everywhere; cursor pagination for long lists; an **idempotency key** so a double tap creates one record; a **version number** so two tabs cannot silently overwrite each other (the second gets a 409); **202 Accepted** for slow work with progress read from the database.

**Interview question.** "How do you make a POST safe to retry?" **Answer.** The client sends an `Idempotency-Key`; the server stores the first response under that key for a day and replays it for a repeat, and rejects the same key with a different body.

---

## Entry 6 · Phase 1 · Threat model

**What was built.** `docs/SECURITY.md`: assets, actors, trust boundaries, numbered threats with a control and a test for each, mapped to the OWASP lists.

**Key concept: a threat model.** A written list of who might attack, what they want, how, and what stops them, made before building so each control answers a named threat and each threat has a test. Method: name the asset, draw the trust boundary, list how it breaks (spoofing, tampering, leaking, denying, escalating), then decide the control.

**A token** is a small proof of identity the server hands out after sign-in. Ours: a 15-minute access token kept in memory, and a 7-day refresh token that is rotated on every use; if an old one is ever replayed, the whole family is revoked because that means it was stolen.

**New for AI apps:** text from job posts and emails can contain instructions aimed at the model (prompt injection). We treat all outside text as data, verify quotes in code, give models no tools that write, and allow only proposals the owner approves.

**Interview question.** "How do you protect an LLM agent from prompt injection?" **Answer.** Assume it will happen: separate instructions from untrusted data, validate output against a schema, verify claims in code, give the agent least-privilege tools with no direct write or send ability, and require human approval for any change.


---

## Entry 7 · Phase 2 · Docker and containers

**What was built.** `docker-compose.yml` runs PostgreSQL (with pgvector) and Redis on your laptop, using Docker Engine inside Ubuntu on WSL 2.

**Key concept: a container** is a sealed box holding one program and everything it needs, started from a ready-made **image**. **Docker** runs containers; **Compose** starts several from one file. Data lives in a **volume**, so stopping a container keeps your data (`down`), while `down -v` deletes it.

**Why not install PostgreSQL directly?** The same image runs on your laptop and in CI, one command starts both services, and removing them leaves Windows clean. Ports are bound to `127.0.0.1`, so only your computer can reach them.

**A lesson from this task.** We first planned Docker Desktop. Reading its requirements showed Windows 10 Home is not a listed edition, so the plan changed (D-041). Check requirements before you rely on a tool.

**Interview question.** "What is the difference between an image and a container?" **Answer.** An image is the read-only template; a container is a running instance of it, with its own writable layer. Volumes keep data beyond the container's life.

---

## Entry 8 · Phase 2 · Environment variables and configuration

**What was built.** `api/app/config.py`, three `.env.example` files, and `check-config`.

**Key concept: an environment variable** is a named value given to a program from outside its code, such as `DATABASE_URL`. The same code runs on your laptop and in production with different values, and secrets never enter git. A `.env` file is a convenient local list of them.

**How ours works.** One module reads every setting. If one is missing or wrong, the program stops with a message that names it and never prints its value. Passwords use a "secret" type, so printing the settings shows stars.

**Interview question.** "How do you handle secrets in a project?" **Answer.** Outside the code in environment variables or a secret store, templates with names only in git, `.env` ignored, a secret scanner before commits and in CI, redaction in logs, and rotation if one leaks.

---

## Entry 9 · Phase 2 · The API skeleton, health checks and migrations

**What was built.** A FastAPI app with one error shape, JSON logs with a request id, health routes, and the first Alembic migration.

**Key concepts.** A **migration** is a versioned file that changes the database one step; `0001` switches on the `vector` extension, and `downgrade` reverses it. A **liveness** check (`/health`) says the program runs; a **readiness** check (`/api/health/ready`) says it can reach what it needs, and returns **503** when it cannot. The app does not connect at start-up, so a slow database cannot cause a crash loop.

**A real bug we avoided.** The database driver cannot use Windows' default event loop (the engine that juggles many tasks at once), so `app/core/loop.py` picks the other one. Reading the library's code before writing ours found it.

**Interview question.** "Why separate liveness and readiness?" **Answer.** A platform restarts a program that is not alive, but should only stop sending it traffic when it is not ready. Restarting cannot fix a database that is down.

---

## Entry 10 · Phase 2 · Tests

**What was built.** 32 API tests (25 need nothing running, 7 use real PostgreSQL and Redis), 4 component tests and 2 browser tests.

**Key concepts.** A **unit** test checks a small piece; an **integration** test checks pieces together with the real database; an **end-to-end** test drives a real browser the way you would. A **fixture** is prepared setup a test asks for. Our integration tests empty their database, so they refuse to run unless its name ends in `_test`.

**Interview question.** "Why not mock the database in integration tests?" **Answer.** A mock only repeats your assumptions. Real constraints, migrations, drivers and timeouts are exactly where bugs hide.

---

## Entry 11 · Phase 2 · Linters, pre-commit and CI

**What was built.** Ruff and mypy for Python; ESLint, Prettier and TypeScript checks for the web; pre-commit hooks with a secret scanner; a GitHub Actions workflow and Dependabot.

**Key concepts.** A **linter** reads code without running it and flags likely mistakes; a **formatter** fixes layout; a **type checker** verifies that values are used as their declared types. A **pre-commit hook** runs checks before git saves a commit. **CI** (continuous integration) runs all checks on a clean machine after every push, so "works on my laptop" is not enough. Ours has not run yet because nothing is pushed.

**Supply chain.** Dependencies are locked to exact versions, new releases wait 7 days, and CI actions are pinned to a commit hash.

**Interview question.** "What do you put in a CI pipeline for a small project?" **Answer.** Install from the lockfile, lint, type check, tests against real services, build, a browser smoke test, a dependency audit and a secret scan, with least-privilege permissions.
