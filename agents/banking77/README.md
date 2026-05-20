
# banking77

A highly accurate intent classification agent designed to analyze incoming customer queries related to banking operations and classify them into exactly one of 77 pre-defined intent categories. It serves as a classic classification task using the ADK framework and the Gemini 2.5 Flash model.

## What it does

Input:

```json
{
  "text": "I lost my credit card, what should I do?"
}
```

Sample call (via Restate):

```bash
make task INPUT='{"text":"I lost my credit card, what should I do?"}' KEY=t-001 \
  ENDPOINT=http://localhost:8080/Banking77Agent/t-001/run
```

Sample output:

```json
"lost_or_stolen_card"
```

## How the pieces fit

```
agents/banking77/
├── service.yaml    Restate wiring — VirtualObject "Banking77Agent",
│                   handler "run", input schemas: Banking77Request
├── agent.yaml      ADK LlmAgent (gemini-2.5-flash). System instructions containing
│                   the exhaustive list of 77 valid banking intents.
├── schemas.py      Banking77Request(text: str)
└── eval/           ADK evalset directory (currently empty, ready for test cases)
```

## Required env vars

| Var | Why |
|-----|-----|
| `GEMINI_API_KEY` | Forwarded to ADK for model authentication and inference. |
