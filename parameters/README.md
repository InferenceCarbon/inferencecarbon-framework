# Parameters (paper Appendix A)

Machine-readable copies of everything Appendix A tabulates. **Every value
carries its source and access date in the row** — Appendix A has this in
prose; the CSV column is what makes a reviewer's spot-check take a minute
rather than an afternoon. Bracketed reference numbers (e.g. `[37]`) are the
paper's reference list.

| File | Contents |
|---|---|
| `provider_reference.csv` | Per-provider PUE and clean-energy match (Appendix A.1–A.4), the anchor's implicit PUE, the footprint-weighted OpenAI location/market-based intensities (§4.6–4.8), and the Stargate intensity scenarios |
| `routing_shares.csv` | OpenAI multi-cloud routing shares from the §4.5 contract-value proxy (Azure 26.7 / Oracle-Stargate 44.8 / AWS 4.0 / GCP 24.4), all at Low confidence — the paper's most consequential very-low-confidence input |

Values transcribed from the paper and verified against their cited sources.

## Grid intensities are not redistributed here

The subregion CO₂e emission rates the paper uses come from the Cornerstone
Sustainability Data Initiative's eGRID2024 computation (paper ref [26],
https://zenodo.org/records/18968658). That dataset carries its own licence
and is not reproduced in this repository. The individual rates the paper
relies on are quoted, with their subregion codes, in Appendix A and section
4.5 – 4.6; obtain the full table from the source above and match on the
subregion code (column SRL24/SRC2ERTA, annual CO₂e total output emission
rate, kg/MWh ≡ gCO₂e/kWh).
