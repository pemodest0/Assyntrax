#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument('--csv', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()

csv = Path(args.csv)
out = Path(args.out)
df = pd.read_csv(csv)
# Detect date column
date_col = None
for c in ['date', 'DATE', 'Date', 'observation_date', 'OBSERVATION_DATE']:
	if c in df.columns:
		date_col = c
		break
if date_col is None:
	raise SystemExit('Arquivo CSV não contém coluna de data reconhecível')
df[date_col] = pd.to_datetime(df[date_col])
df = df.set_index(date_col)
# Detect price/value column (any numeric column except date)
value_col = None
for c in df.columns:
	if pd.api.types.is_numeric_dtype(df[c]):
		value_col = c
		break
if value_col is None:
	raise SystemExit('Arquivo CSV não contém coluna numérica para plotagem')
plt.figure(figsize=(12,4))
plt.plot(df.index, df[value_col])
plt.title(csv.stem)
plt.tight_layout()
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out)
plt.close()
print('Plot salvo:', out)
