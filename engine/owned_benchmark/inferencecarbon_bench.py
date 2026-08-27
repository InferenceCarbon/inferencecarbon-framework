#!/usr/bin/env python3
"""
InferenceCarbon — owned LLM-throughput benchmark (OpenAI GPT models).

Measures inference throughput with our own prompts and the open-source
o200k_base tokenizer, so the resulting data is owned outright and
reproducible. Design choices follow published throughput-benchmarking
practice so the figures sit alongside public series; the paper's section 5.3
sets out the comparison.

It additionally captures what the InferenceCarbon energy model needs and
public trackers do not publish: native (provider) token counts,
reasoning-token counts, and a clean TTFT / decode split.

Methodology choices:
  - workloads by input length (1k / 10k default / 100k), with minimum answer tokens
  - temperature 0, top_p 1
  - streaming; TTFT = first token (reasoning or answer), TTFAT = first answer token
  - output speed measured after the first token
  - token counts standardised with tiktoken o200k_base (for comparability)
  - summarise as P50 across repeats (a single run; persist history for a rolling window)

Deliberate additions (see README):
  - native token counts (usage) recorded alongside o200k_base
  - reasoning_tokens captured from usage where exposed
  - optional higher-concurrency scenario (energy-relevant; public trackers report single and parallel-10)

Usage:
  python inferencecarbon_bench.py discover            # build/update manifest.json from /v1/models
  python inferencecarbon_bench.py run --models gpt-4o-mini --workload 1k --repeats 2
  python inferencecarbon_bench.py run --workload 10k --repeats 8        # full set (costs $$)
  python inferencecarbon_bench.py run --mock --workload 1k              # no API, validates pipeline
"""
import os, sys, json, time, math, argparse, random, statistics, datetime as dt, re
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../InferenceCarbonWorking/owned_benchmark
WORKDIR = Path(os.environ.get("INFERENCECARBON_DIR", HERE.parent))   # .../InferenceCarbonWorking
DESKTOP = WORKDIR.parent                          # .../Desktop
RESULTS = HERE/"results"; RESULTS.mkdir(exist_ok=True)
PROVIDERS_FILE = HERE/"providers.json"
DEFAULT_PRICE = {"in": 5.0, "out": 30.0}   # conservative fallback for unpriced models

# ---- provider plumbing (set_provider mutates these per command) ----
PROVIDER = "openai"
PROV = {}                                          # active provider config
BASE_URL = None; MODELS_URL = "https://api.openai.com/v1/models"
KEY_FILE = WORKDIR/"OpenAIAPIKey.txt"
MANIFEST = HERE/"manifest.json"
TRACKED = HERE/"tracked_models.json"               # curated set the benchmark actually runs
WORKBOOK = DESKTOP/"InferenceCarbon_TokenSec_Daily_OpenAI_Owned.xlsx"   # engine: Latest + Run Log
DAILY_WORKBOOK = DESKTOP/"InferenceCarbon_TokenSec_Daily_Owned.xlsx"    # standalone daily summary (template format)
PRICES_FILE = HERE/"prices.json"
SPEND_STATE = RESULTS/"spend_state.json"

def load_providers():
    try: return json.loads(PROVIDERS_FILE.read_text()).get("providers", {})
    except Exception: return {}

def set_provider(slug):
    """Point all per-provider paths/URLs/keys at <slug> from providers.json. Defaults preserve
       the original single-provider (OpenAI) layout, so provider=openai is byte-for-byte unchanged."""
    global PROVIDER, PROV, BASE_URL, MODELS_URL, KEY_FILE, MANIFEST, TRACKED
    global WORKBOOK, DAILY_WORKBOOK, PRICES_FILE, SPEND_STATE
    provs = load_providers()
    if slug not in provs:
        if slug == "openai": return        # fall back to module defaults
        log(f"provider '{slug}' not in providers.json"); sys.exit(2)
    p = provs[slug]; PROVIDER = slug; PROV = p
    BASE_URL = p.get("base_url")
    MODELS_URL = p.get("models_url", MODELS_URL)
    KEY_FILE = WORKDIR/p.get("key_file", "OpenAIAPIKey.txt")
    MANIFEST = HERE/p.get("manifest_file", "manifest.json")
    TRACKED = HERE/p.get("tracked_file", "tracked_models.json")
    WORKBOOK = DESKTOP/p.get("engine_workbook", "InferenceCarbon_TokenSec_Daily_OpenAI_Owned.xlsx")
    DAILY_WORKBOOK = DESKTOP/p.get("daily_workbook", "InferenceCarbon_TokenSec_Daily_Owned.xlsx")
    PRICES_FILE = HERE/p.get("prices_file", f"prices_{slug}.json" if slug!="openai" else "prices.json")
    SPEND_STATE = RESULTS/p.get("spend_file", "spend_state.json")

def load_prices():
    try: return json.loads(PRICES_FILE.read_text())
    except Exception: return {}
def est_cost(prices, api_model, in_tok, out_tok):
    p = prices.get(api_model, DEFAULT_PRICE)
    return (in_tok or 0)/1e6*p["in"] + (out_tok or 0)/1e6*p["out"]
def load_spend():
    try: return json.loads(SPEND_STATE.read_text())
    except Exception: return {"cumulative_usd": 0.0, "runs": []}
def save_spend(st): SPEND_STATE.write_text(json.dumps(st, indent=2))
def run_tag_default():
    now=dt.datetime.now()
    pre = "" if PROVIDER=="openai" else PROVIDER+"-"     # keep OpenAI tags unprefixed (back-compat)
    return pre+now.strftime("%Y-%m-%d")+("-AM" if now.hour<14 else "-PM")

# (input_token_target, min_answer_tokens)  — standard throughput-benchmark workloads.
# 'short' (100/300) and '1k' (1000/1000) match the framework paper's Table-1
# short/medium query definitions, so owned reasoning multipliers can be
# query-length-conditioned (2026-07-23 revision).
WORKLOADS = {"short": (100, 300), "1k": (1000, 1000), "10k": (10000, 1500), "100k": (100000, 2000)}
EFFORT_LADDER = ["minimal", "low", "medium", "high", "xhigh"]   # candidate; pruned at runtime
EXCLUDE = ("tts","transcribe","realtime","audio","search","image","instruct",
           "embedding","moderation","-16k","chat-latest","-preview")

def log(*a): print(*a, file=sys.stderr, flush=True)

def read_key():
    if not KEY_FILE.exists(): log(f"KEY_MISSING: {KEY_FILE}"); sys.exit(2)
    return KEY_FILE.read_text().strip()

# ---------- tokenizer (o200k_base, the cross-provider standard here) ----------
def get_encoder():
    try:
        import tiktoken
        return tiktoken.get_encoding("o200k_base")
    except Exception as e:
        log(f"tiktoken unavailable ({e}); falling back to ~word count"); return None
ENC = None
def n_tokens(text):
    if ENC: return len(ENC.encode(text or ""))
    return max(1, round(len((text or "").split()) * 1.3))

# ---------- prompt generation (OUR content, sized to the token budget) ----------
# Coherent, benign sentences. Used (shuffled per seed, to defeat prompt caching) to build a
# prompt of the exact target token length. Coherent prose avoids the content filters that some
# providers (e.g. Anthropic Opus) apply to random-word gibberish, which returned empty completions.
_SENTS = [
 "Throughput in large language model inference depends on model size, hardware, and batching.",
 "Engineers measure latency and tokens per second to understand and compare system performance.",
 "The prefill phase processes the input prompt before the model begins generating any output.",
 "During decoding the model emits tokens one at a time, and this stage sets the output speed.",
 "Time to first token captures how long a user waits before a response starts to appear.",
 "Energy use follows from the same dynamics, so careful measurement matters for cost and sustainability.",
 "Reasoning models spend additional compute thinking before they produce a visible answer.",
 "Provider routing, network conditions, and server load can all shift measured throughput.",
 "A reproducible benchmark uses fixed prompt sizes and records results over many repeated runs.",
 "Capacity planning relies on these measurements to estimate how many requests a cluster can serve.",
 "Standardising token counts across providers makes throughput figures easier to compare fairly.",
 "Streaming responses lets a client display partial output while later tokens are still arriving.",
]
def _filler(target_tokens, seed):
    rnd = random.Random(seed); sents=_SENTS[:]; rnd.shuffle(sents)
    out=[]; tot=0; i=0
    while tot < target_tokens:
        s=sents[i % len(sents)]; out.append(s); tot += n_tokens(s); i += 1
    text = " ".join(out)
    if ENC:  # trim to exact budget
        ids = ENC.encode(text)[:target_tokens]; text = ENC.decode(ids)
    return text
