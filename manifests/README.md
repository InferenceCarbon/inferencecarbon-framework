# Tracked-model manifests

One JSON file per provider, compiled from the frozen owned-benchmark corpus
(14,733 request records) and the campaign retirement record. Each entry
carries the model id **exactly as the API names it**, the family, the effort
settings measured, and the campaign dates — so that when a brief has to
explain, say, that its anchor model was retired from the API (as the Gemini
brief does for `gemini-3-pro-preview`, retired 1 June 2026), that
explanation is reconstructable from the manifest rather than from memory.

## Files

| File | Contents |
|---|---|
| `openai.json`, `anthropic.json`, `google.json`, `mistral.json`, `deepseek.json` | Per-provider manifests (schema below) |
| `variant_dates.csv` | The underlying per-(model, effort) first/last measurement dates and request counts, computed from `results/run_*.json` |
| `RETIREMENTS.md` | The retirement/withdrawal evidence record: confirmed retirements, transient flaps, and endpoint incompatibilities, with dates and sources |

## Schema

```json
{
  "provider": "openai",
  "campaign_window": { "start": "2026-06-25", "compiled": "2026-08-07" },
  "models": [
    {
      "model_id": "gpt-5.4",
      "family": "GPT-5.4",
      "effort_settings": ["minimal", "low", "medium", "high", "xhigh"],
      "added": "2026-06-25",
      "retired": null,
      "first_measured": "2026-06-25",
      "last_measured": "2026-08-07",
      "n_requests": 512,
      "n_failed": 3,
      "notes": ""
    }
  ]
}
```

- `model_id` — verbatim API identifier, never a marketing name.
- `effort_settings` — the effort levels with at least one successful owned
  sample (`default` = the provider's single default variant; Anthropic
  models all run default adaptive thinking — no effort ladder exists via
  the compat layer).
- `added` / `retired` — campaign entry date and API retirement date
  (ISO 8601); `retired: null` means still live at compile date. The Gemini
  anchor has `added: null` because it was already retired at campaign
  start; its entry documents the failed-attempt evidence.
- `first_measured` / `last_measured` / `n_requests` / `n_failed` —
  provenance from the corpus, so every date is checkable against the
  deposited `run_*.json` records.

Entries whose `effort_settings` is empty never produced a successful owned
sample; the `notes` field says why (retirement, or the codex-line
responses-endpoint incompatibility — paper limitation 25).

Manifests are regenerated from the corpus, not hand-edited; if a hand edit
is unavoidable, record it in `notes`.
