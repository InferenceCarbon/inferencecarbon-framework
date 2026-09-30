#!/usr/bin/env python3
# Copyright 2026 InferenceCarbon Ltd. Licensed under the Apache License, Version 2.0
# (see LICENSE at the repository root). Mirrored from the product repository.
"""InferenceCarbon API test harness.

A single-file command-line client for the public information API. Standard
library only (Python 3.9+); no packages to install.

Walks the whole access flow and then exercises every endpoint:

    python ic_api.py signup you@example.org      # create account (accepts the Terms of Service), sends verify email
    # click the link in the email, then:
    python ic_api.py login you@example.org       # sign in; shows verification / API-terms state
    python ic_api.py accept-terms                # read and accept the API Terms (once per version)
    python ic_api.py create-key laptop --use academic   # creates a key; stores it in ~/.inferencecarbon/api_key
                                                # --use: academic | public-body | commercial-evaluation | commercial-licensed
    python ic_api.py check                       # one keyed call: proves the key works
    python ic_api.py models                      # table of every published row
    python ic_api.py models --csv out.csv        # export the rows
    python ic_api.py model gpt-5.5-medium        # one row, all fields
    python ic_api.py uncertainty gpt-5.5-medium  # why the band is as wide as it is
    python ic_api.py providers | factors | coverage | meta
    python ic_api.py keys | revoke-key <id> | rotate-key <id>

Key resolution order: --key flag, INFERENCECARBON_API_KEY env var, ~/.inferencecarbon/api_key.
Session tokens from `login`/`signup` are kept in ~/.inferencecarbon/session.json and are only
needed for account actions (accept-terms, create-key, keys, revoke-key, rotate-key, resend-verify).

--base overrides the API origin (default https://api.inferencecarbon.ai), e.g. a staging host.
"""
from __future__ import annotations

import argparse
import csv
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://api.inferencecarbon.ai"
CONF_DIR = Path.home() / ".inferencecarbon"
KEY_FILE = CONF_DIR / "api_key"
SESSION_FILE = CONF_DIR / "session.json"
USER_AGENT = "inferencecarbon-api-harness/1.0"


# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------

class ApiError(Exception):
    def __init__(self, status: int, detail: str, headers: dict | None = None):
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status
        self.detail = detail
        self.headers = headers or {}


def request(method: str, url: str, *, body: dict | None = None, headers: dict | None = None) -> tuple[dict | list | None, dict]:
    data = json.dumps(body).encode() if body is not None else None
    h = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if data is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return (json.loads(raw) if raw else None), hdrs
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw)
            detail = payload.get("detail", raw.decode(errors="replace"))
            if isinstance(detail, dict):
                detail = detail.get("message") or json.dumps(detail)
            elif isinstance(detail, list):  # pydantic validation errors
                detail = "; ".join(f"{'.'.join(map(str, d.get('loc', [])))}: {d.get('msg')}" for d in detail)
        except Exception:
            detail = raw.decode(errors="replace")
        raise ApiError(e.code, str(detail), {k.lower(): v for k, v in e.headers.items()}) from None
    except urllib.error.URLError as e:
        raise ApiError(0, f"connection failed: {e.reason}") from None


# ----------------------------------------------------------------------------
# Local state
# ----------------------------------------------------------------------------

def _ensure_conf_dir() -> None:
    CONF_DIR.mkdir(mode=0o700, exist_ok=True)


