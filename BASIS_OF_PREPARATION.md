# Basis of preparation — InferenceCarbon framework v1.0.0

This document states, in the form an inventory preparer or assurance provider expects, how the figures
in *A Bounded Estimation Framework for the Per-Token Carbon Intensity of LLM Inference Under Limited
Disclosure* (v1.0.0) were prepared, what they cover, what they exclude, and how good the inputs are.
It summarises the paper; the paper is canonical, and section references are to it.

## 1. What the figures are

Attributional estimates of the operational (GHG Protocol Scope 2 category) greenhouse-gas intensity of
OpenAI GPT-5.x inference, stated as **gCO₂e per 1,000 output tokens** at the anchor's 1:3 input:output
shape (Appendix D.5.1). Each figure is a central estimate with a Low and High plausibility bound (Table 8)
and a qualitative confidence label (Table 11). They are modelled from public information and an owned
throughput campaign; **none is a measurement of OpenAI's energy use**, and they are not compliance-grade
absolutes (Section 7).

For a user of the figures as Scope 3 emission factors (purchased services), they are *secondary data* in
GHG Protocol Scope 3 terms, and this document is their data-quality record.

## 2. Boundary

| | In | Out |
|---|---|---|
| Life-cycle stage | Operational electricity of inference serving: accelerator, host, cooling and power-delivery overhead via PUE (Section 3.1) | Training; embodied emissions of hardware and buildings; networking outside the data centre; end-user devices; water |
| Energy components | Decode energy per output token, with the anchor's prefill folded in at the 1:3 shape (Appendix D.5.8 gives the shape correction) | Fixed fleet floor as a separate term (attributional average is reported, not marginal — Section 1); tool execution and orchestration in agentic chains (limitation 6) |
| Scopes | Scope 2 of the serving provider, allocated to output tokens: location-based and market-based reported in parallel (Sections 3.6 – 3.7) | Scope 1 of the provider (except the off-grid gas scenario, Appendix D.3); Scope 3 of the provider |
| Gases | CO₂e as published in the grid factors (eGRID 2024 combustion-only; upstream methane excluded on both sides for boundary comparability — Section 4.6) | Upstream fuel-cycle emissions (~93 gCO₂e/kWh for gas, quantified and excluded) |
| Geography | US grid subregions of the assessed data-centre locations, footprint-weighted by the routing proxy (Sections 4.5 – 4.7) | Non-US serving |
| Period | Throughput and reasoning telemetry 24 June – 22 August 2026 (frozen corpus); grid factors eGRID 2024; provider market-based intensities Microsoft FY2025, Oracle FY25, Google CY2025 | Anything after the 22 August 2026 data close |

## 3. Method in one paragraph

An anchor energy per query (Jegham et al. [15], GPT-4o-mini, 0.577 Wh at 100 in / 300 out) is restated
per 1,000 output tokens, scaled to each GPT-5.x variant by the ratio of measured output throughputs
(Section 3.2), adjusted for provider PUE (3.1) and for the higher per-accelerator power of the target
fleet (PQPC, 3.4), and multiplied by the variant's measured reasoning multiplier — hidden plus visible
tokens over visible tokens on a fixed hard task (3.3). Energy is converted to carbon at a footprint-weighted
grid intensity built from a contract-value routing proxy across Azure, Oracle/Stargate, AWS and Google
Cloud (3.5, 4.5 – 4.8): location-based at the assessed grid subregions, market-based under the GHG Protocol
Scope 2 Guidance (2015) with each provider credited at its own reported realised market-based intensity
where it publishes one (Microsoft, Oracle, Google) and at the face value of its match claim where it does
not (AWS). Bounds compound declared bands on the anchor, PQPC and PUE with bootstrap bands on throughput
and the reasoning multiplier (3.8, Appendix D.6).

## 4. Data-quality indicators

Scored on the GHG Protocol Scope 3 five-indicator scale, 1 = very good … 5 = very poor, and mapped to the
paper's Table 11 confidence labels. Scores are the authors' judgement and are the point an assurance
provider should challenge first.

| Input | Technological | Temporal | Geographical | Completeness | Reliability | Table 11 |
|---|---|---|---|---|---|---|
| Anchor energy per query (Jegham GPT-4o-mini) | 3 — A100-era model, simulation not metering | 2 — 2025 | 2 — US | 3 — one model, two shapes | 3 — peer-reviewed preprint, model not measurement | Medium / Limited |
| Throughput per variant (owned campaign) | 1 | 1 — in-period | 2 — one vantage point | 1 — 46 variants, 8 – 105 records each | 2 — measured; per-stream, not cluster (E.1) | Medium |
| Reasoning multipliers (owned campaign) | 1 | 1 | 2 | 2 — fixed hard task at three lengths | 2 — measured; task-conditional (limitation 7) | Medium |
| PQPC (2.99) | 3 | 2 | n/a | 3 | 4 — assumed from rated power and utilisation literature | Limited / Low |
| PUE — hyperscalers | 2 | 2 — 2024/25 | 2 | 2 | 1 — provider-disclosed | Robust |
| PUE — Stargate | 3 | 2 | 2 | 3 | 4 — design figure, not operating | Limited |
| Grid intensities (eGRID 2024) | 2 | 2 | 1 — subregion | 2 — combustion-only | 1 — published dataset | Robust |
| Routing shares (contract-value proxy) | 4 | 3 | 3 | 4 — GCP share wholly inferred | 5 — proxy, untestable | Limited / Low |
| Market-based crediting — Microsoft, Google | 2 | 1 | 2 — corporate, not workload | 2 | 2 — reported Scope 2, limited assurance | Medium |
| Market-based crediting — Oracle/Stargate | 3 | 4 — out-of-period | 3 | 3 | 3 | Limited / Low |
| Market-based crediting — AWS (zero) | 3 | 2 | 3 | 4 — no electricity denominator | 4 — face-value claim | Medium / Low |
| Pre-fill ratio (shape correction) | 3 | 2 | n/a | 3 — two points, one model | 4 — factor-of-five spread | Low |

## 5. Conventions a user must apply

- Quote a figure with its band and confidence label, never alone (Section 8.6).
- Where the inventory convention is not to understate, use the **High** bound of Table 8.
- Location-based is the operative column for a user deciding what to run; market-based serves corporate
  accounting under the 2015 Guidance and will be re-stated when the revised standard is published (3.7, 8.5).
- Queries far from the 1:3 shape: apply the shape correction of Appendix D.5.8.
- Restating per 1,000 *total* tokens at the 1:3 shape multiplies every figure by 0.75 (limitation 29).
- Cite the version DOI; figures change between versions and the changelog says how (8.5).

## 6. Materiality and what the bounds mean

The Low – High envelope is a plausibility band formed by compounding assigned and bootstrap widths; it is
not a confidence interval and carries no probability statement (3.8). Its median top-to-bottom span is about
11×. No absolute figure in this release could meet a 5 – 10% materiality threshold; the routing proxy alone
moves the location-based headline by about −10% to +27% and the market-based headline from 47 to 65
gCO₂e/kWh across Table 10's scenarios. Within-family *ratios* — one model against another at a fixed
setting, or one setting against another on the same model — are known to roughly ±10% because the common
factors cancel (Table C3), and are the figures on which a decision can safely rest.

## 7. Verification status

See [VERIFICATION.md](VERIFICATION.md): what has been independently reproduced, by whom, and what has not.

## 8. Contact and corrections

methodology@inferencecarbon.ai — corrections are incorporated under the policy in Section 8.5 and logged in
[CHANGELOG.md](CHANGELOG.md).
