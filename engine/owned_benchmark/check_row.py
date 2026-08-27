import sys, datetime, openpyxl
path = sys.argv[1]
TODAY = datetime.date.today()
wb = openpyxl.load_workbook(path, data_only=True)
ws = wb[wb.sheetnames[0]]
headers = [c.value for c in ws[1]][1:]
row = None
for r in ws.iter_rows(min_row=2):
    v = r[0].value
    d = v.date() if isinstance(v, datetime.datetime) else v if isinstance(v, datetime.date) else None
    if d is None and v is not None:
        try: d = datetime.datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
        except Exception: d = None
    if d == TODAY: row = r
if row is None:
    print("NO_TODAY_ROW"); sys.exit()
gaps, total = [], 0
for h, c in zip(headers, row[1:]):
    if h is None or str(h).strip()=="" : continue
    total += 1
    v = c.value
    if not (isinstance(v,(int,float)) and v != 0): gaps.append("%s=%r" % (h, v))
print("filled %d of %d" % (total-len(gaps), total))
for g in gaps: print("GAP:", g)
