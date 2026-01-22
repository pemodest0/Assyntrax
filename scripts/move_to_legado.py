#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

MOVE_FOLDERS = [
    'agent',
    'analysis',
    'config',
    'core',
    'dados',
    'docs',
    'experiments',
    'modelos',
    'results',
    'results_finance',
    'simulacoes_fisica',
    'visualizacao',
]


def move_folders(base: Path, folders: list[str], target: Path, dry_run: bool = True):
    target.mkdir(parents=True, exist_ok=True)
    for name in folders:
        src = base / name
        if not src.exists():
            print(f"Pulando {name}: não existe")
            continue
        dst = target / name
        if dst.exists():
            print(f"Alvo já existe, pulando: {dst}")
            continue
        print(f"Movendo {src} -> {dst}")
        if not dry_run:
            shutil.move(str(src), str(dst))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Move pastas de projeto para uma pasta legado.')
    parser.add_argument('--base', type=str, default='.', help='Pasta base do repositório')
    parser.add_argument('--target', type=str, default='legado', help='Pasta de destino')
    parser.add_argument('--execute', action='store_true', help='Executa a movimentação (por padrão faz dry-run)')
    args = parser.parse_args()

    base = Path(args.base).resolve()
    target = (base / args.target).resolve()
    print(f'Base: {base}')
    print(f'Target: {target}')
    move_folders(base, MOVE_FOLDERS, target, dry_run=not args.execute)
    if not args.execute:
        print('\nDry-run concluído. Rode com --execute para aplicar as mudanças.')
    else:
        print('\nMovimentação concluída.')
