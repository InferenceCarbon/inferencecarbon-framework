# Verification — InferenceCarbon framework v1.0.0

What can be checked, how, what has been checked, and by whom. The aim is that an assurance provider can
follow the chain from raw record to published cell with no step that depends on the authors' word.

## 1. The chain of evidence

```
frozen corpus (zip, SHA-256)             data/InferenceCarbon_corpus_frozen_20260822.zip
      │  corpus_summary.py  (filters F1–F6, seeds 20260822 / 20260823)
      ▼
Corpus / Bootstrap / RatioEnvelopes sheets   data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx
      │  workbook formulas (Assumptions → GridIntensity → Table7 → Table8 → C_Low/C_High → Table9)
      ▼
tables_7_to_10.py --out                  reproduce/expected/tables/*.csv
      │  tables_7_to_10.py --paper       cell-by-cell comparison with the .docx
      ▼
paper Tables 1, 3–5, 7–11, B1, C1–C3
```

Each arrow is a script or a formula in the deposit. The parameter inputs that are typed into the workbook
(anchor, PUE, PQPC, grid intensities, provider Scope 2 figures, routing shares) are listed with their source
and access date in `parameters/*.csv`, and every one is a public document a verifier can open.

## 2. Verification steps

| Step | Command | Expected result |
|---|---|---|
| V1 Corpus integrity | `shasum -a 256 -c data/InferenceCarbon_corpus_frozen_20260822.sha256` | OK |
| V2 Corpus → workbook inputs | `python reproduce/corpus_summary.py --corpus data/InferenceCarbon_corpus_frozen_20260822.zip --out out/cs --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx` | Corpus sheet agreement report; bootstrap bands within 0.01; ratio envelopes within 0.015 (see §3 for the known differences) |
| V3 Workbook → tables | `python reproduce/tables_7_to_10.py --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx --out out/tables && diff -r out/tables reproduce/expected/tables` | no differences |
| V4 Tables → paper | `python reproduce/tables_7_to_10.py --workbook ... --paper <paper .docx>` | every compared cell agrees at displayed precision |
| V5 Parameters → sources | open each `source_url` in `parameters/*.csv` and confirm the value | manual |
| V6 Workbook formulas | `python reproduce/formula_audit.py --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx` | "undeclared numeric constants: 0", exit status 0 |

## 3. Verification record

### 3.1 Author-side reproduction, 11 September 2026 (Claude Fable 5.1 at the author's direction — not independent)

- V1: OK.
- V2: Corpus sheet — 628 of 644 cells agree exactly. The 16 that do not are recorded in §4 below; none
  enters a published figure. Bootstrap bands (184 values): maximum absolute difference 0.0098, mean 0.0009 —
  the residual is the random-number stream, not the method. Ratio envelopes (33 values): maximum difference
  0.014 on ratios of 1.2 – 3.5.
- V3: expected outputs committed from this run.
- V4: paper v1.0.0 (release candidate): Tables 7, 8, 9, B1, C1 and C2 — 1,971 numeric cells
  compared, 1,971 agree.

### 3.1a Author-side regeneration, 12 September 2026 (Claude Fable 5.1 at the author's direction — not independent)

The corpus → workbook step was made mechanical before release: `corpus_summary.py --write-workbook` now writes
the Corpus, TableB1, Bootstrap, RatioEnvelopes and T1_GPT55_Grid input cells, and the deposited workbook is the
recalculated output of that procedure (see reproduce/README.md, "Regenerating the workbook").

- V2: 644 of 644 Corpus cells agree; bootstrap bands and ratio envelopes agree to 0.0000 (the deposited script
  is now the source of the values, so the random-stream residual of 3.1 is gone). The 16 discrepancies of §4
  items 1 – 4 are thereby corrected.
