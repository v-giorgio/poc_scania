"""Cross-platform check that key project artifacts are present."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "SPEC.md",
    "README.md",
    "pyproject.toml",
    "docs/setup.md",
    "docs/architecture.md",
    "docs/data-discovery.md",
    "docs/data-dictionary.md",
    "docs/modeling-and-evaluation.md",
    "docs/experiment-results.md",
    "config/data_contract.yaml",
    "notebooks/03_data_preparation/01_ingest_raw.py",
    "notebooks/03_data_preparation/02_silver_transform.py",
    "notebooks/03_data_preparation/03_gold_features.py",
    "src/scania_poc/features.py",
    "src/scania_poc/evaluation.py",
    "tests/unit/test_models.py",
)


def main() -> int:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        print("Estrutura incompleta:")
        for path in missing:
            print(f"  MISSING {path}")
        return 1
    print(f"Estrutura válida: {len(REQUIRED_PATHS)} caminhos conferidos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
