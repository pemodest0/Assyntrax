import json, csv
from pathlib import Path

P = Path('results/today_forecast_eval/calibration/calibration_results.json')
OUT = Path('results/today_forecast_eval/calibration/summary_by_symbol.csv')
data = json.loads(P.read_text(encoding='utf8'))
rows = []
for sym, v in data.items():
    b = v.get('best')
    if not b:
        continue
    rows.append([sym, b.get('pl'), b.get('ph'), b.get('low'), b.get('high'), b.get('mae_coh'), b.get('dir_coh'), b.get('mae_dif'), b.get('dir_dif'), b.get('n_coh'), b.get('n_dif')])
rows.sort(key=lambda r: (-(r[6] if r[6] is not None else -9999), r[5]))
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', newline='', encoding='utf8') as f:
    w = csv.writer(f)
    w.writerow(['symbol','p_low','p_high','low','high','mae_coh','dir_coh','mae_dif','dir_dif','n_coh','n_dif'])
    w.writerows(rows)
print('wrote', OUT)
