# Submission checklist

- [ ] OpenAI Platform publisher identity matches `Yiğitcan Ural` or replace every listing field with the exact verified identity.
- [ ] Organization/project has global (not EU) data residency for MCP submission.
- [ ] Submitter has Apps Management Write (`api.apps.write`) and Read access.
- [ ] Production MCP, landing, privacy, terms and support URLs return HTTPS 200.
- [ ] Domain challenge token is set and `/.well-known/openai-apps-challenge` returns the exact portal value.
- [ ] `python scripts/mcp_smoke.py https://mevzuat.sorgunbogaz.com/mcp` passes.
- [ ] Portal **Scan Tools** discovers exactly six public tools and no admin tool.
- [ ] Every tool shows accurate `readOnlyHint`, `destructiveHint`, `idempotentHint` and `openWorldHint`.
- [ ] Five positive and three negative test cases are copied from `test-cases.md`.
- [ ] Privacy text matches production embedding/log/Cloudflare settings.
- [ ] No screenshots are uploaded because this version has no MCP UI.
- [ ] `assets/openai-plugin-logo.png` portalda yüklenir; marka sahipliği ve son görsel kontrolü onaylanır.
- [ ] Country availability and support capacity are confirmed.
- [ ] Release notes and policy attestations are completed.
