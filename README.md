# bluelotus-engine

**Deterministic BlueLotus V3 research engine** — governance gates, contradiction clerk, NITE-PEI Bayesian thesis updates, and SLICDO institutional learning.

This is the **sanitized public research edition**. It deliberately excludes:

- GitHub Pages publishing (`bluelotus_publisher.py`)
- Telegram push notifications
- LLM agent council (`run_v3_grand_cycle`)
- Broker write access and private portfolio identifiers

> Research only. No advice. No orders. `CIO_ONLY_MANUAL`.

---

## Install


## Install from GitHub release (no PyPI account needed)

```bash
pip install https://github.com/sohweekian/bluelotus-engine/releases/download/v3.0.0/bluelotus_engine-3.0.0-py3-none-any.whl
```

PyPI publish (`pip install bluelotus-engine`) — see `PYPI_SETUP.md` in the release staging folder when ready.

```bash
pip install bluelotus-engine
# or if console script not on PATH:
python -m bluelotus_engine.cli --help
```

Or from source:

```bash
git clone https://github.com/sohweekian/bluelotus-engine.git
cd bluelotus-engine
pip install -e ".[dev]"
```

---

## Quick start

```bash
mkdir my-bluelotus-lab && cd my-bluelotus-lab
bluelotus init-workspace
# edit .env if needed
bluelotus pipeline --once --dry-run
bluelotus clerk
bluelotus governance-gate
```

The `init-workspace` command copies a **synthetic demo dataset** — no real positions, no API keys.

---

## CLI

| Command | What it does |
|---------|----------------|
| `bluelotus init-workspace` | Create `.env`, folders, sample `dataset_raw.json` |
| `bluelotus pipeline --once` | Research pipeline (governance → report → clerk → NITE-PEI → SLICDO) |
| `bluelotus clerk` | Deterministic Zone A contradiction map cycle |
| `bluelotus governance-gate` | Run governance gate on current dataset |
| `bluelotus nite-pei` | Bayesian thesis probability update |
| `bluelotus slicdo` | Institutional learning cycle (claims → proposals) |
| `bluelotus validate` | Post-generation output validation |

---

## Architecture (research edition)

```text
dataset_raw.json
    → governance gate + regression tests
    → research report generator (TXT / XLSX / DOCX)
    → deterministic clerk (Zone A — no LLM)
    → NITE-PEI (Bayesian thesis + CKRI)
    → SLICDO learning spine
```

Pipeline config: `config/v3_pipeline_research.yaml`

---

## Why deterministic?

We removed LLM agents from production after live field evaluation: temporal blindness, partial-read hallucination, and non-reproducible outputs are disqualifying for governed capital intelligence.

Full narrative: [bluelotus-engine-docs](https://github.com/sohweekian/bluelotus-engine-docs) · [DETERMINISTIC_TRANSITION](https://github.com/sohweekian/bluelotus-research/blob/main/DETERMINISTIC_TRANSITION.md)

---

## Bring your own data

Replace `data/frontend/dataset_raw.json` with your own export matching `schemas/dataset_raw.schema.json`. The engine does **not** ship live broker fetchers in the public edition.

---

## License

MIT — see `LICENSE` and `DISCLAIMER.md`.
