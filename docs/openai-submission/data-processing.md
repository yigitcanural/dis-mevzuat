# Data processing explanation

The service receives MCP protocol metadata, tool arguments and a regulation
search query. It reads an approved SQLite index and returns source excerpts and
provenance. Query content and responses are not persisted by the application.
Application access logs are disabled. The origin limiter does not retain the raw
connecting IP. It keeps a process-keyed, pseudonymous value in memory for
approximately one minute and does not write it to disk.

Cloudflare Tunnel terminates/proxies HTTPS and may process network metadata under
the account's Cloudflare configuration and agreements. The application does not
claim a Cloudflare retention period it cannot verify.

Semantic retrieval is optional. When enabled, query text is sent to the configured
embedding API. It is disabled in the public submission configuration.

The service is not a patient-record system. Patient photos, videos, CRM records,
medical files, identifiers and health data must not be submitted. Personal data
is not sold.
