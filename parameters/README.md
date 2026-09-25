# Parameters (paper Appendix A)

Machine-readable copies of everything Appendix A tabulates. **Every value
carries its source and access date in the row** — Appendix A has this in
prose; the CSV column is what makes a reviewer's spot-check take a minute
rather than an afternoon. Bracketed reference numbers (e.g. `[32]`) are the
paper's reference list.

| File | Contents |
|---|---|
| `provider_reference.csv` | Per-provider PUE, clean-energy claims and — where reported — realized market-based Scope 2 intensities (Appendix A.1–A.4; Microsoft, Oracle and Google are credited at the realized figure, AWS at face value), the anchor's implicit PUE, the footprint-weighted OpenAI location/market-based intensities (§4.6–4.8), the Stargate intensity scenarios, and the pre-fill ratio of Appendix D.5.8 |
| `routing_shares.csv` | OpenAI multi-cloud routing shares from the §4.5 contract-value proxy (Azure 23.4 / Oracle-Stargate 39.3 / AWS 11.7 / GCP 25.5), all at Low confidence — the paper's most consequential low-confidence input |

Values transcribed from the paper and verified against their cited sources.

## Grid intensities are not redistributed here

The subregion CO₂e emission rates the paper uses come from the Cornerstone
Sustainability Data Initiative's eGRID2024 computation (paper ref [27],
https://zenodo.org/records/18968658). That dataset carries its own license
and is not reproduced in this repository. The individual rates the paper
relies on are quoted, with their subregion codes, in Appendix A and section
4.5 – 4.6; obtain the full table from the source above and match on the
subregion code (column SRL24/SRC2ERTA, annual CO₂e total output emission
rate, kg/MWh ≡ gCO₂e/kWh).
