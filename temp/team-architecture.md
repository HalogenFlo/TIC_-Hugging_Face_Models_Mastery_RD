# Team architecture

> Three teams, one project — and a closed loop connecting them.

```
                ┌──────────────────────────────────────────────────┐
                │                                                  │
                ▼                                                  │
   ┌──────────────────────┐         golden.jsonl       ┌──────────────────────┐
   │  Team 1: ADK agents  │ ────── (training data) ───▶│  Team 3: Unsloth FT  │
   │                      │                            │                      │
   │  agents/<name>/      │                            │  finetuning/<name>/  │
   │    agent.yaml        │                            │    train.yaml        │
   │    eval/golden.jsonl │                            │    adapter weights   │
   └──────────────────────┘                            └──────────┬───────────┘
              ▲                                                   │
              │                                                   │ LoRA / merged weights
              │ model: alias                                      ▼
              │                                        ┌──────────────────────┐
              │                                        │  Team 2: vLLM/TGI    │
              │     OpenAI-compatible endpoint URL     │   Self-hosted        │
              └──────────────────────────────────────  │   GPU/TPU serving    │
                                                       │                      │
                                                       │  serving/<model>/    │
                                                       │    config.yaml       │
                                                       │    deployment.yaml   │
                                                       └──────────────────────┘
```

**The flywheel:** Team 1's golden sets become Team 3's training data → Team 3's fine-tuned weights load into Team 2's serving stack → Team 2's endpoint becomes a `model:` value in Team 1's agents → loop closes, agents get measurably better against their own goldens.

## What each team owns

### Team 1 — ADK agent builders
| | |
|---|---|
| **Owns** | `agents/<name>/agent.yaml`, `eval/golden.jsonl`, `tools.py`, prompts, workflow design |
| **Consumes from Team 2** | Endpoint URL of self-hosted models (becomes `model:` aliases) |
| **Produces for Team 3** | Golden eval sets — these ARE the training-data candidates |

### Team 2 — Model serving
| | |
|---|---|
| **Owns** | `serving/<model>/` configs — vLLM/TGI Docker setup, k8s manifests, scaling config, OpenAI-compat endpoint |
| **Consumes from Team 3** | LoRA adapters or merged weights to load into the serving runtime |
| **Produces for Team 1** | OpenAI-compatible endpoint URL + a documented model-name registry |

### Team 3 — Fine-tuning with Unsloth
| | |
|---|---|
| **Owns** | `finetuning/<name>/` — Unsloth training scripts, hyperparameters, training data prep, adapter outputs |
| **Consumes from Team 1** | `agents/<name>/eval/golden.jsonl` — converted to SFT format (chat-template messages) |
| **Produces for Team 2** | LoRA adapter (`.safetensors`) or merged model weights, plus a small README of the training run (base model, hyperparams, eval delta) |

## Use cases (and the datasets behind them)

Six concrete use cases. Each one is a real HuggingFace dataset, permissively licensed, with a clear primary metric. Teams pick a use case to work on as a triple: Team 1 builds the agent, Team 2 hosts the model, Team 3 fine-tunes a base model on the same dataset.

