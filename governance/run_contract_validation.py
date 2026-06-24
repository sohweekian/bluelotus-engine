"""Pipeline step: validate dataset_raw and delivery JSON contracts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governance.contract_validation import run_all_contract_validations
from llm_clients.config_loader import project_root


def main() -> int:
    result = run_all_contract_validations(project_root())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
