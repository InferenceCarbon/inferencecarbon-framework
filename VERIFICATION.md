# Verification — InferenceCarbon framework v1.0.0

What can be checked, how, what has been checked, and by whom. The aim is that an assurance provider can
follow the chain from raw record to published cell with no step that depends on the authors' word.

## 1. The chain of evidence

```
frozen corpus (zip, SHA-256)             data/InferenceCarbon_corpus_frozen_20260822.zip
      │  corpus_summary.py  (filters F1–F6, seeds 20260822 / 20260823)
      ▼
Corpus / Bootstrap / RatioEnvelopes sheets   data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx
      │  workbook formulas (Assumptions → GridIntensity → Table6 → Table7 → C_Low/C_High → Table8)
      ▼
paper_tables.py --out                  reproduce/expected/tables/*.csv
      │  paper_tables.py --paper       cell-by-cell comparison with the .docx
      ▼
paper Tables 1, 3–11, B1, C1–C3
```

Each arrow is a script or a formula in the deposit. The parameter inputs that are typed into the workbook
(anchor, PUE, PQPC, grid intensities, provider Scope 2 figures, routing shares) are listed with their source
and access date in `parameters/*.csv`, and every one is a public document a verifier can open.

## 2. Verification steps

| Step | Command | Expected result |
|---|---|---|
| V1 Corpus integrity | `(cd data && shasum -a 256 -c InferenceCarbon_corpus_frozen_20260822.sha256)` | OK |
| V2 Corpus → workbook inputs | `python reproduce/corpus_summary.py --corpus data/InferenceCarbon_corpus_frozen_20260822.zip --out out/cs --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx` | Corpus sheet agreement report (644/644); bootstrap bands and ratio envelopes agree to the displayed precision |
| V3 Workbook → tables | `python reproduce/paper_tables.py --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx --out out/tables && diff -r out/tables reproduce/expected/tables` | no differences |
| V4 Tables → paper | `python reproduce/paper_tables.py --workbook ... --paper <paper .docx>` | every compared cell agrees at displayed precision |
| V5 Parameters → sources | open each `source_url` in `parameters/*.csv` and confirm the value | manual |
| V6 Workbook formulas | `python reproduce/formula_audit.py --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx` | "undeclared numeric constants: 0", exit status 0 |

## 3. Verification record

### 3.1 Author-side reproduction, 21 September 2026 (Claude Fable 5.1 at the author's direction — not independent)

- V1: OK.
- V2: Corpus sheet — 644 of 644 cells agree. Bootstrap bands (184 values) and ratio envelopes (33 values)
  agree to 0.0000; the deposited script is the source of the workbook's values (see reproduce/README.md,
  "Regenerating the workbook"). Output identical to `reproduce/expected/corpus_summary/`.
- V3: output identical to `reproduce/expected/tables/`.
- V4: paper v1.0.0: Tables 6, 7, 8, B1, C1 and C2 — 1,971 numeric cells compared, 1,971 agree. Tables 1,
  3 – 5, 9 – 11, C3 and D1 checked against the exported CSVs by hand.
- V6: 3,943 formulas, 461 declared inputs, 0 undeclared constants.

### 3.2 Independent reproduction

**None yet.** The framework is not independently verified. See the open items below.

## 4. Known discrepancies

None known between the corpus, the deposited workbook and the paper's tables at this release. Discrepancies
found after release are recorded here until the next release corrects them (VERSIONING.md,
"Paper-authoritative artefacts").

One rule is worth restating because a verifier will meet it: the word-minimum filter (an answer that stops
short of the prompt's word minimum is excluded) applies to the fixed-task reasoning cells and not to the
k = 36 heavy-task rung, whose answers are puzzle solutions rather than summaries (paper Appendix D.5.5;
`corpus_summary.py`, filter F3). The heavy rung enters only Table 1.

## 5. Open items for independent verification

1. A named third party runs V1 – V4 from the Zenodo deposit on a clean machine and signs a short reproduction
   statement (template in §6). Candidates: a university energy-informatics group; or an ISAE 3000 limited-assurance
   engagement on the methodology.
2. A metered anchor: prefill and decode power on an open-weight model on rented accelerators, to test the
   1/TPS scaling law and the pre-fill ratio (paper Appendix G).
3. Independent re-derivation of the parameter CSVs from their sources (V5) by someone who did not compile them.

## 6. Reproduction statement (template)

> I, [name, affiliation], obtained the v1.0.0 deposit (Zenodo DOI [ ]) on [date] and, on a machine not
> previously used for this work, ran steps V1 – V4 of VERIFICATION.md. [V1 – V3 reproduced exactly / with the
> following differences: … ]. [V4: n cells compared, n agree.] I spot-checked [k] parameter rows against their
> cited sources (V5) and found [no / the following] discrepancies. I received [no payment / payment of … ] for
> this work and have no financial interest in InferenceCarbon Ltd.
