import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Remove results/_tmp directory.")
    parser.add_argument("--yes", action="store_true", help="Confirm deletion.")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    target = base_dir / "results" / "_tmp"

    if not target.exists():
        print("results/_tmp does not exist.")
        return

    if not args.yes:
        print("Add --yes to confirm deletion.")
        return

    shutil.rmtree(target)
    print("Removed results/_tmp.")


if __name__ == "__main__":
    main()
