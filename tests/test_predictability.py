from pathlib import Path
import json


def test_attractor_and_predictability_files_exist():
    base = Path('C:/Users/Pedro Henrique/Desktop/A-firma/website/assets/spa_energy')
    attractor = base / 'attractor_daily_Sudeste_Centro-Oeste.json'
    predictability = base / 'predictability_daily_Sudeste_Centro-Oeste.json'

    assert attractor.exists(), 'attractor json missing'
    assert predictability.exists(), 'predictability json missing'

    data = json.loads(attractor.read_text(encoding='utf-8'))
    assert isinstance(data, list)
    assert len(data) > 0
    assert all('x' in p and 'y' in p and 'z' in p for p in data[:5])

    pred = json.loads(predictability.read_text(encoding='utf-8'))
    assert 'h' in pred and 'mape' in pred
    assert len(pred['h']) > 0
    assert len(pred['h']) == len(pred['mape'])