def build_prompt(input_target, min_out, seed, prompt_class="summarise"):
    if prompt_class == "reason":
        return build_reasoning_prompt(input_target, min_out, seed)
    if prompt_class == "reason-heavy":
        return build_reasoning_prompt(input_target, min_out, seed, k=36)
    task = ("Read the following notes carefully, then write a detailed, well-structured "
            "explanatory summary of at least %d words, covering the key themes, drawing "
            "comparisons, and noting any tensions. Notes:\n\n" % max(400, min_out//2))
    budget = max(50, input_target - n_tokens(task))
    return task + _filler(budget, seed)

REASON_PROMPT_V = 2   # v2 (2026-07-23): task size FIXED across workloads — see docstring
def build_reasoning_prompt(input_target, min_out, seed, k=12):
    """Reasoning-eliciting prompt class, VERSION 2. v1 scaled the puzzle with the input
    budget (k = budget/25), which confounded task difficulty with prompt length — the two
    axes Table 1 must keep separate. v2 fixes the puzzle at twelve elements at EVERY
    workload; only filler padding (and therefore prefill/context) grows with the budget.
    Difficulty is varied at fixed length by the summarise/reason class split instead.
    prompt_version is recorded per request; v1 hard-task records (23 Jul only) are the
    confounded basis and are analysed separately.

    Second rung (30 Jul): class 'reason-heavy' uses k=36 — a second FIXED reference task,
    also constant across lengths, so task-demand sensitivity is measured on clean bases
    (a 36-element task does not fit the 100-token budget; heavy runs at 1k+ only)."""
    rnd = random.Random(seed)
    nums = [rnd.randint(12, 97) for _ in range(k)]
    task = ("Using the list below: (1) compute the running totals; (2) mark each total "
            "divisible by 3 or by 7; (3) compute the mean of the unmarked totals; "
            "(4) count the pairs from the ORIGINAL list that sum to an even number. "
            f"Show your working and final answers, explaining your method in at least {max(120, min_out//4)} words. "
            f"List: {nums}. Notes:\n\n")
    budget = max(0, input_target - n_tokens(task))
    return task + (_filler(budget, seed) if budget > 50 else "")

def _as_text(x):
    """Coerce a streamed delta field to a string. Some providers (e.g. Mistral) send
       `content` as a list of content parts rather than a plain string."""
    if x is None: return ""
    if isinstance(x, str): return x
    if isinstance(x, list):
        out=[]
        for it in x:
            if isinstance(it, str): out.append(it)
            elif isinstance(it, dict): out.append(it.get("text") or it.get("content") or "")
            else: out.append(getattr(it, "text", "") or "")
        return "".join(out)
    return str(x)

# ---------- think-tag parsing (Mistral/Magistral stream reasoning as visible text) ----------
_THINK_PATTERNS = [(re.compile(r"<think>", re.I), re.compile(r"</think>", re.I)),
                   (re.compile(r"\[THINK\]", re.I), re.compile(r"\[/THINK\]", re.I))]
def _split_think(text):
    """Split streamed content into (visible_text, think_text, first_visible_char_offset).
    Magistral-class models stream reasoning inside think tags within `content`; counting
    that as visible answer inflates throughput by exactly the thinking (the magistral-small
    divergence). An unclosed span (timeout) runs to end-of-text. Returns the
    original text unchanged if no think tags are present."""
    for opat, cpat in _THINK_PATTERNS:
        m = opat.search(text)
        if not m: continue
        segs = []; pos = 0
        while m:
            if m.start() > pos: segs.append((pos, m.start(), False))
            mc = cpat.search(text, m.end())
            if mc:
                segs.append((m.end(), mc.start(), True)); pos = mc.end()
            else:
                segs.append((m.end(), len(text), True)); pos = len(text); break
            m = opat.search(text, pos)
        if pos < len(text): segs.append((pos, len(text), False))
        visible = "".join(text[a:b] for a, b, t in segs if not t)
        think   = "".join(text[a:b] for a, b, t in segs if t)
        first_vis = None
        for a, b, t in segs:
            if not t and text[a:b].strip(): first_vis = a; break
        return visible, think, first_vis
    return text, "", None

# ---------- usage extraction, hardened (2026-07-23) ----------
def _uget(u, name):
    if u is None: return None
    return u.get(name) if isinstance(u, dict) else getattr(u, name, None)

def _usage_reasoning(usage):
    """First non-None reasoning-token count across the field shapes providers use.
    (OpenAI: completion_tokens_details.reasoning_tokens; Gemini compat: thoughts_token_count
    variants; some compat layers flatten to usage.reasoning_tokens.)"""
    det = _uget(usage, "completion_tokens_details")
    for src, v in (("completion_tokens_details.reasoning_tokens", _uget(det, "reasoning_tokens")),
                   ("usage.reasoning_tokens", _uget(usage, "reasoning_tokens")),
                   ("usage.thoughts_token_count", _uget(usage, "thoughts_token_count")),
                   ("usage.thoughtsTokenCount", _uget(usage, "thoughtsTokenCount"))):
        if v is not None:
            try: return int(v), src
            except Exception: pass
    return None, None

def _usage_raw(usage):
    """Verbatim usage payload for the JSON corpus — the cheapest future-proofing against
    provider field renames (the Anthropic 4-6 capture gap would have been diagnosable
    from this)."""
    if usage is None: return None
    for attr in ("model_dump", "dict"):
        f = getattr(usage, attr, None)
        if callable(f):
            try: return f()
            except Exception: pass
    if isinstance(usage, dict): return usage
    try:
        return json.loads(json.dumps(usage, default=lambda o: getattr(o, "__dict__", str(o))))
    except Exception:
        return str(usage)

# ---------- one streamed request, fully instrumented ----------
def benchmark_once(client, api_model, effort, prompt, min_out, mock=False, max_output=None,
                   request_timeout=25, thinking=False, effort_style="openai",
                   thinking_budgets=None, reasoning_headroom=4000):
    """Returns a dict of measurements for a single request (or a synthetic one in mock mode).

    2026-07-23 revision:
      - `thinking` marks variants that think by DEFAULT (Gemini/Anthropic/DeepSeek and the
        magistral family) so they get reasoning headroom above the visible-answer cap.
        Previously effort=None implied non-thinking, which silently truncated default
        thinkers to cap-minus-thinking visible tokens (the gemini-3.5-flash anomaly).
      - `effort_style`: 'openai' -> reasoning_effort param; 'anthropic-thinking' ->
        extra_body thinking budgets (minimal = thinking off); 'none' -> no effort param.
      - think-tag text is split out of the visible stream (Magistral), TTFAT corrected to
        the first genuinely visible token, and reasoning tokens estimated from the best
        available source with provenance recorded.
      - resolved model id, system fingerprint, and the raw usage payload are recorded
        ('-latest' alias pinning; field-rename forensics).
    """
    rec = {"api_model": api_model, "effort": effort, "ok": False, "error": None}
    in_tok_o200k = n_tokens(prompt)
    rec["input_tokens_o200k"] = in_tok_o200k
    wants_reasoning = bool(thinking) or (effort not in (None, "minimal", "none"))
    if max_output:
        max_out = max_output + (reasoning_headroom if wants_reasoning else 0)
    else:
        max_out = min_out + (reasoning_headroom if wants_reasoning else 256)
    rec["max_output_effective"] = max_out
    if mock:
        rnd = random.Random(hash((api_model, effort, len(prompt))) & 0xffffffff)
        base = rnd.uniform(40, 260)
        out_native = min_out + rnd.randint(0, 200)
        reasoning = rnd.randint(800, 2600) if wants_reasoning else 0
        ttft = rnd.uniform(0.2, 1.2) + (reasoning/base if reasoning else 0)
        gen_time = out_native / base
        rec.update(ok=True, ttft_s=round(ttft,4), ttfat_s=round(ttft,4),
                   e2e_s=round(ttft+gen_time,4),
                   output_tokens_native=out_native, reasoning_tokens=reasoning,
                   reasoning_tokens_est=reasoning, reasoning_source="mock",
                   output_tokens_o200k=int(out_native*1.02),
                   output_tps_native=round(out_native/gen_time,2),
                   output_tps_o200k=round(out_native*1.02/gen_time,2),
                   itl_ms=round(1000*gen_time/max(1,out_native),2),
                   resolved_model=api_model, min_answer_met=True)
        return rec
    # ---- real call ----
    from openai import OpenAI  # imported lazily
    messages=[{"role":"user","content":prompt}]
    def attempt(extra):
        kw = dict(model=api_model, messages=messages, stream=True,
                  stream_options={"include_usage": True})
        kw.update(extra)
        return client.chat.completions.create(**kw)
    # build param set with graceful fallback (reasoning models reject temp/top_p/effort variously)
    extras = dict(temperature=0, top_p=1, max_completion_tokens=max_out)
    if effort and effort not in ("none",):
        if effort_style == "anthropic-thinking":
            if effort == "minimal":
                # Claude 4.6+/Fable think ADAPTIVELY BY DEFAULT (probe 2026-07-23: no thinking
                # param still produced ~515 hidden tokens) — the R=1 baseline needs an explicit off.
                extras["extra_body"] = {"thinking": {"type": "disabled"}}
            else:
                bud = int((thinking_budgets or {}).get(effort, 8192))
                extras["extra_body"] = {"thinking": {"type": "enabled", "budget_tokens": bud}}
                extras.pop("temperature", None); extras.pop("top_p", None)  # thinking requires default temp
        elif effort_style != "none":
            extras["reasoning_effort"] = effort
    stream=None; last_err=None
    for _ in range(6):
        try:
            t0=time.perf_counter(); stream=attempt(extras); break
        except Exception as e:
            last_err=str(e); msg=last_err.lower()
            if "thinking" in msg and "extra_body" in extras:
                extras.pop("extra_body"); rec["thinking_param_rejected"]=True; continue
            # per-model output-token ceiling (2026-08-18): the 100k reasoning headroom
            # exceeds some models' max (e.g. claude-haiku-4-5 caps at 64000). Parse the
            # provider's stated maximum from the error and clamp, rather than failing.
            # allowed ceiling = the LARGEST token-count below what we just requested
            # (excludes the HTTP status '400' and the requested value itself; a dated
            # model id like 20251001 is out of the token range and ignored)
            if ("output tokens" in msg or "max_tokens" in msg):
                req=max([extras.get(k,0) for k in ("max_completion_tokens","max_tokens")] or [0])
                nums=[int(n) for n in re.findall(r"\b(\d{3,8})\b", msg)
                      if 1000<=int(n)<=1_000_000 and (not req or int(n)<req)]
                if nums:
                    cap=max(nums)
                    for k in ("max_completion_tokens","max_tokens"):
                        if k in extras and extras[k]>cap: extras[k]=cap
                    rec["max_tokens_clamped"]=cap; continue
            for p in ("reasoning_effort","temperature","top_p","max_completion_tokens"):
                if p in msg and p in extras:
                    if p=="max_completion_tokens": extras["max_tokens"]=extras.pop("max_completion_tokens")
                    else: extras.pop(p, None)
                    break
            else:
                break
    if stream is None:
        rec["error"]=f"request failed: {last_err}"; return rec
    ttft=ttfat=None; ans_chunks=[]; ans_text=[]; usage=None
    resolved=None; fingerprint=None; cum=0; reason_stream=[]
    try:
        for chunk in stream:
            now=time.perf_counter()
            if request_timeout and now-t0 > request_timeout:
                rec["timed_out"]=True; break
            if getattr(chunk,"usage",None): usage=chunk.usage
            if resolved is None: resolved=getattr(chunk,"model",None) or None
            if fingerprint is None: fingerprint=getattr(chunk,"system_fingerprint",None)
            if not getattr(chunk,"choices",None): continue
            d=chunk.choices[0].delta
            r=_as_text(getattr(d,"reasoning_content",None) or getattr(d,"reasoning",None)
                       or getattr(d,"thinking",None))
            c=_as_text(getattr(d,"content",None))
            if ttft is None and (r or c): ttft=now
            if r: reason_stream.append(r)
            if c:
                if ttfat is None: ttfat=now
                ans_chunks.append((now, cum, cum+len(c))); cum+=len(c); ans_text.append(c)
    except Exception as e:
        rec["error"]=f"stream error: {e}"
    t_end=time.perf_counter()
    text="".join(ans_text)
    if ttft is None:
        # error path now records timing (2026-08-16): four fable-5 "no tokens" failures
        # were indistinguishable between a 10-minute censoring and an instant empty
        # stream because this branch skipped the elapsed fields
        rec["error"]=rec.get("error") or "no tokens"
        rec["e2e_s"]=round(t_end-t0,2); rec["timed_out"]=bool(rec.get("timed_out"))
        return rec
    # ---- think-tag split (Magistral-class): visible answer vs streamed thinking ----
    visible, think_txt, first_vis = _split_think(text)
    think_detected = bool(think_txt)
    if think_detected and first_vis is not None:
        for tnow, a, b in ans_chunks:
            if b > first_vis: ttfat = tnow; break
    out_o200k = n_tokens(visible)
    think_tokens_o200k = n_tokens(think_txt) if think_detected else None
    reasoning_stream_o200k = n_tokens("".join(reason_stream)) if reason_stream else None
    # ---- usage extraction, all shapes ----
    out_native   = _uget(usage, "completion_tokens")
    prompt_native= _uget(usage, "prompt_tokens")
    total_native = _uget(usage, "total_tokens")
    reasoning, rsrc = _usage_reasoning(usage)
    hidden_usage_delta = None
    if None not in (total_native, prompt_native, out_native) and total_native > prompt_native + out_native + 2:
        hidden_usage_delta = total_native - prompt_native - out_native   # Gemini: thoughts outside completion
    hidden_native_delta = None; tok_k = None
    if out_native and out_o200k:
        cal=_tok_calibration()
        if cal:
            tok_k=(cal.get("models",{}).get(api_model) or {}).get("k") or cal.get("k")
        if tok_k:
            expected = tok_k*out_o200k                                   # calibrated same-text native count
            if out_native > expected*1.02:
                hidden_native_delta = round(out_native - expected)       # thinking, tokenizer share removed
        elif out_native > out_o200k * 1.05:
            hidden_native_delta = out_native - out_o200k                 # uncalibrated fallback
    reasoning_est, rsrc_est = reasoning, rsrc
    if reasoning_est is None and reasoning_stream_o200k:
        reasoning_est, rsrc_est = reasoning_stream_o200k, "stream.reasoning_content(o200k)"
    if reasoning_est is None and think_tokens_o200k:
        reasoning_est, rsrc_est = think_tokens_o200k, "think-tags(o200k)"
    if reasoning_est is None and hidden_usage_delta:
        reasoning_est, rsrc_est = hidden_usage_delta, "usage.total-minus-parts"
    if reasoning_est is None and hidden_native_delta:
        reasoning_est, rsrc_est = hidden_native_delta, ("native-minus-k*o200k(calibrated)" if tok_k else "native-minus-o200k")
    # ---- rates: visible tokens over the visible window (measured after first token; after
    # first VISIBLE token when thinking streamed in-band) ----
    gen_window = max(1e-6, t_end - ttft)
    vis_window = max(1e-6, t_end - (ttfat or ttft)) if think_detected else gen_window
    denom_native = out_native if out_native else out_o200k
    rec.update(ok=True,
        ttft_s=round(ttft-t0,4), ttfat_s=round((ttfat or ttft)-t0,4), e2e_s=round(t_end-t0,4),
        output_tokens_native=out_native, output_tokens_o200k=out_o200k,
        reasoning_tokens=reasoning,
        reasoning_tokens_est=reasoning_est, reasoning_source=rsrc_est,
        think_tokens_o200k=think_tokens_o200k, think_detected=think_detected or None,
        think_time_s=round((ttfat-ttft),4) if (think_detected and ttfat and ttft and ttfat>ttft) else None,
        hidden_usage_delta=hidden_usage_delta, hidden_native_delta=hidden_native_delta,
        tokenizer_k=tok_k,
        output_tps_native=round(denom_native/gen_window,2),
        output_tps_o200k=round(out_o200k/vis_window,2),
        itl_ms=round(1000*(t_end-(ttfat or ttft))/max(1,len(ans_chunks)-1),2) if len(ans_chunks)>1 else None,
        resolved_model=resolved, system_fingerprint=fingerprint,
        usage_raw=_usage_raw(usage), usage_missing=(usage is None) or None,
        min_answer_met=bool(out_o200k >= 0.5*min_out) if not rec.get("timed_out") else None,
        used_params={k:extras[k] for k in extras if k not in ("model","messages")})
    return rec

# ---------- discovery / manifest ----------
def fetch_openai_model_ids(mock=False):
    if mock:
        return ["gpt-4o","gpt-4o-mini","gpt-4.1","gpt-4.1-mini","gpt-5","gpt-5-mini","gpt-5-nano",
                "gpt-5.4","gpt-5.4-mini","gpt-5.4-nano","gpt-5.5","gpt-5.5-pro","gpt-5.3-codex"]
    import urllib.request
    key=read_key()
    if PROV.get("auth")=="x-api-key":          # Anthropic: x-api-key + version, not Bearer
        headers={"x-api-key":key, "anthropic-version":PROV.get("anthropic_version","2023-06-01")}
    else:
        headers={"Authorization":f"Bearer {key}"}
    req=urllib.request.Request(MODELS_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        data=json.load(r)
    ids=[m["id"] for m in data.get("data", data.get("models", []))]
    return [i.split("/",1)[1] if i.startswith("models/") else i for i in ids]   # strip Google 'models/' prefix

def family_version(mid):
    m=re.match(r"gpt-(\d+)(?:\.(\d+))?", mid)
    if not m: return None
    return float(f"{m.group(1)}.{m.group(2) or 0}")

def is_chat_gpt(mid):
    return mid.startswith("gpt-") and not any(x in mid for x in EXCLUDE) \
           and not re.search(r"-\d{4}-\d{2}-\d{2}$", mid)   # drop dated snapshots; keep aliases

def build_manifest(ids):
    """Map OpenAI ids -> benchmark entries. Reasoning bases expand across the effort ladder."""
    entries=[]
    bases=[i for i in ids if is_chat_gpt(i)]
    for mid in sorted(bases):
        fv=family_version(mid)
        reasoning = fv is not None and fv>=5 and not mid.endswith("-pro") and "codex" not in mid
        if reasoning:
            for eff in EFFORT_LADDER:
                entries.append({"label": f"{mid} ({eff})", "api_model": mid,
                                "reasoning_effort": eff, "family": fv, "verified": False})
        else:
            entries.append({"label": mid, "api_model": mid,
                            "reasoning_effort": None, "family": fv, "verified": False})
    return entries

# ---------- curated tracked list ----------
DEFAULT_EFFORTS = ["minimal","low","medium","high","xhigh"]
SEED_TRACKED = {
    "efforts": DEFAULT_EFFORTS,
    "exclude_substrings": ["-pro","codex"],
    "models": [
        {"api_model":"gpt-4o-mini","reasoning":False},
        {"api_model":"gpt-5","reasoning":True},
        {"api_model":"gpt-5.2","reasoning":True},
        {"api_model":"gpt-5.4","reasoning":True},
        {"api_model":"gpt-5.4-mini","reasoning":True},
        {"api_model":"gpt-5.4-nano","reasoning":True},
        {"api_model":"gpt-5.5","reasoning":True},
    ],
}
def load_tracked():
    if TRACKED.exists():
        try: return json.loads(TRACKED.read_text())
        except Exception as e: log(f"{TRACKED.name} unreadable ({e}); using seed")
    if PROVIDER=="openai": return dict(SEED_TRACKED)
    return {"provider":PROVIDER, "efforts":PROV.get("efforts",[]), "models":[]}

def tracked_entries(cfg):
    """Expand the curated list into benchmark entries. Reasoning models with a non-empty
       'efforts' list are broken out across those efforts; everything else is one variant.
       Per-model overrides (2026-07-23): 'efforts' (list), 'keep_default' (also run the
       default no-effort variant, preserving series continuity when a ladder is added),
       'repeats' (per-fire sample count, e.g. anchor models), 'thinking' (thinks by
       default — grants reasoning headroom)."""
    efforts_default = cfg.get("efforts") or []
    out=[]
    for m in cfg.get("models", []):
        api=m["api_model"]; fv=family_version(api)
        extra={k:m[k] for k in ("thinking","repeats") if k in m}
        effs = m.get("efforts", efforts_default)
        if m.get("reasoning") and effs:
            if m.get("keep_default"):
                out.append({"label":api,"api_model":api,
                            "reasoning_effort":None,"family":fv,"verified":False,**extra})
            for eff in effs:
                out.append({"label":f"{api} ({eff})","api_model":api,
                            "reasoning_effort":eff,"family":fv,"verified":False,**extra})
        else:
            out.append({"label":api,"api_model":api,
                        "reasoning_effort":None,"family":fv,"verified":False,**extra})
    return out

SNAPSHOT_RE=re.compile(r"-(\d{4}-\d{2}-\d{2}|\d{8}|\d{6}|\d{4})$")   # drop dated snapshots (YYYY-MM-DD / YYYYMMDD / YYYYMM / YYMM)
def update_families_tracked(ids):
    """Discovery for non-OpenAI providers: pick frontier chat models by seed_families,
       dropping excluded ids and dated snapshots. New clean ids are reported as candidates;
       they are auto-added unless the tracked file is 'locked' (hand-curated), in which case
       they are only reported so a human can confirm — provider model lists are alias-noisy."""
    fams=PROV.get("seed_families",[]); excl=PROV.get("exclude",[])
    sel=[i for i in sorted(set(ids))
         if any(f in i for f in fams) and not any(x in i for x in excl)
         and not SNAPSHOT_RE.search(i)]
    cfg = load_tracked()
    cfg.setdefault("provider", PROVIDER); cfg.setdefault("efforts", PROV.get("efforts",[]))
    have={m["api_model"] for m in cfg.get("models",[])}
    cand=[i for i in sel if i not in have]
    if cfg.get("locked"):
        if cand: log(f"[{PROVIDER}] new frontier ids (locked list, NOT auto-added): "+", ".join(cand))
        return [], len(cfg.get("models",[])), cand
    for i in cand:
        cfg.setdefault("models",[]).append({"api_model":i,"reasoning":False})
    TRACKED.write_text(json.dumps(cfg,indent=2))
    if cand: log(f"[{PROVIDER}] newly tracked: "+", ".join(cand))
    return cand, len(cfg.get("models",[])), []

def update_tracked(bases):
    """Auto-append NEW major families (fv strictly above current max tracked, e.g. gpt-5.6/gpt-6)
       and their mini/nano/codex siblings. Never adds -pro / codex-max or legacy (<= current max)."""
    cfg=load_tracked()
    if not TRACKED.exists(): TRACKED.write_text(json.dumps(cfg,indent=2))
    tracked={m["api_model"] for m in cfg["models"]}
    excl=cfg.get("exclude_substrings",["-pro","codex-max"])
    max_fv=max([family_version(m["api_model"]) or 0 for m in cfg["models"]] or [0])
    added=[]
    for b in sorted(bases):
        if b in tracked: continue
        fv=family_version(b)
        if fv is None or fv<=max_fv: continue
        if any(x in b for x in excl): continue
        cfg["models"].append({"api_model":b,"reasoning":fv>=5}); added.append(b)
    if added:
        TRACKED.write_text(json.dumps(cfg,indent=2))
        log("NEW tracked major variants: "+", ".join(added))
    return added

def cmd_discover(args):
    set_provider(args.provider)
    ids=fetch_openai_model_ids(mock=args.mock)
    if PROV.get("discovery")=="families":      # non-OpenAI providers
        MANIFEST.write_text(json.dumps({"generated":dt.datetime.now().isoformat(timespec="seconds"),
                                        "provider":PROVIDER,"model_ids":sorted(set(ids))}, indent=2))
        added,total,candidates=update_families_tracked(ids)
        log(f"[{PROVIDER}] discovered {len(set(ids))} ids; tracking {total}")
        print(json.dumps({"provider":PROVIDER,"discovered_ids":len(set(ids)),
                          "tracked":total,"newly_tracked":added,"new_candidates":candidates}, indent=2))
        return
    # ---- OpenAI: curated major-version rule (unchanged) ----
    new_manifest=build_manifest(ids)
    old=[]
    if MANIFEST.exists():
        old=json.loads(MANIFEST.read_text()).get("entries",[])
    old_models={e["api_model"] for e in old}
    new_models={e["api_model"] for e in new_manifest}
    added=sorted(new_models - old_models)
    removed=sorted(old_models - new_models)
    # preserve 'verified' flags from old
    vmap={(e["api_model"],e.get("reasoning_effort")):e.get("verified",False) for e in old}
    for e in new_manifest:
        e["verified"]=vmap.get((e["api_model"],e["reasoning_effort"]), e["verified"])
    MANIFEST.write_text(json.dumps({"generated": dt.datetime.now().isoformat(timespec="seconds"),
                                    "source":"openai /v1/models", "entries": new_manifest}, indent=2))
    log(f"manifest: {len(new_manifest)} entries across {len(new_models)} base models")
    if added:   log("NEW models on /v1/models: "+", ".join(added))
    if removed: log("removed/absent since last run: "+", ".join(removed))
    newly_tracked = update_tracked(new_models)   # auto-add new MAJOR families to the curated list
    print(json.dumps({"entries":len(new_manifest),"base_models":len(new_models),
                      "new":added,"removed":removed,"newly_tracked":newly_tracked}, indent=2))

# ---------- run ----------
def _censored_labels(workload, prompt_class, min_attempts=2):
    """Labels with >= min_attempts recorded CENSORED attempts (timed out with no usage
    payload, or 'no tokens') for this provider+workload+prompt_class. Rider fires use
    fresh daily run-tags, so without this the same censored variants would burn paid
    attempts every fire; instead they are skipped and written to a deferred file that
    HeavyThinkers.command reads. Only consulted when request_timeout < 60 — local
    long-timeout runs measure these labels normally."""
    from collections import defaultdict
    cnt=defaultdict(int)
    pslug = "" if PROVIDER=="openai" else PROVIDER+"_"
    # scan window: last 14 days only (2026-08-07) — full-corpus scans grew past the 45s
    # shell budget and were themselves causing the kills they were counting
    cutoff=(dt.datetime.now()-dt.timedelta(days=14)).strftime("%Y%m%d")
    def _recent(fp):
        import re as _re
        m=_re.search(r"(\d{8})T", fp.name); return bool(m) and m.group(1)>=cutoff
    for fp in (f for f in RESULTS.glob(f"run_{pslug}*_{workload}.json") if _recent(f)):
        try: d=json.loads(fp.read_text())
        except Exception: continue
        if d.get("mock") or d.get("provider","openai")!=PROVIDER: continue
        for r in d.get("records",[]):
            if r.get("prompt_class","summarise")!=prompt_class: continue
            censored=(r.get("ok") and r.get("timed_out") and r.get("reasoning_tokens") is None
                      and r.get("usage_missing")) or \
                     (not r.get("ok") and "no tokens" in str(r.get("error") or ""))
            if censored: cnt[r.get("label")]+=1
    # calls killed at the 45s shell leave NO record — they are counted via orphaned
    # in-flight markers accumulated in the killed_* file (see cmd_run)
    kf=RESULTS/f"killed_{PROVIDER}_{workload}_{prompt_class}.json"
    try:
        for l,c in json.loads(kf.read_text()).items(): cnt[l]+=int(c)
    except Exception: pass
    # SUCCESS-AWARE (2026-08-07): shell kills also strike FAST variants (startup + corpus
    # scan overhead), so raw kill counts eventually condemned the whole roster and the
    # sandbox fires went no-op. A variant with >=3 usable records at this cell is provably
    # collectable — never skip it regardless of kill count.
    ok_n=defaultdict(int)
    for fp in (f for f in RESULTS.glob(f"run_{pslug}*_{workload}.json") if _recent(f)):
        try: d=json.loads(fp.read_text())
        except Exception: continue
        if d.get("mock") or d.get("provider","openai")!=PROVIDER: continue
        for r in d.get("records",[]):
            if r.get("prompt_class","summarise")==prompt_class and r.get("ok") and r.get("reasoning_tokens") is not None:
                ok_n[r.get("label")]+=1
    cen={l for l,c in cnt.items() if c>=min_attempts and ok_n.get(l,0)<3}
    f=RESULTS/f"deferred_{PROVIDER}_{workload}_{prompt_class}.json"
    try: f.write_text(json.dumps(sorted(cen), indent=1))
    except Exception: pass
    return cen

def _timeout_capped_labels(min_rate=0.5, min_n=4):
    """Labels whose corpus history (this provider, non-mock) shows >= min_rate timed-out
    requests — the variants whose throughput/reasoning measurements are censored by the
    scheduled task's 40s timeout and need uncensored long-timeout runs."""
    from collections import defaultdict
    tot=defaultdict(int); cap=defaultdict(int)
    for fp in RESULTS.glob("run_*.json"):
        try: d=json.loads(fp.read_text())
        except Exception: continue
        if d.get("mock") or d.get("provider","openai")!=PROVIDER: continue
        for r in d.get("records",[]):
            if not r.get("ok"): continue
            l=r.get("label"); tot[l]+=1
            if r.get("timed_out"): cap[l]+=1
    return {l for l in tot if tot[l]>=min_n and cap[l]/tot[l]>=min_rate}

def pct(xs,p):
    xs=[x for x in xs if x is not None]
    if not xs: return None
    xs=sorted(xs); k=(len(xs)-1)*p/100; f=math.floor(k); c=math.ceil(k)
    return round(xs[f] if f==c else xs[f]+(xs[c]-xs[f])*(k-f),3)

def cmd_run(args):
    set_provider(args.provider)
    global ENC; ENC=get_encoder()
    if getattr(args, "jitter", 0):
        time.sleep(random.uniform(0, args.jitter))   # de-synchronise fixed fire times (Tier 3)
    in_target,min_out = WORKLOADS[args.workload]
    if args.models:
        # ad-hoc override: pull the requested ids/labels from the full manifest
        man = json.loads(MANIFEST.read_text())["entries"] if MANIFEST.exists() else build_manifest(
            fetch_openai_model_ids(mock=True))
        want=set(args.models.split(","))
        entries=[e for e in man if e["api_model"] in want or e["label"] in want]
    else:
        # default: only the curated tracked list, expanded across all efforts
        entries = tracked_entries(load_tracked())
    if args.exclude:
        pats=[x.strip() for x in args.exclude.split(",") if x.strip()]
        entries=[e for e in entries if not any(x in e["api_model"] for x in pats)]
    # REASONING-CLASS OPT-OUT (2026-08-17): some variants refuse the reasoning prompt at
    # their safety layer (native-API stop_reason 'refusal', categories 'cyber' and
    # 'reasoning_extraction' — i.e. the prompt's shape reads as prompt-injection / hidden-
    # reasoning-extraction / distillation tradecraft). Re-firing a refused prompt has no
    # data value and registers a flagged event against the account each time, so such
    # variants are excluded from the reason/reason-heavy classes ONLY. They remain in the
    # summarise (throughput) series, which they answer normally. Provider models are
    # matched by substring; the refusal is documented in the corpus and Appendix B.
    REASON_OPT_OUT = ["claude-fable-5"]
    if args.prompt_class.startswith("reason"):
        before=len(entries)
        entries=[e for e in entries if not any(x in e["api_model"] for x in REASON_OPT_OUT)]
        if len(entries)<before:
            log(f"reasoning opt-out: skipped {before-len(entries)} variant(s) that refuse the reasoning prompt ({', '.join(REASON_OPT_OUT)})")
    # reason-class only: a timed-out summarise request is still a valid partial TPS
    # sample, but a timed-out reason-class request loses usage = no reasoning count.
    if args.prompt_class.startswith("reason") and args.request_timeout and args.request_timeout < 60 and not args.mock:
        cen=_censored_labels(args.workload, args.prompt_class)
        skip=[e["label"] for e in entries if e["label"] in cen]
        if skip:
            entries=[e for e in entries if e["label"] not in cen]
            log(f"censored-skip ({len(skip)} labels -> HeavyThinkers): "+", ".join(sorted(skip)))
    if getattr(args, "timeout_capped_only", False):
        # Keep only variants whose corpus history shows >=50% timed-out requests — the
        # censored heavy thinkers. Pair with a long --request-timeout OUTSIDE the 45s
        # scheduled shell (see engine/InferenceCarbon_HeavyThinkers.command).
        capped=_timeout_capped_labels()
        entries=[e for e in entries if e["label"] in capped]
        log(f"timeout-capped-only: {len(entries)} variants selected: "+", ".join(sorted(e['label'] for e in entries)))
    if args.skip_efforts:
        sk=set(x.strip() for x in args.skip_efforts.split(","))
        entries=[e for e in entries if e["reasoning_effort"] not in sk]
    if args.limit: entries=entries[:args.limit]
    client=None
    if not args.mock:
        from openai import OpenAI
        ckw=dict(api_key=read_key(), timeout=args.request_timeout)
        if BASE_URL: ckw["base_url"]=BASE_URL          # OpenAI-compatible endpoint for non-OpenAI providers
        if PROV.get("default_headers"): ckw["default_headers"]=PROV["default_headers"]
        client=OpenAI(**ckw)
    # Budget defaults from providers.json 'budget_cap' so AD-HOC runs are capped too —
    # the 4-week campaign ended $16 over the OpenAI cap because --budget was opt-in.
    prices=load_prices(); spend=load_spend()
    budget=args.budget if args.budget is not None else PROV.get("budget_cap")
    stop_budget=False
    run_id=dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    tag=args.run_tag or run_tag_default()
    prog_file=RESULTS/f"progress_{PROVIDER}_{tag}_{args.workload}.json"   # per-provider AND per-workload:
    # shared --run-tag across providers must not merge queues, and short/1k/10k fires must not mask one another
    # Progress now counts REPEATS per label (2026-07-23b): a multi-repeat item (e.g. the
    # anchor model's 5 repeats) is split across calls instead of running atomically —
    # 5 x ~25s can never fit the platform's 45s shell cap, which stalled the 23 Jul
    # rider fire on the gemini-2.5 family. Legacy list-format progress = fully done.
    try:
        _d=json.loads(prog_file.read_text()).get("done",[])
        done=_d if isinstance(_d,dict) else {l:10**6 for l in _d}
    except Exception: done={}
    def _wanted(e): return int(e.get("repeats") or args.repeats)
    entries=[e for e in entries if int(done.get(e["label"],0)) < _wanted(e)]
    t_start=time.time()
    all_recs=[]; summary=[]; time_up=False
    thinking_fams = PROV.get("thinking_families", [])
    def _thinks(e):
        if e.get("thinking") is not None: return bool(e["thinking"])
        if PROV.get("default_thinking"): return True
        return any(f in e["api_model"] for f in thinking_fams)
    # Incremental persistence (2026-07-23b): the run json is rewritten after EVERY record,
    # so a call killed at the 45s shell cap during workbook writes (or a long request)
    # keeps its paid-for measurement. The Run Log's historical 'Models: 0' entries were
    # this failure mode: request + startup + corpus-wide daily rebuild > 44s, all lost.
    pslug = "" if PROVIDER=="openai" else PROVIDER+"_"
    jpath=RESULTS/f"run_{pslug}{run_id}_{args.workload}{'_mock' if args.mock else ''}.json"
    # In-flight marker (2026-07-23d): written before each request, cleared after the
    # record persists. A marker still present at the START of a later call means that
    # call was shell-killed mid-request (recordless, but billed) — counted into the
    # killed_* file, which _censored_labels folds into the deferral decision.
    kills_f=RESULTS/f"killed_{PROVIDER}_{args.workload}_{args.prompt_class}.json"
    intent_f=RESULTS/f"inflight_{PROVIDER}_{args.workload}_{args.prompt_class}.json"
    if not args.mock:
        try:
            if intent_f.exists():
                orphan=json.loads(intent_f.read_text()).get("label")
                if orphan:
                    k=json.loads(kills_f.read_text()) if kills_f.exists() else {}
                    k[orphan]=int(k.get(orphan,0))+1; kills_f.write_text(json.dumps(k,indent=1))
                    log(f"orphaned in-flight marker: {orphan} (killed-call count +1)")
                intent_f.unlink()
        except Exception: pass
    def _persist():
        jpath.write_text(json.dumps({"run_id":run_id,"provider":PROVIDER,"workload":args.workload,
            "scenario":"single","repeats":args.repeats,"mock":args.mock,
            "generated":dt.datetime.now().isoformat(timespec="seconds"),
            "summary":summary,"records":all_recs}, indent=2))
    for e in entries:
        if stop_budget or time_up: break
        recs=[]
        n_repeats=_wanted(e); already=int(done.get(e["label"],0))
        for i in range(already, n_repeats):
            if args.time_budget and (all_recs or i>already) and time.time()-t_start > args.time_budget:
                time_up=True
                log(f"  TIME_BUDGET {args.time_budget}s reached; pausing (resume next call)"); break
            if budget and not args.mock:
                worst=est_cost(prices, e["api_model"], in_target, (args.max_output or (min_out+256)) + args.reasoning_headroom)
                if spend["cumulative_usd"]+worst > budget:
                    log(f"  BUDGET_STOP: est ${spend['cumulative_usd']:.2f} + ${worst:.2f} would exceed ${budget}")
                    stop_budget=True; break
            seed=random.randint(0,10**9)
            prompt=build_prompt(in_target, min_out, seed, prompt_class=args.prompt_class)
            # seed recorded (2026-07-23c): the paper claims any run is reconstructible from
            # its seed — that claim was hollow while seeds went unrecorded. Records before
            # this date lack the field; acknowledge in the data note.
            if not args.mock:
                try: intent_f.write_text(json.dumps({"label":e["label"],"ts":dt.datetime.now().isoformat(timespec="seconds")}))
                except Exception: pass
            rec=benchmark_once(client, e["api_model"], e["reasoning_effort"], prompt, min_out,
                               mock=args.mock, max_output=args.max_output, request_timeout=args.request_timeout,
                               thinking=_thinks(e), effort_style=PROV.get("effort_style","openai"),
                               thinking_budgets=PROV.get("thinking_budgets"),
                               reasoning_headroom=args.reasoning_headroom)
            rec.update(label=e["label"], workload=args.workload, repeat=i, run_id=run_id,
                       prompt_class=args.prompt_class, prompt_seed=seed,
                       prompt_version=(REASON_PROMPT_V if args.prompt_class.startswith("reason") else 1),
                       puzzle_k=(36 if args.prompt_class=="reason-heavy" else (12 if args.prompt_class=="reason" else None)))
            if rec["ok"] and not args.mock:
                rc=est_cost(prices, e["api_model"], rec.get("input_tokens_o200k"), rec.get("output_tokens_native") or rec.get("output_tokens_o200k"))
                spend["cumulative_usd"]=round(spend["cumulative_usd"]+rc,4); rec["est_cost_usd"]=round(rc,4)
                save_spend(spend)
            if rec.get("error") and any(x in str(rec["error"]).lower() for x in ("insufficient_quota","billing","quota","429")):
                log("  QUOTA/BILLING limit hit — stopping run"); stop_budget=True
            recs.append(rec); all_recs.append(rec)
            _persist()                                     # measurement safe from this point
            if not args.mock:
                try: intent_f.unlink()                     # record persisted; not a killed call
                except Exception: pass
            done[e["label"]]=already+len(recs)
            prog_file.write_text(json.dumps({"tag":tag,"done":done}))
            if stop_budget: break
            ok = "ok" if rec["ok"] else f"ERR {rec.get('error')}"
            log(f"  {e['label']:34s} [{i+1}/{n_repeats}] {ok}"
                + (f"  {rec.get('output_tps_native')} tok/s  ttft={rec.get('ttft_s')}s" if rec['ok'] else ""))
        good=[r for r in recs if r["ok"]]
        if good:
            resolved=[r.get("resolved_model") for r in good if r.get("resolved_model")]
            summary.append({
              "label":e["label"], "api_model":e["api_model"], "effort":e["reasoning_effort"],
              "workload":args.workload, "n":len(good),
              "p50_output_tps_native":pct([r["output_tps_native"] for r in good],50),
              "p50_output_tps_o200k":pct([r["output_tps_o200k"] for r in good],50),
              "p50_ttft_s":pct([r["ttft_s"] for r in good],50),
              "p50_ttfat_s":pct([r["ttfat_s"] for r in good],50),
              "p50_e2e_s":pct([r["e2e_s"] for r in good],50),
              "median_input_tokens_o200k":pct([r["input_tokens_o200k"] for r in good],50),
              "median_output_tokens_native":pct([r.get("output_tokens_native") for r in good],50),
              "median_reasoning_tokens":pct([r.get("reasoning_tokens") for r in good],50),
              "median_reasoning_tokens_est":pct([r.get("reasoning_tokens_est") for r in good],50),
              "p50_think_time_s":pct([r.get("think_time_s") for r in good],50),
              "resolved_model":(max(set(resolved), key=resolved.count) if resolved else None),
              "n_usage_missing":sum(1 for r in good if r.get("usage_missing")),
            })
    _persist()   # final rewrite includes per-entry summaries
    log(f"wrote {jpath}")
    if not args.mock:
        spend["runs"].append({"run_id":run_id,"workload":args.workload,
                              "cumulative_usd":spend["cumulative_usd"],"stopped_on_budget":stop_budget})
        save_spend(spend)
    write_workbook(summary, run_id, args.workload, args.mock)
    if not args.mock: rebuild_daily()   # template-format daily summary, rebuilt from corpus
    pending=[e for e in entries if int(done.get(e["label"],0)) < _wanted(e)]
    all_done = (len(pending)==0) and not stop_budget
    print(json.dumps({"tag":tag,"models_this_call":len(summary),"pending":len(pending),
                      "ALL_DONE":all_done,"stopped_on_budget":stop_budget,
                      "est_cumulative_usd":spend["cumulative_usd"] if not args.mock else 0,
                      "json":str(jpath),"workbook":str(WORKBOOK)}, indent=2))

# ---------- workbook ----------
def write_workbook(summary, run_id, workload, mock):
    try:
        from openpyxl import load_workbook, Workbook
    except Exception as e:
        log(f"openpyxl unavailable ({e}); skipping workbook"); return
    cols=["Model","API model","Effort","Workload","n","P50 output tok/s (native)",
          "P50 output tok/s (o200k)","P50 TTFT s","P50 TTFAT s","P50 E2E s",
          "Median input tok","Median output tok (native)","Median reasoning tok",
          "Median reasoning tok (est)","P50 think s","Resolved model"]
    if WORKBOOK.exists():
        wb=load_workbook(WORKBOOK)
    else:
        wb=Workbook(); wb.active.title="Latest"; wb.create_sheet("Run Log")
        wb["Latest"].append(cols)
        wb["Run Log"].append(["Run ID","Timestamp","Workload","Models","Mock"])
    # the daily view now lives in its own workbook; drop any legacy daily sheets here
    for old in ("Daily","Daily native tok-s"):
        if old in wb.sheetnames: del wb[old]
    ws=wb["Latest"]
    for ci,cname in enumerate(cols,1):        # extend legacy 13-column headers in place
        if ws.cell(1,ci).value!=cname: ws.cell(1,ci,cname)
    rowmap={ws.cell(r,1).value:r for r in range(2,ws.max_row+1)}
    for s in summary:
        row=[s["label"],s["api_model"],s["effort"] or "",workload,s["n"],
             s["p50_output_tps_native"],s["p50_output_tps_o200k"],s["p50_ttft_s"],
             s["p50_ttfat_s"],s["p50_e2e_s"],s["median_input_tokens_o200k"],
             s["median_output_tokens_native"],s["median_reasoning_tokens"],
             s.get("median_reasoning_tokens_est"),s.get("p50_think_time_s"),
             s.get("resolved_model")]
        if s["label"] in rowmap:
            rr=rowmap[s["label"]]
            for ci,val in enumerate(row,1): ws.cell(rr,ci,val)
        else:
            ws.append(row)
    wb["Run Log"].append([run_id, dt.datetime.now().isoformat(timespec="seconds"),
                          workload, len(summary), "yes" if mock else "no"])
    wb.save(WORKBOOK); log(f"wrote {WORKBOOK}")

def append_daily(summary, tag):
    """Append a row (one per fire-tag) of P50 native tok/s, one column per model."""
    try:
        from openpyxl import load_workbook, Workbook
    except Exception as e:
        log(f"openpyxl unavailable ({e}); skip daily append"); return
    SHEET="Daily native tok-s"
    if WORKBOOK.exists(): wb=load_workbook(WORKBOOK)
    else: wb=Workbook(); wb.active.title="Latest"
    if SHEET not in wb.sheetnames:
        ws=wb.create_sheet(SHEET); ws.append(["Run tag"])
    ws=wb[SHEET]
    header=[c.value for c in ws[1]]; colmap={h:i+1 for i,h in enumerate(header)}
    for s in summary:
        if s["label"] not in colmap:
            ws.cell(1, ws.max_column+1, s["label"]); colmap[s["label"]]=ws.max_column
    drow=None
    for r in range(2, ws.max_row+1):
        if ws.cell(r,1).value==tag: drow=r; break
    if drow is None: drow=ws.max_row+1; ws.cell(drow,1,tag)
    for s in summary:
        ws.cell(drow, colmap[s["label"]], s["p50_output_tps_native"])
    wb.save(WORKBOOK); log(f"appended row {tag} (+{len(summary)} models) to {SHEET}")

def _disp_effort(eff):
    """Display label for an effort: the lowest tier reads
       'non-reasoning' (OpenAI's 'minimal' / a call with no reasoning_effort)."""
    if eff in (None,"","minimal","none","non-reasoning"): return "non-reasoning"
    return eff

def rebuild_daily():
    """Standalone daily summary workbook in the InferenceCarbon_TokenSec_Daily.xlsx format.

    Writes DESKTOP/InferenceCarbon_TokenSec_Daily_Owned.xlsx with a 'Daily' sheet:
    column A = Date (one row per CALENDAR DAY), then one column per tracked model variant
    (reasoning models broken out as non-reasoning / low / medium / high / xhigh), then
    trailing Total / Mean / Standard Deviation formula rows. Each cell is the median
    output tok/s for that variant on that day, pooling every fire (AM, PM, ad-hoc),
    using the o200k_base (visible-token) measure UNIFORMLY. Rationale: (a) the native
    measure divides usage.completion_tokens — which includes HIDDEN reasoning tokens —
    by the visible-stream window, inflating high/xhigh variants by 10-30x when the
    model reasons silently before streaming; (b) mixing native-where-completed with
    o200k-where-timed-out puts two token-counting bases in one series (they differ by
    ~1.65x for Anthropic). One basis, one tokenizer, cross-family comparable. The
    native figures remain available as diagnostics in the engine workbook and the
    raw JSON corpus.

    Only the curated tracked_models.json variants are shown. Rebuilt wholesale from the
    results/*.json corpus each run, so it is idempotent and always current; the
    per-measurement detail stays in the JSON corpus and is not duplicated here.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.utils import get_column_letter
    except Exception as e:
        log(f"openpyxl unavailable ({e}); skip daily rebuild"); return
    cfg=load_tracked()
    # ordered display columns + lookup from (api_model, disp_effort) -> header
    columns=[]; colkey={}
    for m in cfg.get("models", []):
        api=m["api_model"]
        effs=m.get("efforts", cfg.get("efforts", DEFAULT_EFFORTS))
        if m.get("reasoning") and effs:
            if m.get("keep_default") and api not in columns:   # ladder added later: default series continues
                columns.append(api); colkey[(api,None)]=api
            for eff in effs:
                disp=_disp_effort(eff); hdr=f"{api} ({disp})"
                if hdr not in columns: columns.append(hdr)
                colkey[(api,disp)]=hdr
        else:
            columns.append(api); colkey[(api,None)]=api
    daily={}   # 'YYYY-MM-DD' -> {header: [tok/s, ...]}
    for fp in sorted(RESULTS.glob("run_*.json")):
        try: d=json.loads(fp.read_text())
        except Exception: continue
        if d.get("mock"): continue
        if d.get("provider","openai") != PROVIDER: continue   # one daily workbook per provider
        if d.get("workload","10k") != "10k": continue   # Daily = the 10k comparison series ONLY;
                                                        # short/1k riders live in the JSON corpus
        for r in d.get("records",[]):
            if not r.get("ok"): continue
            if r.get("prompt_class","summarise") != "summarise": continue   # one prompt class per series
            rid=r.get("run_id") or d.get("run_id") or ""
            if "T" not in rid: continue
            date=f"{rid[0:4]}-{rid[4:6]}-{rid[6:8]}"
            v=r.get("output_tps_o200k")                    # uniform o200k basis (see docstring)
            if v is None: v=r.get("output_tps_native")     # legacy records only
            if v is None: continue
            api=r.get("api_model"); eff=r.get("effort")
            hdr=colkey.get((api,None)) if eff in (None,"","minimal") and (api,None) in colkey \
                else colkey.get((api,_disp_effort(eff)))
            if hdr is None: continue          # not a tracked variant -> trimmed out
            daily.setdefault(date,{}).setdefault(hdr,[]).append(v)
    if not daily:
        log("no tracked non-mock records; skip daily rebuild"); return
    dates=sorted(daily)
    wb=Workbook(); ws=wb.active; ws.title="Daily"
    ws.append(["Date"]+columns)
    for dstr in dates:
        y,m,dd=map(int,dstr.split("-"))
        row=[dt.datetime(y,m,dd)]
        for hdr in columns:
            vals=daily[dstr].get(hdr)
            row.append(round(statistics.median(vals),2) if vals else None)
        ws.append(row); ws.cell(ws.max_row,1).number_format="yyyy-mm-dd"
    n=len(dates); ncols=len(columns)+1
    def rng(ci): c=get_column_letter(ci); return f"{c}2:{c}{1+n}"
    ws.append(["Total"]+[f"=SUM({rng(i)})" for i in range(2,ncols+1)])
    ws.append(["Mean"]+[f"=AVERAGE({rng(i)})" for i in range(2,ncols+1)])
    ws.append(["Standard Deviation"]+[f"=_xlfn.STDEV.S({rng(i)})" for i in range(2,ncols+1)])
    ws.column_dimensions["A"].width=14; ws.freeze_panes="B2"
    notes=wb.create_sheet("Notes")
    for line in [
        (f"InferenceCarbon — owned {PROVIDER} throughput tracker (daily summary)",),
        (None,),
        ("Each cell: median output tokens/sec for that model variant on that calendar day,",),
        ("pooled across all fires (AM, PM, ad-hoc). Token count is o200k_base (visible answer",),
        ("tokens) UNIFORMLY, over the visible-stream window (after first token, per standard",),
        ("methodology). Requests that hit the per-request timeout still yield a valid partial",),
        ("throughput sample. The native-tokenizer figures (which include hidden reasoning",),
        ("tokens and are NOT comparable across families) stay in the engine workbook and",),
        ("the raw JSON corpus as diagnostics. Basis fixed 2026-07-09; the Daily sheet is",),
        ("rebuilt wholesale from the corpus, so all history is on the corrected basis.",),
        (None,),
        ("'non-reasoning' = OpenAI's lowest reasoning tier (reasoning_effort=minimal).",),
        ("Models tracked are listed in tracked_models.json; new major families (e.g. gpt-5.6)",),
        ("are added automatically by `discover`. Raw per-measurement data: owned_benchmark/results/*.json.",),
        (None,),
        ("Recorder revision 2026-07-23: (1) think-tag text (Magistral-class) is now excluded",),
        ("from visible tokens and counted as reasoning — records BEFORE this date for",),
        ("magistral-small include streamed thinking in the visible series and are inflated;",),
        ("(2) default-thinking models (Gemini/Anthropic/DeepSeek) now receive reasoning",),
        ("headroom above the visible-answer cap — earlier records for heavy default thinkers",),
        ("(e.g. gemini-3.5-flash) were cap-truncated; (3) this sheet pools ONLY the 10k",),
        ("summarise workload — short/1k and reasoning-class riders stay in the JSON corpus;",),
        ("(4) resolved model ids, raw usage payloads and reasoning-token estimates with",),
        ("provenance are recorded per request.",),
        (None,),
        ("Auto-generated by inferencecarbon_bench.py — rebuilt every run. Safe to add your own sheets;",),
        ("the 'Daily' and 'Notes' sheets are overwritten on each rebuild.",),
    ]:
        notes.append(list(line))
    notes.column_dimensions["A"].width=100
    wb.save(DAILY_WORKBOOK)
    log(f"wrote {DAILY_WORKBOOK}: {n} dates x {len(columns)} model variants")

_TOK_CAL = {}
def _tok_calibration():
    """Load {slope k, intercept} mapping o200k tokens -> native tokens for PROVIDER, if a
    calibration file exists (written by calibrate-tokenizer). Cached per process."""
    if PROVIDER in _TOK_CAL: return _TOK_CAL[PROVIDER]
    f = RESULTS/f"tokenizer_calibration_{PROVIDER}.json"
    cal = None
    if f.exists():
        try: cal = json.loads(f.read_text())
        except Exception: pass
    _TOK_CAL[PROVIDER] = cal
    return cal

def cmd_calibrate_tokenizer(args):
    """Measure the PROVIDER-native-tokenizer vs o200k_base ratio on known visible text,
    via Anthropic's free count_tokens endpoint. Purpose: hidden-token estimation for
    providers whose usage.completion_tokens is NATIVE-tokenizer (Anthropic): hidden ~=
    native_total - k*o200k_visible. Without k, tokenizer divergence masquerades as
    thinking. Fits a regression over several text sizes so per-message overhead lands
    in the intercept, not the slope. Free: count_tokens bills nothing."""
    set_provider(args.provider)
    if args.provider != "anthropic":
        log("calibrate-tokenizer currently supports provider=anthropic (count_tokens endpoint)"); sys.exit(2)
    global ENC; ENC=get_encoder()
    import urllib.request
    key=read_key()
    models=[m["api_model"] for m in load_tracked().get("models",[])] or [args.model]
    if args.model and args.model!="ALL": models=[args.model]
    sizes=[500,1000,2000]
    def fit(model):
        pts=[]
        for i,sz in enumerate(sizes):
            text=_filler(sz, seed=4242+i)
            o200k=n_tokens(text)
            body=json.dumps({"model":model,"messages":[{"role":"user","content":text}]}).encode()
            req=urllib.request.Request("https://api.anthropic.com/v1/messages/count_tokens", data=body,
                headers={"x-api-key":key,"anthropic-version":PROV.get("anthropic_version","2023-06-01"),
                         "content-type":"application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                native=json.load(r)["input_tokens"]
            pts.append((o200k,native))
        n=len(pts); sx=sum(p[0] for p in pts); sy=sum(p[1] for p in pts)
        sxx=sum(p[0]**2 for p in pts); sxy=sum(p[0]*p[1] for p in pts)
        k=(n*sxy-sx*sy)/(n*sxx-sx*sx); b=(sy-k*sx)/n
        return round(k,5), round(b,2), pts
    per={}
    for m in models:
        try:
            k,b,pts=fit(m); per[m]={"k":k,"intercept":b}
            log(f"  {m:28s} k={k:.4f} intercept={b}")
        except Exception as e:
            log(f"  {m:28s} FAILED: {str(e)[:80]}")
    ks=[v["k"] for v in per.values()]
    out={"provider":args.provider,"models":per,
         "k":round(sorted(ks)[len(ks)//2],5) if ks else None,   # median as family fallback
         "generated":dt.datetime.now().isoformat(timespec="seconds"),
         "note":"PER-MODEL calibration (2026-07-23c): Anthropic runs two tokenizer generations "
                "(fable-5/sonnet-5/opus-4-8/opus-4-7 at k~1.64; opus-4-6/sonnet-4-6/haiku-4.5 at "
                "k~1.06), so a single family k mis-estimates hidden tokens for one generation or "
                "the other. native ~= k*o200k + intercept on benign English prose; hidden-token "
                "estimate = native_completion - k*o200k_visible. Top-level k = family median, "
                "fallback only."}
    f=RESULTS/f"tokenizer_calibration_{args.provider}.json"
    f.write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2)); log(f"wrote {f}")

def cmd_probe(args):
    """Fire ONE fully instrumented request per requested variant and print what was captured.
    Purpose: verify, for pennies, (a) that an effort/thinking parameter actually BINDS on a
    provider's compat layer, and (b) which usage fields carry reasoning tokens — before a
    ladder is enabled in a tracked file. Does not write to the results corpus or workbooks;
    does count against the spend state."""
    set_provider(args.provider)
    global ENC; ENC=get_encoder()
    in_t,min_o = WORKLOADS[args.workload]
    from openai import OpenAI
    ckw=dict(api_key=read_key(), timeout=args.request_timeout)
    if BASE_URL: ckw["base_url"]=BASE_URL
    if PROV.get("default_headers"): ckw["default_headers"]=PROV["default_headers"]
    client=OpenAI(**ckw)
    prices=load_prices(); spend=load_spend()
    out=[]
    for spec in args.variants.split(","):
        model,_,eff = spec.strip().partition(":")
        rec=benchmark_once(client, model, eff or None, build_prompt(in_t,min_o,seed=1234), min_o,
                           max_output=args.max_output, request_timeout=args.request_timeout,
                           thinking=bool(PROV.get("default_thinking")),
                           effort_style=PROV.get("effort_style","openai"),
                           thinking_budgets=PROV.get("thinking_budgets"))
        if rec.get("ok"):
            rc=est_cost(prices, model, rec.get("input_tokens_o200k"),
                        rec.get("output_tokens_native") or rec.get("output_tokens_o200k"))
            spend["cumulative_usd"]=round(spend["cumulative_usd"]+rc,4); save_spend(spend)
        keep=("api_model","effort","ok","error","resolved_model","output_tokens_native",
              "output_tokens_o200k","reasoning_tokens","reasoning_tokens_est","reasoning_source",
              "think_tokens_o200k","think_time_s","hidden_usage_delta","hidden_native_delta",
              "ttft_s","ttfat_s","e2e_s","timed_out","usage_missing","thinking_param_rejected",
              "min_answer_met","used_params")
        out.append({k:rec.get(k) for k in keep if rec.get(k) is not None or k in ("ok","reasoning_tokens")})
    print(json.dumps(out, indent=2))
    log("probe: effort BINDS if reasoning tokens/think time move with the requested effort; "
        "'thinking_param_rejected' or flat counts mean it does not — leave the ladder off.")

def main():
    ap=argparse.ArgumentParser(description="InferenceCarbon owned throughput benchmark")
    sub=ap.add_subparsers(dest="cmd", required=True)
    d=sub.add_parser("discover"); d.add_argument("--provider",default="openai"); d.add_argument("--mock",action="store_true"); d.set_defaults(func=cmd_discover)
    dl=sub.add_parser("daily"); dl.add_argument("--provider",default="openai")    # rebuild Daily workbook from corpus
    dl.set_defaults(func=lambda a: (set_provider(a.provider), rebuild_daily()))
    r=sub.add_parser("run")
    r.add_argument("--provider",default="openai")
    r.add_argument("--workload",choices=list(WORKLOADS),default="10k")
    r.add_argument("--repeats",type=int,default=8)
    r.add_argument("--models",help="comma-separated api_model ids or labels to limit to")
    r.add_argument("--limit",type=int,help="only first N manifest entries")
    r.add_argument("--max-output",dest="max_output",type=int,help="cap completion tokens (cost/time control)")
    r.add_argument("--budget",type=float,help="hard cap on cumulative ESTIMATED spend (USD) across all runs")
    r.add_argument("--exclude",help="comma-separated api_model substrings to skip (e.g. 'pro,codex-max')")
    r.add_argument("--skip-efforts",dest="skip_efforts",help="comma-separated reasoning efforts to skip (e.g. 'high,xhigh')")
    r.add_argument("--time-budget",dest="time_budget",type=int,help="seconds; stop starting new models after this, persist progress, resume next call")
    r.add_argument("--run-tag",dest="run_tag",help="shared tag so chunked calls of one fire resume together (default: date+AM/PM)")
    r.add_argument("--request-timeout",dest="request_timeout",type=float,default=25.0,help="per-request timeout (s); keeps each shell call under the 45s limit")
    r.add_argument("--prompt-class",dest="prompt_class",choices=["summarise","reason","reason-heavy"],default="summarise",
                   help="'reason' = multi-step puzzle that elicits genuine thinking (rider campaigns)")
    r.add_argument("--reasoning-headroom",dest="reasoning_headroom",type=int,default=4000,
                   help="completion-cap headroom added for thinking variants (hidden tokens)")
    r.add_argument("--jitter",type=float,default=0.0,
                   help="sleep U(0,jitter) seconds before starting — de-synchronises fixed fire times")
    r.add_argument("--timeout-capped-only",dest="timeout_capped_only",action="store_true",
                   help="only variants with >=50%% historically timed-out requests; pair with a long --request-timeout for uncensored measurement")
    r.add_argument("--mock",action="store_true")
    r.set_defaults(func=cmd_run)
    p=sub.add_parser("probe", help="one instrumented request per variant; verifies effort binding and reasoning capture BEFORE enabling a ladder")
    p.add_argument("--provider",default="openai")
    p.add_argument("--variants",required=True,help="comma-separated model or model:effort specs, e.g. 'claude-fable-5:medium,gemini-3.1-pro-preview:high'")
    p.add_argument("--workload",choices=list(WORKLOADS),default="short")
    p.add_argument("--max-output",dest="max_output",type=int,default=None)
    p.add_argument("--request-timeout",dest="request_timeout",type=float,default=90.0)
    p.set_defaults(func=cmd_probe)
    c=sub.add_parser("calibrate-tokenizer", help="fit native-vs-o200k tokenizer slope on known text (free; Anthropic count_tokens)")
    c.add_argument("--provider",default="anthropic")
    c.add_argument("--model",default="claude-fable-5")
    c.set_defaults(func=cmd_calibrate_tokenizer)
    args=ap.parse_args(); args.func(args)

if __name__=="__main__":
    main()
