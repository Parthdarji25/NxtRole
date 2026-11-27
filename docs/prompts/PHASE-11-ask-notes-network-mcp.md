# Phase 11 — Ask NxtRole, notes, network and MCP

> Paste this whole file into Claude Code, or type: `Read docs/prompts/PHASE-11-ask-notes-network-mcp.md and follow it.`
> Follow `CLAUDE.md`. No commits.

## 1. Phase name and objective
**Ask NxtRole, notes, network and MCP.** Let me chat with my own job-search data (answers with sources,
changes only through approval), search my notes by meaning, find people I know at my top matches from my
LinkedIn export, and let other AI apps (like Claude) read NxtRole safely through an MCP server.

## 2. Context and dependencies
- Requires Phases 7 (search, embeddings), 9 (applications, notes, rounds, offers), 10 (agent framework,
  SSE, documents). Read the current MCP Python SDK and LangGraph docs first.

## 3. Detailed implementation tasks
1. **Notes and RAG:** notes on jobs, applications, companies and interviews get embeddings; retrieval
   with hybrid search (Phase 7); answers cite notes as sources; chunk long notes.
2. **Ask NxtRole agent:** LangGraph chat with tools: search jobs, get a job, pipeline summary, follow-ups
   due, compare offers, search notes, today's brief, create a proposal (for any change; never applies it).
   Rules: answer only from tool results or notes, with sources shown; "I don't have that yet" when there
   is no data; requests to send or delete are refused with an offer to draft or propose instead; budgets
   (6 tool calls); replies streamed word by word; chats list, rename, delete; suggested prompts from the
   mock ("What should I do today?", "Compare my two offers", "Prep me for …", "Which skills do I keep
   missing?"); a "Tools it can use" panel. Long chats are summarised to fit the context.
3. **Network (referral finder):** import my LinkedIn `Connections.csv` (handle column-name variants,
   BOM, UTF-8/UTF-16, blank rows, duplicates; size limit); keep first name, last name, company, title,
   connected date, profile URL; drop email addresses; match contacts to companies of my top matches
   (normalised names with rapidfuzz, plus domains when known); referral ask drafts written by the AI with
   a `{name}` placeholder that **code** fills in (contact data never reaches the AI); "Copy and mark asked";
   status per person; staleness reminder after 90 days; "Delete all contacts".
4. **MCP server:** official MCP Python SDK, streamable HTTP mounted at `/mcp`; tools: today's brief, top
   matches, job details, pipeline summary, follow-ups due, search notes (read), and "create proposal"
   (write, needs my approval in NxtRole); personal tokens created in Settings › Connections (shown once,
   stored hashed, named, scoped read or read+propose, revocable); call log with tool, time and status;
   rate limit per token.
5. **Top bar search:** extend to companies and notes.

## 4. UI mock references
`Ask` / `MAsk` (chats, sources, tools panel, suggested prompts, approvals), `Network` / `MNetwork`,
`Settings` / `MSettings` (Connections, "Tools shared over MCP", "Recent calls"), `TopBar` (search),
`Brief` ("Needs you" referral items).

## 5. Recommended technologies
LangGraph, the Phase 5 gateway + Instructor, pgvector, rapidfuzz, Python `csv` with encoding detection, MCP Python SDK,
SSE streaming (from Phase 10).

## 6. Files and modules to create or modify
`api/app/chat/{graph,tools,router,models}.py`, `api/app/notes/{rag,embed}.py`,
`api/app/network/{csv_import,match,drafts,router,models}.py`, `api/app/mcp/{server,tools,auth,log}.py`,
migrations for `chats`, `chat_messages`, `contacts`, `mcp_tokens`, `mcp_calls`; web routes `/ask`,
`/network`, settings Connections; top bar search update.

## 7. Database and API requirements
Tables: `chats`, `chat_messages`, `contacts`, `mcp_tokens`, `mcp_calls` (+ note embeddings).
Endpoints: chats CRUD, `POST /api/chats/{id}/messages` (SSE reply), contacts import/list/delete, referral
drafts and status, MCP tokens CRUD and call log; `/mcp` for MCP clients.

## 8. Implementation sequence
Note embeddings + RAG → chat tools → chat graph + streaming → Ask UI → CSV import + matching → referral
drafts + Network UI → MCP server + token auth + log → Connections UI → search extension → tests and evals.

## 9. Testing requirements
Q&A eval: questions with known answers from my data (target ≥ 90% correct with sources); tool-choice eval
(20 tasks, target ≥ 18 correct). Tests: chat refuses to send/delete and offers a proposal; answers with no
data say so; prompt injection inside a note does not change behaviour; CSV variants (columns, encodings,
BOM, duplicates, huge file); contact names never appear in AI request logs (test the redaction);
MCP: missing/invalid/revoked token rejected, scopes enforced, rate limit, every call logged.

## 10. Edge-case checklist
- [ ] Chat asked to delete data or send a message.
- [ ] Question with no data; very long chat; two chats at once.
- [ ] Note or job text containing instructions (treated as data).
- [ ] CSV with different column names, encodings, BOM, empty rows, duplicates, over the size limit.
- [ ] Contact who has changed jobs (stale import reminder).
- [ ] MCP token leaked (revoke works immediately).

## 11. Security considerations
Least-privilege tools; proposals for every write; contacts never sent to AI; MCP tokens hashed and scoped;
call logs without personal content; rate limits; prompt-injection tests (OWASP LLM Top 10: injection,
data leakage, excessive agency).

## 12. Acceptance criteria
- [ ] I can ask real questions and get correct answers with sources; changes come only as proposals.
- [ ] Q&A ≥ 90% and tool choice ≥ 18/20 on my eval sets.
- [ ] Importing my LinkedIn CSV shows people at my top matches with copyable asks; emails are not stored.
- [ ] Claude (or another MCP client) can read my brief with a token, and loses access when I revoke it.
- [ ] Screens match the mocks; all tests, lint, types and build pass.

## 13. Documentation updates
`docs/ARCHITECTURE.md` (chat, RAG, MCP), `docs/API_DOCUMENTATION.md` (+ MCP tools),
`docs/DATABASE_SCHEMA.md`, `docs/SECURITY.md`, `docs/TESTING.md` (evals), `README.md` (connect Claude via
MCP), `docs/LEARNING_LOG.md`.

## 14. Completion report
`CLAUDE.md` section 9 format, with eval results. Explain: RAG, tool calling, streaming, MCP, scopes.

## 15. Approval
Stop. Write "Waiting for your approval before Phase 12." Do not commit.
