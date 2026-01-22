from pathlib import Path
import shutil
import json
import sys

ROOT = Path(__file__).resolve().parent
SIM_DIR = ROOT.parent / "simulacoes_fisica"
SIM_DIR.mkdir(exist_ok=True)

# conservative list of files/dirs to move (physics/simulations/visualization)
TO_MOVE = [
    "scripts/validate_with_duffing.py",
    "scripts/duffing_post_analysis.py",
    "scripts/ehrenfest_urn.py",
    "scripts/run_graph_discovery_physics.py",
    "scripts/hypercube_battery.py",
    "scripts/run_graph_discovery_physics.py",
    "scripts/estudos",
    "visualizacao/streamlit/simulador_qubits_algebras.py",
    "visualizacao/dashboards/app/deformed_schrodinger.py",
    "visualizacao/dashboards/app/crystal_walk.py",
    "visualizacao/dashboards/app/quantum_hypercube_anim.py",
    "visualizacao/dashboards/app/quantum_explorer.py",
    "visualizacao/dashboards/app/ising_interface.py",
    "visualizacao/docs",
    "modelos/gaq",
]

ops = []
for rel in TO_MOVE:
    src = ROOT.parent / rel
    if not src.exists():
        ops.append({"path": str(src), "status": "missing"})
        continue
    # destination: keep relative path under simulacoes_fisica
    dest = SIM_DIR / src.relative_to(ROOT.parent)
    dest_parent = dest.parent
    dest_parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dest))
        ops.append({"path": str(src), "moved_to": str(dest), "status": "moved"})
    except Exception as e:
        ops.append({"path": str(src), "status": "error", "error": str(e)})

log = ROOT.parent / "reorg_proposed.json"
log.write_text(json.dumps({"ops": ops}, indent=2))
print("Reorg complete. See", log)

if __name__ == '__main__':
    pass
