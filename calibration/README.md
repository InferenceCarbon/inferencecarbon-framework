# Tokenizer calibration

This is the single canonical statement of the tokenizer basis for the whole
series. Every brief refers back to here rather than restating it.

## The two bases

- **o200k_base** — OpenAI's tokenizer, used as the common cross-provider
  yardstick. Per-token figures on this basis are comparable across providers
  but do not match any non-OpenAI provider's own token counts. The Gemini
  brief's figures are on this basis.
- **Calibrated (native)** — per-token figures expressed in the provider's own
  tokenizer, obtained by calibrating o200k_base counts against native counts
  over the calibration corpus in `runs/`. The Claude brief is scheduled on
  this basis.

A reader comparing a calibrated-basis brief with an o200k_base brief must
convert one to the other using the calibration ratios in `runs/` before the
numbers are comparable. Which basis a figure is on is stated in the brief
that publishes it; what each basis *means* is stated only here.

## Measured ratios

One calibration run is published in `runs/`: Anthropic, measured 23 July
2026 via the provider's token-count endpoint against o200k_base on identical
prose (`tokenizer_calibration_anthropic.json`). Current-generation Claude
models tokenize the same visible text at **k ~= 1.64x** the o200k_base count
(per-model slopes 1.63-1.65, small per-model intercepts, recorded in the
file). OpenAI models need no calibration (native counts are o200k_base).
Google, Mistral and DeepSeek calibrations will be added when their briefs
are prepared; until then their figures are published on the o200k_base
basis only.
