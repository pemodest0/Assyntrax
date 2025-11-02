#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import sys
from typing import Iterable, List


DOMAIN_MODULES = {
    "finance": "scripts.run_graph_discovery_finance",
    "logistics": "scripts.run_graph_discovery_logistics",
    "health": "scripts.run_graph_discovery_health",
    "physics": "scripts.run_graph_discovery_physics",
}


def run_domain(domain: str) -> None:
    module_name = DOMAIN_MODULES[domain]
    module = importlib.import_module(module_name)
    if not hasattr(module, "main"):
        raise RuntimeError(f"Módulo {module_name} não expõe função main()")
    module.main()  # type: ignore[call-arg]


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa descoberta de grafos + ingest para domínios específicos."
    )
    parser.add_argument(
        "--domain",
        "-d",
        action="append",
        choices=sorted(DOMAIN_MODULES.keys()),
        help="Domínio para rodar (pode repetir). Se omitido, roda todos.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    domains: List[str]
    if args.domain:
        domains = args.domain
    else:
        domains = sorted(DOMAIN_MODULES.keys())
    for domain in domains:
        print(f"=== Rodando pipeline para {domain} ===")
        run_domain(domain)
        print()


if __name__ == "__main__":
    main()
