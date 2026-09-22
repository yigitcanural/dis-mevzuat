---
name: review-health-tourism-content
description: Review Turkish healthcare or health-tourism marketing, social-media, website, price, testimonial, patient-media, privacy, or intermediary content against current official sources through the health-tourism regulations MCP. Use for source-backed pre-publication risk screening; do not use it to grant legal approval, diagnose patients, or store patient data.
---

# Review Health Tourism Content

Produce a source-backed pre-publication risk screen, not a legal opinion or
permission to publish. The responsible human remains the final decision-maker.

## Establish the actual scenario

Identify the content, format, publisher/provider type, paid distribution,
audience targeting, landing page, and whether it contains:

- Treatment outcomes, guarantees, comparisons or superiority claims
- Before/after media, patient stories, reviews or testimonials
- Price, discount, campaign, package, urgency or calls to action
- Patient identity, health data, consent or reuse of media
- Influencers, intermediary organizations or referral activity
- Health-tourism authorization or HealthTürkiye-related claims

Do not infer the target market from language alone. When the market is not
explicit, explain Turkey/domestic and internationally directed scenarios
separately. A foreign language alone does not establish foreign targeting.

Do not send patient photos, CRM records, patient files, identifiers or medical
records to the regulations MCP. If an identifiable patient image is relevant,
review a de-identified description when possible and distinguish the AI
provider's data processing from the MCP index. Never claim an upload is local
or private unless that architecture was actually verified.

## Retrieve only necessary evidence

1. Run two to four narrow `search_regulations` queries for the concrete risks,
   normally with `top_k=3` and `current_only=true`.
2. Use `get_chunk` to verify a critical passage or `get_source_status` to check
   dates/version. Use `get_source` only when the wider document is necessary.
3. Prefer Resmî Gazete and ministry sources, then KVKK, USHAŞ/HealthTürkiye and
   other primary official bodies. Treat professional guidance and enforcement
   examples according to their actual authority; do not relabel them as law.
4. Prefer current sources. If an archived source or older enforcement decision
   is relevant, label its historical period and compare it with the current rule.
5. If sources conflict, concern different periods, or do not answer the issue,
   say so. Never turn “no result” into “permitted.”

Keep source text and analysis separate. Cite the shortest useful source name and
article/section inline, and provide the official URL when the user asks for links
or when the review needs an auditable evidence trail. Never invent an article,
date, authority or source status.

## Assess precisely

Evaluate each issue on its own legal or operational basis. Missing consent,
warning, date, interaction setting or disclosure may create non-compliance or
privacy risk; it does not automatically prove covert advertising. Analyze the
overall advertising presentation separately, including claims, inducements,
prices, testimonials, targeting and calls to action.

Consent does not automatically settle advertising, professional-rule or data-
controller questions. Separate what the retrieved source explicitly requires
from recommended risk-management practice.

## Report

Lead with one screening outcome:

- **High risk** — clear source-backed issue to correct before publication
- **Needs revision** — material uncertainty or correctable presentation risk
- **No clear issue found** — none found in checked scope; not legal approval
- **General framework only** — no concrete content was supplied

Then give the scope, findings with evidence, domestic scenario, international
scenario, safer revision, material missing facts and human checkpoint. Keep the
answer proportional to the content. Do not say “legally safe,” “definitely
compliant,” “approved,” or “you can publish.”
