# Security model

## Trust boundaries

- Internet -> Cloudflare edge -> remotely managed Tunnel -> private Docker network -> public MCP.
- Public MCP -> local read-only SQLite index.
- Local admin MCP -> allowlisted official source URLs -> staging -> human approval -> index.

## Controls

- Public inventory contains exactly six read-only tools; no dynamic URL fetch.
- Admin process is separate and refuses non-loopback HTTP binding.
- Origin has no public router port; Docker host binding is loopback only.
- Per-IP in-memory rate limit, 1 MiB request limit and 20-second application timeout.
- Security headers, HSTS behind HTTPS, no application access log, rotated container logs.
- Container uses read-only root, no-new-privileges, dropped capabilities and bounded tmpfs.
- SQL values are parameterized; FTS input is tokenized and quoted.
- Source ingestion rejects credentials, nonstandard ports, unapproved domains,
  localhost/private/reserved IPs, redirect-to-private targets, oversized bodies
  and malformed/overlarge PDFs.
- New source bytes are hashed and staged. Only explicit approval activates a version.
- Database/raw sources persist outside the container and have backup/restore scripts.

## Residual risks

- Legal sources can change between retrieval and use; every result exposes dates,
  current/archive status and official URL for verification.
- In-process rate limits reset on restart and do not replace Cloudflare edge limits.
- Cloudflare retention/settings are external configuration and must be audited in
  the dashboard before submission.
- Optional embedding sends query text to the configured provider; it is disabled
  in the submitted production configuration.
