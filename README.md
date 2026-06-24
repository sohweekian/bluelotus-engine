# bluelotus-engine

**BlueLotus V3 — deterministic research engine (frozen v3.0.0)**

Governance gates · contradiction clerk · Bayesian thesis updates (NITE-PEI) · **Nash / QRE game theory (BGTM-V1)** · institutional learning (SLICDO).

> Research only. No advice. No orders. `CIO_ONLY_MANUAL`.

**Documentation:** [bluelotus-engine-docs](https://github.com/sohweekian/bluelotus-engine-docs) — what it is, who it's for, how to download.

---

## Download

```bash
pip install https://github.com/sohweekian/bluelotus-engine/releases/download/v3.0.0/bluelotus_engine-3.0.0-py3-none-any.whl
```

Release page: https://github.com/sohweekian/bluelotus-engine/releases/tag/v3.0.0

---

## What this software does

| Layer | Function |
|-------|----------|
| **Governance** | Contract validation, approval gate, scenario overlay, regression tests |
| **Reports** | Deterministic TXT / XLSX / DOCX intelligence package |
| **Zone A clerk** | Contradiction map from rules and portfolio math — **no LLM agents** |
| **NITE-PEI** | Bayesian thesis probabilities, CKRI kill-risk, Kelly advisory |
| **BGTM-V1** | Nash Equilibrium · QRE · Correlated Equilibrium · Geo-LR → NITE-PEI |
| **SLICDO** | Claims, resolutions, replay, CIO-gated learning proposals |

**Not included:** GitHub publish, Telegram, broker fetchers, LLM agent council, private portfolio data.

Full explanation: [WHAT_IS_BLUELOTUS.md](https://github.com/sohweekian/bluelotus-engine-docs/blob/main/WHAT_IS_BLUELOTUS.md) · [BGTM game theory](https://github.com/sohweekian/bluelotus-engine-docs/blob/main/BGTM.md)

---

## Who it is for

- Researchers studying governed financial AI
- Developers building on Bayesian thesis / governance patterns
- CIO practitioners studying single-mandate intelligence architecture
- **Not for:** auto-trading, investment advice, or a maintained SaaS product

Details: [WHO_IS_IT_FOR.md](https://github.com/sohweekian/bluelotus-engine-docs/blob/main/WHO_IS_IT_FOR.md)

---

## Quick start

```bash
mkdir bluelotus-lab && cd bluelotus-lab
python -m bluelotus_engine.cli init-workspace
python -m bluelotus_engine.cli pipeline --once --dry-run
python -m bluelotus_engine.cli clerk
```

Uses **synthetic demo data** — no API keys required.

---

## CLI

| Command | What it does |
|---------|----------------|
| `init-workspace` | Create `.env`, folders, sample dataset |
| `pipeline --once` | Governance → report → clerk → NITE-PEI → SLICDO |
| `clerk` | Deterministic Zone A contradiction cycle |
| `governance-gate` | Run governance gate on dataset |
| `nite-pei` | Bayesian thesis update |
| `slicdo` | Institutional learning cycle |
| `validate` | Post-generation output checks |

If `bluelotus` is not on PATH: `python -m bluelotus_engine.cli <command>`

---

## Release status

**Frozen at v3.0.0** — no further software updates planned. Thesis uploads may continue in [bluelotus-research](https://github.com/sohweekian/bluelotus-research). Private production stack remains proprietary.

See [PUBLIC_RELEASE_NOTICE.md](https://github.com/sohweekian/bluelotus-research/blob/main/PUBLIC_RELEASE_NOTICE.md).

---

## License

MIT — see `LICENSE` and `DISCLAIMER.md`.