def _write_private(path: Path, text: str) -> None:
    """Create/replace a file with mode 0600 from the start (no 0644 window)."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.chmod(path, 0o600)


def save_key(key: str) -> None:
    _ensure_conf_dir()
    _write_private(KEY_FILE, key.strip() + "\n")


def load_key(explicit: str | None) -> str | None:
    if explicit:
        return explicit.strip()
    env = os.environ.get("INFERENCECARBON_API_KEY")
    if env:
        return env.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text().strip() or None
    return None


def save_session(tokens: dict) -> None:
    _ensure_conf_dir()
    _write_private(SESSION_FILE, json.dumps({
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "email": tokens.get("email"),
    }))


def load_session() -> dict | None:
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text())
        except json.JSONDecodeError:
            return None
    return None


# ----------------------------------------------------------------------------
# Client
# ----------------------------------------------------------------------------

class Client:
    def __init__(self, base: str, key: str | None):
        self.base = base.rstrip("/")
        self.key = key

    # -- public (keyed) -------------------------------------------------------
    def public(self, path: str, params: dict | None = None) -> tuple[dict | list | None, dict]:
        url = f"{self.base}/v1/public{path}"
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        headers = {"X-API-Key": self.key} if self.key else {}
        return request("GET", url, headers=headers)

    # -- account (JWT) --------------------------------------------------------
    def _bearer(self) -> dict:
        sess = load_session()
        if not sess or not sess.get("access_token"):
            raise SystemExit("Not signed in. Run: python ic_api.py login you@example.org")
        return {"Authorization": f"Bearer {sess['access_token']}"}

    def _auth(self, method: str, path: str, body: dict | None = None) -> tuple[dict | list | None, dict]:
        url = f"{self.base}/v1/auth{path}"
        try:
            return request(method, url, body=body, headers=self._bearer())
        except ApiError as e:
            if e.status == 401:
                refreshed = self._refresh()
                if refreshed:
                    return request(method, url, body=body, headers=self._bearer())
            raise

    def _refresh(self) -> bool:
        sess = load_session()
        if not sess or not sess.get("refresh_token"):
            return False
        try:
            data, _ = request("POST", f"{self.base}/v1/auth/refresh", body={"refresh_token": sess["refresh_token"]})
        except ApiError:
            return False
        data = dict(data or {})
        data.setdefault("email", sess.get("email"))
        save_session(data)
        return True

    def signup(self, email: str, password: str) -> dict:
        data, _ = request("POST", f"{self.base}/v1/auth/register", body={
            "email": email, "password": password, "accept_terms": True,
        })
        save_session(dict(data or {}, email=email))
        return data or {}

    def login(self, email: str, password: str) -> dict:
        data, _ = request("POST", f"{self.base}/v1/auth/login", body={"email": email, "password": password})
        save_session(dict(data or {}, email=email))
        return data or {}

    def me(self) -> dict:
        data, _ = self._auth("GET", "/me")
        return data or {}

    def accept_terms(self, version: str) -> dict:
        data, _ = self._auth("POST", "/accept-terms", {"terms_version": version})
        return data or {}

    def resend_verification(self) -> dict:
        data, _ = self._auth("POST", "/verify-email/resend")
        return data or {}

    def keys(self) -> list:
        data, _ = self._auth("GET", "/api-keys")
        return (data or {}).get("keys", [])

    def create_key(self, name: str, intended_use: str) -> dict:
        data, _ = self._auth("POST", "/api-keys", {"name": name, "intended_use": intended_use})
        return data or {}

    def rotate_key(self, key_id: str) -> dict:
        data, _ = self._auth("POST", f"/api-keys/{urllib.parse.quote(key_id)}/rotate")
        return data or {}

    def revoke_key(self, key_id: str) -> None:
        self._auth("DELETE", f"/api-keys/{urllib.parse.quote(key_id)}")


# ----------------------------------------------------------------------------
# Output helpers
# ----------------------------------------------------------------------------

def print_json(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def print_table(rows: list[dict], columns: list[tuple[str, str]]) -> None:
    """columns: [(key, heading)]. Numbers are printed to 2 dp."""
    def cell(v):
        if v is None:
            return "—"
        if isinstance(v, float):
            return f"{v:.2f}"
        return str(v)
    table = [[cell(r.get(k)) for k, _ in columns] for r in rows]
    widths = [max(len(h), *(len(t[i]) for t in table)) if table else len(h) for i, (_, h) in enumerate(columns)]
    line = "  ".join(h.ljust(w) for (_, h), w in zip(columns, widths))
    print(line)
    print("  ".join("-" * w for w in widths))
    for t in table:
        print("  ".join(c.ljust(w) for c, w in zip(t, widths)))


def write_csv(rows: list[dict], path: str) -> None:
    if not rows:
        print("no rows to write", file=sys.stderr)
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {path}")


def show_rate_limit(headers: dict) -> None:
    lim, rem, reset = headers.get("x-ratelimit-limit"), headers.get("x-ratelimit-remaining"), headers.get("x-ratelimit-reset")
    if lim:
        print(f"[rate limit {rem}/{lim} remaining, resets {reset}]", file=sys.stderr)


def describe_access(me: dict) -> None:
    print(f"Signed in as {me.get('email')}")
    print(f"  email verified : {'yes' if me.get('email_verified') else 'NO — click the link in the verification email (or run resend-verify)'}")
    tv = me.get("terms_version")
    cur = me.get("terms_current_version")
    ok = me.get("terms_up_to_date")
    print(f"  API terms      : {'accepted v' + str(tv) if ok else ('NO — run accept-terms (current version ' + str(cur) + ')')}")
    print(f"  active keys    : {me.get('api_key_count', 0)}")
    blockers = me.get("api_access_blockers") or []
    print("  can create key : " + ("yes" if not blockers else "not yet (" + ", ".join(blockers) + ")"))


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

def _password(prompt: str) -> str:
    pw = os.environ.get("INFERENCECARBON_PASSWORD")
    return pw if pw else getpass.getpass(prompt)


def cmd_signup(c: Client, a) -> None:
    print("Creating an account records your acceptance of the Terms of Service")
    print("(https://www.inferencecarbon.ai/terms). The API Terms are accepted separately with accept-terms.")
    if not a.yes and input("Accept and continue? [y/N] ").strip().lower() != "y":
        raise SystemExit("aborted")
    pw = _password("Choose a password (min 8 chars, upper+lower+digit): ")
    c.signup(a.email, pw)
    print(f"Account created for {a.email}. A verification email has been sent; click its link, then run:")
    print(f"  python {sys.argv[0]} login {a.email}")


def cmd_login(c: Client, a) -> None:
    pw = _password("Password: ")
    c.login(a.email, pw)
    describe_access(c.me())


def cmd_whoami(c: Client, a) -> None:
    describe_access(c.me())


def cmd_resend_verify(c: Client, a) -> None:
    r = c.resend_verification()
    print("already verified" if r.get("already_verified") else ("sent to " + r.get("email", "")) if r.get("sent") else "could not send; try again shortly")


def cmd_accept_terms(c: Client, a) -> None:
    me = c.me()
    if me.get("terms_up_to_date"):
        print(f"API terms already accepted (v{me.get('terms_version')}).")
        return
    ver = me.get("terms_current_version")
    print(f"Read https://www.inferencecarbon.ai/api-terms (version {ver}).")
    if not a.yes and input("Accept the API Terms? [y/N] ").strip().lower() != "y":
        raise SystemExit("aborted")
    describe_access(c.accept_terms(ver))


INTENDED_USES = {
    "academic": "academic or independent research, teaching, non-commercial publication",
    "public-body": "regulator, standards body or public authority",
    "commercial-evaluation": "commercial evaluation: 30-day trial, the key expires automatically",
    "commercial-licensed": "commercial use under a licence agreement with InferenceCarbon",
}


def cmd_create_key(c: Client, a) -> None:
    use = a.use.replace("-", "_")
    created = c.create_key(a.name, use)
    save_key(created["key"])
    print(f"Created key '{created['name']}' ({created['key_prefix']}…, use: {a.use}) and saved it to {KEY_FILE}")
    if created.get("expires_at"):
        print(f"Expires: {created['expires_at']}")
    if use.startswith("commercial"):
        print("Commercial use needs a licence: https://www.inferencecarbon.ai/api-terms#commercial (info@inferencecarbon.ai)")
    print("This is the only time the full key is shown:")
    print(f"  {created['key']}")
    print("The harness reads it from that file; to use it elsewhere, export INFERENCECARBON_API_KEY from the file, not by pasting.")


def cmd_keys(c: Client, a) -> None:
    rows = c.keys()
    if not rows:
        print("no keys")
        return
    print_table(rows, [("id", "id"), ("name", "name"), ("key_prefix", "prefix"), ("is_active", "active"),
                       ("created_at", "created"), ("last_used_at", "last used")])


def cmd_revoke_key(c: Client, a) -> None:
    c.revoke_key(a.key_id)
    print(f"revoked {a.key_id}")


def cmd_rotate_key(c: Client, a) -> None:
    created = c.rotate_key(a.key_id)
    save_key(created["key"])
    print(f"Rotated. New key ({created['key_prefix']}…) saved to {KEY_FILE}:")
    print(f"  {created['key']}")


def _need_key(c: Client) -> None:
    if not c.key:
        raise SystemExit("No API key. Run create-key, or set INFERENCECARBON_API_KEY, or pass --key.")


def cmd_check(c: Client, a) -> None:
    _need_key(c)
    data, hdrs = c.public("/models", {"modality": "text"})
    n = data.get("total_models") if isinstance(data, dict) else None
    print(f"OK — key accepted. {n} text-model rows, methodology v{data.get('methodology_version')}, "
          f"data window {data.get('data_window_start')} to {data.get('data_window_end')}.")
    show_rate_limit(hdrs)


MODEL_COLUMNS = [
    ("model_id", "model_id"),
    ("reasoning_mode", "mode"),
    ("carbon_gco2e_per_1k_tokens_market", "market"),
    ("carbon_gco2e_per_1k_tokens_market_low", "mkt low"),
    ("carbon_gco2e_per_1k_tokens_market_high", "mkt high"),
    ("carbon_gco2e_per_1k_tokens_location", "location"),
    ("carbon_gco2e_per_1k_tokens_location_low", "loc low"),
    ("carbon_gco2e_per_1k_tokens_location_high", "loc high"),
    ("wh_per_1k_tokens", "Wh/1k"),
    ("confidence", "conf"),
    ("input_cost_per_million", "$/M in"),
    ("output_cost_per_million", "$/M out"),
    ("methodology_version", "ver"),
]


def cmd_models(c: Client, a) -> None:
    _need_key(c)
    data, hdrs = c.public("/models", {
        "modality": a.modality, "provider": a.provider,
        "methodology_version": a.version, "as_of": a.as_of,
    })
    rows = data.get("models", []) if isinstance(data, dict) else []
    if a.json:
        print_json(data)
    elif a.csv:
        write_csv(rows, a.csv)
    else:
        print(f"{len(rows)} rows · methodology v{data.get('methodology_version')} · "
              f"data window {data.get('data_window_start')} to {data.get('data_window_end')} · "
              "gCO2e per 1,000 output tokens; every figure is central [low–high] with confidence; prices are USD list per 1M tokens")
        print_table(rows, MODEL_COLUMNS)
    show_rate_limit(hdrs)


def cmd_model(c: Client, a) -> None:
    _need_key(c)
    data, hdrs = c.public("/models", {"modality": "all"})
    rows = [m for m in data.get("models", []) if m.get("model_id") == a.model_id]
    if not rows:
        raise SystemExit(f"no published row for '{a.model_id}'. Try: python ic_api.py coverage")
    print_json(rows[0])
    show_rate_limit(hdrs)


def _simple(path: str):
    def run(c: Client, a) -> None:
        if path != "/meta":
            _need_key(c)
        params = {"provider": getattr(a, "provider", None)} if path == "/coverage" else None
        data, hdrs = c.public(path, params)
        print_json(data)
        show_rate_limit(hdrs)
    return run


def cmd_uncertainty(c: Client, a) -> None:
    _need_key(c)
    data, hdrs = c.public(f"/models/{urllib.parse.quote(a.model_id)}/uncertainty")
    print_json(data)
    show_rate_limit(hdrs)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ic_api.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", default=os.environ.get("INFERENCECARBON_API_BASE", DEFAULT_BASE), help="API origin")
    p.add_argument("--key", help="API key (else env INFERENCECARBON_API_KEY, else ~/.inferencecarbon/api_key)")
    p.add_argument("--insecure", action="store_true", help="allow a plain http:// --base (local development only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("signup", help="create an account (accepts the terms) and send the verification email")
    s.add_argument("email"); s.add_argument("-y", "--yes", action="store_true", help="skip the terms prompt")
    s.set_defaults(fn=cmd_signup)
    s = sub.add_parser("login", help="sign in and show verification / terms state"); s.add_argument("email"); s.set_defaults(fn=cmd_login)
    sub.add_parser("whoami", help="show the signed-in account's access state").set_defaults(fn=cmd_whoami)
    sub.add_parser("resend-verify", help="resend the verification email").set_defaults(fn=cmd_resend_verify)
    s = sub.add_parser("accept-terms", help="accept the current API terms (existing accounts)"); s.add_argument("-y", "--yes", action="store_true"); s.set_defaults(fn=cmd_accept_terms)
    s = sub.add_parser("create-key", help="create an API key and store it locally")
    s.add_argument("name", nargs="?", default="harness")
    s.add_argument("--use", required=True, choices=sorted(INTENDED_USES),
                   help="declared use per the API Terms: " + "; ".join(f"{k} = {v}" for k, v in INTENDED_USES.items()))
    s.set_defaults(fn=cmd_create_key)
    sub.add_parser("keys", help="list your keys").set_defaults(fn=cmd_keys)
    s = sub.add_parser("revoke-key"); s.add_argument("key_id"); s.set_defaults(fn=cmd_revoke_key)
    s = sub.add_parser("rotate-key"); s.add_argument("key_id"); s.set_defaults(fn=cmd_rotate_key)

    sub.add_parser("check", help="one keyed request to prove the key works").set_defaults(fn=cmd_check)
    s = sub.add_parser("models", help="all published rows (table, --json or --csv)")
    s.add_argument("--modality", default="text"); s.add_argument("--provider")
    s.add_argument("--version", help="pin to a methodology version, e.g. 1.0.0"); s.add_argument("--as-of", dest="as_of", help="YYYY-MM-DD")
    s.add_argument("--json", action="store_true"); s.add_argument("--csv", metavar="FILE")
    s.set_defaults(fn=cmd_models)
    s = sub.add_parser("model", help="one row with every field"); s.add_argument("model_id"); s.set_defaults(fn=cmd_model)
    s = sub.add_parser("uncertainty", help="per-factor breakdown of a model's band"); s.add_argument("model_id"); s.set_defaults(fn=cmd_uncertainty)
    sub.add_parser("providers", help="provider parameters (Appendix A, Tables 3–4)").set_defaults(fn=_simple("/providers"))
    sub.add_parser("factors", help="energy-to-carbon factors and routing scenarios").set_defaults(fn=_simple("/factors"))
    s = sub.add_parser("coverage", help="what is published and what is absent"); s.add_argument("--provider"); s.set_defaults(fn=_simple("/coverage"))
    sub.add_parser("meta", help="versions, citation, usage rule, licences, changelog (no key needed)").set_defaults(fn=_simple("/meta"))

    a = p.parse_args(argv)
    if not a.base.lower().startswith("https://") and not a.insecure:
        print("error: --base must be https:// (keys and session tokens travel in the clear otherwise); "
              "pass --insecure for a local http:// dev server", file=sys.stderr)
        return 2
    c = Client(a.base, load_key(a.key))
    try:
        a.fn(c, a)
    except ApiError as e:
        print(f"error: {e}", file=sys.stderr)
        if e.status == 401 and "X-API-Key" in e.detail:
            print("hint: run create-key first, or check INFERENCECARBON_API_KEY", file=sys.stderr)
        if e.status == 403 and "terms_not_accepted" in e.detail:
            print("hint: the API Terms have a new version — run: python ic_api.py accept-terms", file=sys.stderr)
        if e.status == 403 and "email_unverified" in e.detail:
            print("hint: verify your email (python ic_api.py resend-verify), then retry", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
