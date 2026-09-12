#!/usr/bin/env python3
"""formula_audit.py — VERIFICATION.md step V6: no typed constants outside the declared input cells.

Rule: on the calculation sheets (Table7, Table8, C_Low, C_High, Table9, GridIntensity, ShapeCorrection,
Assumptions, Bootstrap, RatioEnvelopes, Levers, Pinching) every numeric cell must be either a formula or a
declared input. Declared inputs are (a) cells in BLUE font (FF0000FF) — the workbook's own convention — or
(b) cells on the corpus-derived sheets (Corpus, TableB1, T1_GPT55_Grid) and the Bootstrap / RatioEnvelopes
value columns, which corpus_summary.py --write-workbook regenerates. Anything else is reported.

  python formula_audit.py --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx
Exit status 1 if any undeclared constant is found.
"""
import argparse, sys, openpyxl
BLUE = 'FF0000FF'
CALC = ['Assumptions', 'GridIntensity', 'Table7', 'Table8', 'C_Low', 'C_High', 'Table9', 'ShapeCorrection', 'Levers', 'Pinching', 'Bootstrap', 'RatioEnvelopes']
REGEN = {'Bootstrap': {3, 4, 5, 8, 9, 10, 11, 12}, 'RatioEnvelopes': {10, 12, 13}}   # columns corpus_summary.py writes
ap = argparse.ArgumentParser(); ap.add_argument('--workbook', required=True); a = ap.parse_args()
wb = openpyxl.load_workbook(a.workbook)
bad = []; formulas = 0; inputs = 0
for name in CALC:
    if name not in wb.sheetnames: continue
    ws = wb[name]
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if v is None or isinstance(v, str) and not v.startswith('='): continue
            if isinstance(v, str) or type(v).__name__ == 'ArrayFormula': formulas += 1; continue
            if isinstance(v, bool): continue
            col = c.font.color.rgb if c.font and c.font.color and isinstance(c.font.color.rgb, str) else None
            if col == BLUE or c.column in REGEN.get(name, set()): inputs += 1; continue
            # header/row-number style ints in label columns are not constants of the chain
            if c.column == 1: continue
            bad.append((name, c.coordinate, v))
print(f'formulas: {formulas}; declared inputs: {inputs}; undeclared numeric constants: {len(bad)}')
for b in bad: print('  ', *b)
sys.exit(1 if bad else 0)
