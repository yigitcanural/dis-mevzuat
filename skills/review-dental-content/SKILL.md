---
name: review-dental-content
description: Review dental clinic captions or long-form articles and supplied visuals before publication by using the Diş Mevzuat MCP for source-backed risk screening. Use when asked whether clinic content is suitable to publish across one or more platforms, to explain Turkey/domestic and international publication risks separately without inferring the intended market, to identify advertising, patient-rights, consent, privacy, price, testimonial, or before/after risks, or to rewrite risky passages for human approval.
---

# Review Dental Content

Perform a source-backed pre-publication review. Treat the result as operational risk
screening, not a legal opinion or permission to publish. Leave the final decision to a human.

## Establish scope

Identify these inputs from the request or supplied material:

- Content and any visible text, speech, claims, images, links, or calls to action
- Content format: caption/short-form copy or article/long-form copy
- Any paid advertising or audience targeting that changes how the content is distributed
- Whether real patients, health data, testimonials, prices, discounts, or results appear

Classify the content by its form, not by the platform where it will appear. Treat a caption as
the same caption when it is cross-posted to Instagram, LinkedIn, Google Business, or another
platform. Treat a long-form article as the same article when it is published on a clinic blog,
LinkedIn, Reddit, or another platform. Analyze platforms separately only when paid targeting,
visual treatment, character limits, links, or other platform-specific presentation changes the
content or its legal context.

Never infer or choose the intended market from language, platform, account, or content. Always
explain two separate scenarios: publication in Turkey/domestic use and publication directed
internationally. Present them as conditional scenarios, not as a claim about the user's actual
target market. Do not ask the user to choose a target market as a prerequisite for the review.

If a visual or attachment cannot be inspected, explicitly limit the review to the available
text. Never place patient images or clinic patient records into the public-law MCP index.
Do not reflexively tell the user that a real patient image can never be reviewed. If an image
review is requested, briefly explain that an identifiable patient image may contain
special-category health data and should only be handled when the clinic's authority and data
policy permit it. Prefer a de-identified, tightly cropped, redacted, or synthetic example when
that is sufficient. Never send the image, patient identifiers, or image-derived identifiers to
the public-law MCP. Do not claim that an AI client, project folder, or chat is local or private
merely because the files and MCP server are local: the model provider may still process uploaded
content remotely. Clearly distinguish “not sent to the MCP index” from “not transmitted to the AI
provider.” Before inviting an identifiable patient image, require the clinic to verify its chosen
AI deployment, contractual/data-processing terms, retention and training settings, access
controls, and authority for that processing. If those facts are not verified, recommend a
de-identified or synthetic example or an appropriately governed local model instead. Describe
processing as device-local only when that architecture has actually been verified. Do not treat
eye bars or simple cropping as reliable anonymization. Do not repeat a long privacy warning in
every answer when no image handling is actually requested.

## Inspect the content

Extract concrete review subjects before searching. Check at least:

- Treatment outcomes, guarantees, certainty, superiority, comparison, or unverifiable claims
- Before/after presentation, patient stories, testimonials, gratitude, and implied endorsement
- Price, discount, package, campaign, urgency, giveaway, or sales-oriented calls to action
- Patient identity, consent, health data, privacy, and reuse of supplied media
- Practitioner title, specialty, clinic identity, contact information, and required disclosures
- Paid targeting, audience location, language, and domestic accessibility when supplied
- Misleading omissions, fear, pressure, or content that may create unjustified expectations

Do not decide from keywords alone. Interpret text, visual presentation, and any supplied
targeting together.

Describe image privacy status conditionally. A patient image that is identifiable, reasonably
linkable to a person, or retained together with patient records is personal health data; a
genuinely and irreversibly anonymized image may fall outside that scope. Do not declare every
tightly cropped intraoral image personal data without considering linkability, and do not assume
that cropping or an eye bar achieves anonymization.

Classify each issue precisely. A missing consent, date, warning, interaction setting, or other
visual-content condition creates potential regulatory non-compliance; it does not automatically
prove that the content is covert advertising. Analyze advertising separately under the
advertising principles by considering claims, inducement, price, promotion, testimonials,
calls to action, and overall presentation. Never write that one missing condition automatically
turns a post into advertising.

## Retrieve evidence from the MCP

1. For an ordinary review, run 2–4 narrow `search_sources` queries derived from the actual risk
   subjects and use a small result set such as `top_k=3`. Prefer separate queries such as
   `fiyat indirim kampanya`, `hasta yorumu öncesi sonrası`, or `yurt dışı hedefleme
   HealthTürkiye` over one long generic query.
2. Do not call `list_sources` during an ordinary review. Call `system_status` only when an MCP
   request fails, freshness is genuinely uncertain, or the user explicitly asks about system
   status or source freshness.
3. Use `get_chunk` or `get_source` only when a critical passage is ambiguous or the search
   excerpt is insufficient to verify the exact rule.
