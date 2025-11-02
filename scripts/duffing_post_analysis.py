#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, confusion_matrix

OUT = Path('results/duffing_validation')


def main():
    p = OUT / 'duffing_sweep.csv'
    df = pd.read_csv(p)
    # prepare features
    X = df[['entropy', 'alpha', 'n_clusters']].fillna(0).values
    # target: lyap-based chaotic
    y = (df['gt_lyap'] == 'Chaotic').astype(int).values
    clf = DecisionTreeClassifier(max_depth=3, random_state=0)
    scores = cross_val_score(clf, X, y, cv=4, scoring='accuracy')
    clf.fit(X, y)
    preds = clf.predict(X)
    print('Cross-val accuracy (4-fold):', scores)
    print('Train accuracy:', (preds==y).mean())
    print('\nClassification report:')
    print(classification_report(y, preds))
    print('\nConfusion matrix:')
    print(confusion_matrix(y, preds))
    print('\nDecision rule (tree):')
    print(export_text(clf, feature_names=['entropy','alpha','n_clusters']))
    df['pred_lyap'] = preds
    df.to_csv(OUT / 'duffing_sweep_with_preds.csv', index=False)
    print('Saved augmented CSV to', OUT / 'duffing_sweep_with_preds.csv')


if __name__ == '__main__':
    main()
