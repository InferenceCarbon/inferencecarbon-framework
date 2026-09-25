#!/usr/bin/env python3
"""formula_audit.py — VERIFICATION.md step V6: no typed constants outside the declared input cells.

Rule: on the calculation sheets (Table 6, Table 7, C_Low, C_High, Table 8, Grid Intensity Data, Shape Correction,
Assumptions, Bootstrap, Ratio Envelopes, Table 8 - Log Widths, Pinching) every numeric cell must be either a formula or a
declared input. Declared inputs are (a) the typed parameters listed cell by cell in declared_inputs.json
(each has a source row in parameters/ or a source note beside it in the workbook) or (b) cells on the
corpus-derived sheets (Corpus, Table B1, Table 1) and the Bootstrap / Ratio Envelopes value columns,
which corpus_summary.py --write-workbook regenerates. Anything else is reported.

  python formula_audit.py --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx
Exit status 1 if any undeclared constant is found.
"""
import argparse, json, os, sys, openpyxl
DECLARED = {k: set(v) for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'declared_inputs.json'))).items()}
CALC = ['Assumptions', 'Grid Intensity Data', 'Table 6', 'Table 7', 'C_Low', 'C_High', 'Table 8', 'Shape Correction', 'Table 8 - Log Widths', 'Pinching', 'Bootstrap', 'Ratio Envelopes']
REGEN = {'Bootstrap': {3, 4, 5, 8, 9, 10, 11, 12}, 'Ratio Envelopes': {10, 12, 13}}   # columns corpus_summary.py writes
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
            if c.coordinate in DECLARED.get(name, set()) or c.column in REGEN.get(name, set()): inputs += 1; continue
            # header/row-number style ints in label columns are not constants of the chain
            if c.column == 1: continue
            bad.append((name, c.coordinate, v))
print(f'formulas: {formulas}; declared inputs: {inputs}; undeclared numeric constants: {len(bad)}')
for b in bad: print('  ', *b)
sys.exit(1 if bad else 0)