| Use case | Dataset | License | Rows | Primary metric |
|---|---|---|---|---|
| Chatbot / multi-turn dialogue | [`OpenAssistant/oasst1`](https://huggingface.co/datasets/OpenAssistant/oasst1) | Apache-2.0 | 84,400 | `schema_validity` |
| Text classification (intent) | [`PolyAI/banking77`](https://huggingface.co/datasets/PolyAI/banking77) | CC-BY-4.0 | 10,003 | `exact_match` |
| Structured data extraction | [`GEM/viggo`](https://huggingface.co/datasets/GEM/viggo) | CC-BY-SA-4.0 | 5,103 | `field_f1` |
| Document parsing (image → markdown) | [`getomni-ai/ocr-benchmark`](https://huggingface.co/datasets/getomni-ai/ocr-benchmark) | MIT | 1,000 | `schema_validity` (text-similarity v2) |
| Multi-source Q&A | [`hotpotqa/hotpot_qa`](https://huggingface.co/datasets/hotpotqa/hotpot_qa) | CC-BY-SA-4.0 | 90,447 | `exact_match` |
| Triage / escalation | [`OxAISH-AL-LLM/wiki_toxic`](https://huggingface.co/datasets/OxAISH-AL-LLM/wiki_toxic) | CC0-1.0 | 127,656 | `exact_match` (boolean) |

All licenses are commercial-safe (no "research only" / "non-commercial" datasets in the lineup).

### Worked example: closed loop on banking-intent classification

```
1.  Team 1 (week 1)
    Builds agents/banking77/ → schemas, prompt, golden set (150 cases from the
    PolyAI/banking77 test split). Eval against gemini-3.1-flash-lite as a
    baseline → score=0.74 exact_match.

2.  Team 1 → Team 3
    Hands off agents/banking77/eval/golden.jsonl + the prompt to Team 3.

3.  Team 3 (week 2)
    Converts to SFT format. Fine-tunes Qwen 2.5-7B with Unsloth (LoRA, ~2h
    on a single A100). Saves adapter to s3://team3/banking-v1.

4.  Team 3 → Team 2
    Hands off the LoRA adapter + base-model name (Qwen 2.5-7B) + a one-page
    training README (hyperparams, train/val loss, held-out eval delta).

5.  Team 2 (week 2)
    Adds qwen-banking-ft to model_registry.yaml. Spins up vLLM with the
    LoRA loader pointing at s3://team3/banking-v1. Exposes the OpenAI-
    compatible endpoint at https://team2.internal/v1.

6.  Team 2 → Team 1
    Tells Team 1: "qwen-banking-ft is live; swap your model: alias."

7.  Team 1 (week 3)
    Edits agent.yaml: model: qwen-banking-ft. Re-runs the eval. Score
    delta vs baseline: +0.11 (0.74 → 0.85). Costs drop from $0.30/1k
    requests on Pro-preview to $0.04/1k requests on the self-hosted 7B.
    Team 1 commits the new prompt_history entry. Loop closes.
```

The same flywheel runs for all six use cases. Each team picks 1–2 use cases and runs them end-to-end; aim for one full loop per use case per quarter.

## Concrete contracts between teams

The interfaces matter more than the implementations. Lock these down early:

### A. Model-name registry (Team 2 + Team 3 agree)

Single file in the repo: `model_registry.yaml`:

```yaml
# Names available to Team 1's agent.yaml `model:` field
models:
  # Hosted Gemini (always available)
  gemini-3.1-flash-lite:  { provider: gemini, endpoint: api.gemini.com }
  gemini-3.1-pro-preview: { provider: gemini, endpoint: api.gemini.com }

  # Self-hosted by Team 2
  qwen-2.5-72b:    { provider: openai, endpoint: https://team2.internal/v1, model: qwen-2.5-72b }
  llama-3.3-70b:   { provider: openai, endpoint: https://team2.internal/v1, model: llama-3.3-70b }

  # Fine-tuned by Team 3, served by Team 2
  qwen-banking-ft:     { provider: openai, endpoint: https://team2.internal/v1, model: qwen-banking-v1, base: qwen-2.5-72b, adapter: s3://team3/banking-v1 }
  llama-parsebench-ft: { provider: openai, endpoint: https://team2.internal/v1, model: llama-parsebench-v1, base: llama-3.3-70b }
```

Team 1 just writes `model: qwen-banking-ft` in their YAML. The registry is the source of truth for who's allowed to refer to what.

### B. Eval-set → training-data converter (Team 1 → Team 3)

One script: `scripts/golden_to_sft.py <agent> > sft.jsonl`. Transforms:

```jsonl
{"id":"b77-0001","input":{"text":"How do I link my card?"},"expected":{"intent":"card_linking"}}
```

into Unsloth's chat format:

```jsonl
{"messages":[{"role":"system","content":"<the agent's prompt>"},{"role":"user","content":"How do I link my card?"},{"role":"assistant","content":"{\"intent\":\"card_linking\"}"}]}
```

Team 3 trains on this. Single source of truth for what "good output" looks like.

### C. Repo layout

Monorepo (recommended for a small org):

```
agents/                # Team 1 — what we have today
serving/               # Team 2 — Dockerfiles, vLLM configs, k8s manifests, runbooks
finetuning/            # Team 3 — Unsloth training scripts, adapter outputs, eval reports
model_registry.yaml    # The contract all 3 teams read
scripts/
  golden_to_sft.py     # Team 1 → Team 3 data flow
  publish_adapter.sh   # Team 3 → Team 2 weight handoff
```

Split into separate repos later if any team grows a lot of infra-specific code.

## Three concrete decisions to make before any team starts building

| Decision | Options | Tradeoff |
|---|---|---|
| **Serving stack (Team 2)** | vLLM, TGI, sglang, NVIDIA Triton, llama.cpp server | vLLM is the default for GPU; needs JAX/MaxText for TPU. sglang is fastest for batched. |
| **Base models for fine-tuning (Team 3)** | Qwen 2.5, Llama 3.3, Gemma 3, Mistral 3 | Qwen 2.5 has the best Apache-2.0 instruction tuning. Llama is strongest at 70B. Gemma is Google-blessed. |
| **Adapter format (Team 2 ↔ Team 3)** | LoRA (`.safetensors`, swappable) vs merged weights (`.safetensors`, full model) | LoRA: switch adapters per request, save memory. Merged: simpler serving, no LoRA loader needed. |

