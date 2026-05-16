# Operational Memory Classifier

A GBrain-backed classifier for AI/API execution failures.

## Why

The hardest part about building agents is not getting the model to act.

It is understanding what happened when execution breaks.

When an agent fails at an API boundary, teams usually have to guess whether to:
- retry
- wait
- shrink
- fallback
- or stop

This project classifies the failure and retrieves matching operational precedent from GBrain.

## What it does

Input:

```text
429 handler ignored Retry-After and retried inside the provider cooldown window.
```

Output:

- classification: WAIT
- reason: provider cooldown / rate-limit signal present
- fix shape: honor Retry-After before local backoff
- matched precedent from real operational receipts

## Included tooling

### `classify_with_memory.py`

Classifies operational failures against known operational precedent.

### `query_operational_memory.py`

Retrieves related operational precedent by shared execution structure instead of keywords.

### `search_yc_public_json.py`

Exploratory utility for searching YC public company/repo data and surfacing related operational patterns.

## Example operational patterns

- Retry-After ignored under concurrency
- Hidden retry amplification
- Retry loops without elapsed bounds
- Double-retry fanout across layers
- Provider cooldown violations

## Prior work

The operational receipt corpus comes from prior research in `Pitstop-Truth`.

## Built during hackathon

This repository contains the GBrain-backed operational-memory workflow built during the hackathon:

- execution failure classifier
- operational precedent retrieval
- compact stage renderer
- evidence-backed example findings
- exploratory operational search tooling

## Demo

```bash
python3 scripts/classify_with_memory.py examples/gstack_retry_after.txt
```

## Core idea

This is not just classification.

It is classification grounded in confirmed operational precedent from systems that already hit the same wall.

Execution failures should become reusable precedent instead of isolated tribal knowledge.