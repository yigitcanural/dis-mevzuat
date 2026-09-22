# OpenAI Plugin Directory submission paketi

Bu paket 22 Eylül 2026 tarihinde güncel resmî OpenAI belgelerine göre remote
MCP-only **With MCP** submission için hazırlanmıştır. Eski 2023 ChatGPT plugin
manifesti (`ai-plugin.json`) kullanılmaz.

Resmî kaynaklar:

- [Submit plugins](https://developers.openai.com/plugins/deploy/submission?site_locale=en)
- [Remote MCP server review requirements](https://developers.openai.com/plugins/deploy/app-review?site_locale=en)

## Portal alanları — kopyala/yapıştır

**Submission type**

```text
With MCP
```

**MCP URL type**

```text
Universal
```

**App / plugin name**

```text
Türkiye Sağlık Turizmi Mevzuatı
```

**Developer name**

```text
Yiğitcan Ural
```

Portalda burada yazılan adla aynı doğrulanmış bireysel veya şirket kimliği
seçilmelidir.

**Version**

```text
0.2.0
```

**Logo file**

```text
assets/openai-plugin-logo.png
```

1254×1254 RGBA PNG; metinsiz ve devlet kurumu amblemi izlenimi vermeyen özgün işaret.

**Category**

```text
Research / Reference (portalda sunulan en yakın kategori)
```

**Short description**

```text
Search official Turkish health-tourism, healthcare advertising and privacy regulations with source citations and version-aware retrieval.
```

**Long description**

```text
A read-only compliance research tool for official Turkish health-tourism and healthcare sources. Search regulations and guidance about healthcare advertising, social media, before/after content, patient testimonials, prices and campaigns, privacy, consent, intermediary organizations and health-tourism authorization. Results include the relevant text, publishing institution, dates, current/archive status, version metadata and the official source URL. The tool does not provide legal advice, publication approval, medical diagnosis or treatment planning, and it must not be used to store patient records or health data.
```

**Website URL**

```text
https://mevzuat.sorgunbogaz.com/
```

**MCP Server URL**

```text
https://mevzuat.sorgunbogaz.com/mcp
```

**Privacy Policy URL**

```text
https://mevzuat.sorgunbogaz.com/privacy
```

**Terms URL**

```text
https://mevzuat.sorgunbogaz.com/terms
```

**Support URL**

```text
https://mevzuat.sorgunbogaz.com/support
```

**Authentication**

```text
None. The server is a public, read-only search interface over public official regulatory sources. It has no user accounts, private tenant data or write actions. No-auth maximizes standards-based MCP client compatibility. Abuse controls are enforced with request-size limits, timeouts, per-IP in-memory rate limiting and Cloudflare edge protections.
```

**Data processing**

```text
The application does not persist user query text or MCP results and application access logs are disabled. For rate limiting, a process-keyed pseudonymous value derived from the connecting IP is held transiently in memory for approximately one minute; the raw IP is not retained by the application. Cloudflare Tunnel may process network metadata under Cloudflare's terms. Semantic embeddings are disabled in the submitted production configuration. Users must not submit patient photos, videos, CRM records, medical files or other personal health data. Personal data is not sold.
```

**Security model**

```text
Public tools are read-only and cannot fetch arbitrary URLs or mutate the database. Admin/source-ingestion tools run in a separate local-only MCP process. The origin binds to localhost/private Docker networking and is published through Cloudflare Tunnel over HTTPS without router port forwarding. The service applies request-size and timeout controls, rate limiting, security headers, bounded logging and container hardening. Source ingestion uses an official-domain allowlist, public-IP validation on every redirect, content-size limits, hashing, staging and explicit human approval.
```

**Release notes**

```text
Initial public remote MCP release. Generalizes the existing dental regulations index into a provider-neutral Turkish health-tourism regulations service; adds six read-only public tools with structured evidence, version-aware current/archive metadata, isolated local admin tooling, HTTPS deployment hardening, policy/support pages and independent MCP smoke tests.
```

**Country availability**

```text
Türkiye initially; add other countries only if the portal audience policy and support capacity are confirmed.
```

## Starter prompts

```text
Instagram'da hastanın öncesi/sonrası fotoğrafını paylaşmaya ilişkin güncel resmî kaynakları bul ve kaynakta yazanla yorumunu ayır.
```

```text
Yurt dışındaki hastalara fiyat kampanyası göstermeye ilişkin sağlık turizmi kurallarını güncel kaynaklarıyla karşılaştır.
```

```text
Hasta yorumlarının sağlık hizmeti tanıtımında kullanımına ilişkin güncel ve arşiv kaynakları ayırarak araştır.
```

```text
Saç ekimi kliniğinin influencer ile reklam yapmasına ilişkin resmî kaynaklarda kanıt ara; kesin hukuki onay verme.
```

## Tool inventory ve annotations

| Tool | Amaç | readOnlyHint | destructiveHint | idempotentHint | openWorldHint |
|---|---|---:|---:|---:|---:|
| `search_regulations` | FTS5/opsiyonel hybrid mevzuat araması | true | false | true | false |
| `list_sources` | Kaynak kataloğunu listeleme | true | false | true | false |
| `get_source` | Bir kaynak ve parçalarını getirme | true | false | true | false |
| `get_chunk` | Tek kanıt parçasını getirme | true | false | true | false |
| `get_source_status` | Sürüm ve current/archive durumu | true | false | true | false |
| `system_status` | İndeks/retrieval sağlığı | true | false | true | false |

`openWorldHint=false` gerekçesi: public araçlar yalnız önceden onaylanmış yerel
mevzuat indeksini okur; çağrı sırasında internete veya haricî sisteme erişmez.

## Submission materyalleri

- Test vakaları: [test-cases.md](test-cases.md)
- Güvenlik modeli: [security-model.md](security-model.md)
- Veri işleme: [data-processing.md](data-processing.md)
- Screenshot planı: [screenshots.md](screenshots.md)
- Checklist: [submission-checklist.md](submission-checklist.md)