4. Prefer current primary legislation, then professional guidance, then enforcement examples.
   Use enforcement decisions as practical examples, not as replacements for legislation.
   For dental-clinic questions, check the current TDB communication/publication guidance when it
   is relevant, but label it as professional guidance rather than presenting it as legislation.
   Do not describe a professional guideline as legally binding unless the retrieved source
   establishes that status. It may still indicate professional-discipline or operational risk.
   If current professional guidance is stricter than, or appears to conflict with, primary
   legislation, surface the conflict and its practical uncertainty instead of silently choosing
   one or claiming that the guideline overrides the legislation.
5. Cite material findings inline with the shortest useful legal reference, normally the
   legislation or decision name and article/subparagraph, for example `2025 Tanıtım Yönetmeliği
   md. 7/1-f` or `KVKK Kurulunun 2022/630 sayılı kararı`. Never invent an article number or
   decision reference.

Retrieve only evidence needed for the findings. Do not load every source or paste long legal
passages. If MCP access fails or relevant evidence is absent, say that the result is not
source-verified instead of relying silently on memory.

Use the MCP sources as internal evidence, not as an output dump. By default, do not show raw
URLs, clickable links, source IDs, hashes, chunk IDs, MCP call logs, or a separate sources list.
Provide links or a fuller source list only if the user explicitly asks for them. A comprehensive
answer like a rules table is acceptable when the question genuinely calls for it; efficiency
means avoiding redundant retrieval and metadata, not stripping useful legal explanation.

Do not narrate retrieval with messages such as “I am checking the sources now” or “I found
article 7; now I will search article 8” unless the user explicitly asks for progress. Perform the
necessary calls and present the finished review.

Before using an enforcement decision, compare the content/publication date and the rules applied
in the decision with the effective date of the current regulation. A decision concerning content
published under an earlier regime must be labelled as historical enforcement context; it cannot
by itself prove how a post satisfying the current regulation will be treated. Describe the full
combination assessed in the decision, such as before/after imagery plus patient praise, claims,
prices, or calls to action. Do not rewrite a multi-factor decision as a holding that before/after
imagery alone was prohibited or inherently comparative.

When drawing a practical conclusion from a privacy decision, separate what the decision actually
held from additional risk-management advice. For example, a decision about consent given to one
data controller not covering another account supports checking the recipient/controller and
purpose; it does not by itself establish every proposed consent-form field, such as a mandatory
duration. Label any additional detail as recommended practice unless another source makes it a
legal requirement.

## Explain both market scenarios

Always produce two distinct conclusions for the same content:

1. **If published in Turkey / for domestic use:** Assess the rules governing health-service
   information and promotion in Turkey.
2. **If directed internationally:** Additionally retrieve and assess the current international
   health-tourism promotion and targeting provisions.

Do not merge the conclusions and do not select one on the user's behalf.

In the international scenario, explain that foreign language alone does not establish
international targeting. State which operational facts matter, such as ad audience location,
account settings, landing page, or distribution method, without deciding those facts yourself.
Do not end by asking which market the user selected; provide both conditional explanations.
Do not summarize patient stories, comments, gratitude, or testimonials as categorically
prohibited for domestic use. Preserve the qualification in the rule: domestic risk turns on
whether gratitude or satisfaction expressions are used for an advertising presentation, while
the international regime contains a separate express permission subject to its own conditions.
For a dental clinic considering sponsored international health-tourism content, check both the
express permission and conditions in article 8 and any stricter current TDB sponsored-publication
guidance. If they point in different directions, explain the regulatory permission and the
separate professional-discipline uncertainty; do not collapse them into a simple “permitted” or
“prohibited” verdict.

## Report consistently

Lead with one of these screening outcomes:

- **High risk:** A clear source-backed issue should be corrected before publication.
- **Needs revision:** Material uncertainty or a correctable presentation/claim risk exists.
- **No clear issue found:** No issue was found in the checked scope; this is not legal approval.
- **General framework only:** No concrete caption, article, or visual was supplied, so do not
  assign a content-specific outcome.

Then provide:

1. **Scope:** caption or article, supplied visuals, and any material targeting information
2. **Findings:** exact content element, risk, reason, and supporting source
3. **Turkey/domestic scenario:** separate conclusion
4. **International scenario:** separate conclusion
5. **Safer revision:** preserve the communication goal without promising legal compliance
6. **Missing facts:** only facts that could materially change the conclusion
7. **Human checkpoint:** identify what the responsible clinic reviewer must confirm
Distinguish “the search returned no evidence” from “the conduct is permitted.” Do not use
absolute statements such as “legally safe,” “definitely compliant,” or “you can publish.” For
generic questions, avoid blanket openings such as “categorically permitted” or “not prohibited.”
Say instead that the current regulation provides a conditional framework and that a concrete
content review requires the actual caption, article, or safely handled visual.

Keep the answer proportionate. For a general legal-framework question, a structured explanation,
rules table, domestic/international split, and material missing facts may be useful. For a simple
caption, focus on the actual issues instead of repeating the full framework. Never claim that a
missing consent, date, warning, interaction setting, or similar condition automatically converts
the content into covert advertising; describe it as potential regulatory non-compliance and run
the advertising analysis separately.

Do not label a table or list as “all conditions” unless every applicable paragraph has actually
been checked and included. If only the provisions most relevant to the question are shown, call
them “key conditions” or “relevant conditions.” In a purportedly complete summary of article 7,
do not silently omit paragraph 7/1-a or another applicable paragraph.