- Consequence for the paper: the deposited script's random stream differs from the lost original's, so 236
  bound cells moved at the last displayed decimal (76 in Table 9, 21 in Table C1, 139 in Table C2; largest
  relative change ≈ 0.5%), and Table 10's bounds, Table C3's ranges and Table 11a's medians moved
  correspondingly. Central values are untouched. The paper's tables were regenerated from the workbook
  (tracked changes, 12 September) and V4 re-run: Tables 7, 8, 9, B1, C1, C2 — 1,971 cells compared,
  1,971 agree.
- V6: `formula_audit.py` run for the first time. It found the Table 11a summary rows on the Pinching sheet to
  be typed constants produced by a script not in the deposit (`build_wb46.py`); one of them was wrong (the
  "Anchor and PQPC together" narrowing was typed as 7.19×; 11.14 ÷ 1.43 = 7.79×). The rows are now live
  MEDIAN/MIN/MAX formulas over the flagged reasoning-variant rows. Audit result: 3,944 formulas, 461 declared
  inputs, 0 undeclared constants.
- Every cell changed in this round carries a cyan fill in the workbook and is listed with its old and new
  value on the `Changes_v1.0.0` sheet (390 cells: Pinching 268, Bootstrap 76, Corpus 22, RatioEnvelopes 18,
  T1_GPT55_Grid 4, Assumptions 2).

### 3.2 Independent reproduction

**None yet.** The framework is not independently verified. See the open items below.

## 4. Discrepancies found in the 11 September workbook, and their status

Items 1 – 4 were found by V2 on 11 September and corrected on 12 September by regenerating the workbook from
the deposited script (§3.1a); item 5 is corrected in the paper by tracked change. They are kept here as the record.

1. **Corpus sheet, column "R heavy (k=36)"**: 14 rows hold integers (33, 35, 37, 38, 39, 43, 44, 18) that are
   not medians; they appear to be stray counts. The heavy-task rung enters only Table 1 (GPT-5.5 family,
   which is correct) and no other table. `corpus_summary.py` gives the correct medians.
2. **Heavy rung and the word-minimum filter**: the 10 September 2026 filter (an answer that stops short of the
   prompt's word minimum is excluded) was applied to the fixed-task reasoning cells but not to the k = 36
   heavy cells. Applied to the heavy cells it would leave GPT-5.5 (minimal) with one record instead of twelve
   (Table 1's 5.82). `corpus_summary.py` documents the exemption; the paper's Appendix B.4 should state it.
3. **gpt-5.4 (low), n for the short cell**: workbook 37, corpus 36 — one record excluded by the word-minimum
   filter; the median is unchanged.
4. **R floor for gpt-5 (medium) and gpt-5.4 (high)**: workbook 1.59 / 1.20, corpus 1.63 / 1.23. Floors enter
   only the superseded mean±SD band columns, not the bootstrap bands.
5. **Table 3 arithmetic**: the AWS contribution is shown as 37.5 in the paper (11.7% × 319 = 37.3), giving a
   total of 353.1 against 352.7 computed. The headline 353 is unaffected.

## 5. Open items for independent verification

1. A named third party runs V1 – V4 from the Zenodo deposit on a clean machine and signs a short reproduction
   statement (template in §6). Candidates: a university energy-informatics group; or an ISAE 3000 limited-assurance
   engagement on the methodology.
2. A metered anchor: prefill and decode power on an open-weight model on rented accelerators, to test the
   1/TPS scaling law and the pre-fill ratio (paper Appendix G).
3. ~~A formulas audit script for V6.~~ Done 12 September (`reproduce/formula_audit.py`).
4. Independent re-derivation of the parameter CSVs from their sources (V5) by someone who did not compile them.

## 6. Reproduction statement (template)

> I, [name, affiliation], obtained the v1.0.0 deposit (Zenodo DOI [ ]) on [date] and, on a machine not
> previously used for this work, ran steps V1 – V4 of VERIFICATION.md. [V1 – V3 reproduced exactly / with the
> following differences: … ]. [V4: n cells compared, n agree.] I spot-checked [k] parameter rows against their
> cited sources (V5) and found [no / the following] discrepancies. I received [no payment / payment of … ] for
> this work and have no financial interest in InferenceCarbon Ltd.
