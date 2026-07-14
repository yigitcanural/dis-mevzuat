# Shared project context

This file is the version-controlled memory shared by humans and AI agents. Keep
only durable project facts here. Do not paste conversations, user profiles,
credentials, patient material, or temporary task notes.

## Current state

- Release: `0.1.0`
- Published snapshot date: 2026-07-14
- Default operation: local Python, stdio MCP, SQLite FTS5, no API key
- Optional operation: local HTTP transport, Docker, and external embeddings
- Human responsibility: every legal-risk conclusion and publication decision

The current repository covers the public-law knowledge layer and the dental-content
review workflow. A future clinic-content knowledge system must remain a separate data
boundary; private clinic or patient data must never be mixed into this public-law index.

## System map

```text
AI client
  -> MCP tools in server.py
  -> ComplianceService in service.py
  -> SQLite sources/chunks/FTS in database.py

Source maintenance
  -> URL/text extraction
  -> staging record + content hash
  -> separate human approval
  -> raw archive + chunks + FTS (+ optional embeddings)
```

The MCP retrieves evidence. The review skill interprets a supplied caption, article,
visual, and targeting facts against that evidence. This separation is intentional.

## Sources of truth

- Public MCP surface: `src/dis_mevzuat/server.py`
- Runtime settings: `src/dis_mevzuat/config.py` and `.env.example`
- Database schema and FTS behavior: `src/dis_mevzuat/database.py`
- Maintained source list: `data/seed_sources.json`
- Published source snapshot: `data/dis_mevzuat.sqlite3`
- Editorial/legal-risk workflow: `skills/review-dental-content/SKILL.md`
- User setup and snapshot counts: `README.md`

If documentation conflicts with executable behavior, verify the code and tests, then
update the owning documentation rather than creating another source of truth.

## Durable decisions

1. **Local and keyless first.** FTS5 is the baseline. Embeddings are optional and must
   not be required for useful search.
2. **MCP is retrieval, not a legal decision engine.** The server exposes evidence and
   metadata; the skill controls the review method and output discipline.
3. **Content form before platform.** A cross-posted caption remains one caption unless
   targeting, visual treatment, links, or another platform-specific fact changes the risk.
4. **Always explain both market scenarios.** Domestic Turkey and internationally directed
   publication are separate conditional analyses; the agent does not infer or select one.
5. **Human approval at both boundaries.** Source activation and publication decisions remain
   human responsibilities.
6. **Concise evidence by default.** Cite the shortest useful source/article reference. Do not
   dump URLs, chunk IDs, hashes, or full source lists unless requested.
7. **Public law and private clinic knowledge stay separate.** A later clinic-content MCP or RAG
   system requires its own access controls, storage, retention, and data-processing design.
8. **Shared memory is checked-in context.** Vendor-specific auto-memory and chat history may
   help locally but are never required to understand or maintain the repository.

## Non-obvious behavior

- `Settings.from_env()` creates the selected data, raw, and staging directories.
- Opening the database initializes schema and WAL mode; apparently read-only commands may
  create ignored `-wal` or `-shm` files.
- Admin tools are registered when `server.py` is imported, based on the environment at that
  moment. Changing the variable after import does not change the exposed tool set.
- FTS synchronization is performed by application code, not by database triggers.
- There is no migration framework; schema setup currently uses idempotent creation statements.
- Enabling embeddings transmits source chunks during indexing and search queries during
  retrieval to the selected provider.
- `skills/review-dental-content/agents/openai.yaml` describes an optional HTTP dependency for
  distributed skill metadata. The checked-in Claude and Codex project configs use local stdio.

## Known limitations and risks

- HTTP mode is designed for loopback development and is not hardened for public deployment.
  Authentication, Host/Origin protection, TLS, rate limits, and network egress controls are
  required before any remote exposure.
- Admin tools have no standalone authorization layer. Keep them local and disabled during
  ordinary use.
- Source preview and approval are technically callable by the same client; repository policy
  requires a separate human checkpoint.
- The committed SQLite snapshot and a writable runtime database currently share the same
  filename. Development source maintenance can therefore dirty or contaminate the published
  snapshot if it is run in the repository data directory.
- Public enforcement documents may themselves contain names, account handles, or contact
  details. “Public source” does not mean “contains no personal data”; avoid reproducing such
  details and perform a privacy scan before snapshot releases.
- Test coverage currently focuses on chunking, core service behavior, and repository config.
  Extraction/SSRF behavior, MCP registration, embeddings, CLI seeding, and snapshot privacy
  need broader automated coverage.
- Docker is optional and not the security baseline. Scan and pin its base image before treating
  it as a production artifact.

## Update this file when

- a durable product or architecture decision changes;
- a known limitation is fixed or a new one is accepted;
- data boundaries, source lifecycle, or human approval points change;
- a future maintainer would otherwise need the old conversation to understand the repository.

Do not use this file as a changelog or task list. Git history owns completed change history;
issues or a current task own temporary work.
