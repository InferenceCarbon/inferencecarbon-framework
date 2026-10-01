# InferenceCarbon API test harness

Apache-2.0, like the rest of the software in this repository. This is the client referred to on
https://www.inferencecarbon.ai/api; it is mirrored here so that it is public.

`ic_api.py` is a single-file command-line client for the public information API
(`https://api.inferencecarbon.ai/v1/public`). It needs Python 3.9 or later and no
packages.

## First run: get a key

```bash
cd tools/api-harness

# 1. Create an account. This records your acceptance of the Terms of Service and
#    sends a verification email.
python3 ic_api.py signup you@example.org

# 2. Click the link in the email (valid 48 hours). Then sign in and accept the
#    API Terms (https://www.inferencecarbon.ai/api-terms):
python3 ic_api.py login you@example.org
python3 ic_api.py accept-terms
#    → login shows: email verified, API terms accepted, can create key.

# 3. Create a key, declaring its use (academic | public-body | commercial-evaluation |
#    commercial-licensed). It is printed once and saved to ~/.inferencecarbon/api_key.
python3 ic_api.py create-key laptop --use academic

# 4. Prove it works.
python3 ic_api.py check
```

If your address is not yet verified, `resend-verify` sends a fresh link. The same
steps are available in the browser at https://www.inferencecarbon.ai/app?view=api-keys.
Extension and calculator users who never want a key are never asked to accept the API Terms.

The key is read from `--key`, then the `INFERENCECARBON_API_KEY` environment
variable, then `~/.inferencecarbon/api_key`. Passwords are prompted for, or read
from `INFERENCECARBON_PASSWORD` for scripted use.

## Pull information

```bash
python3 ic_api.py models                      # table: every published row, central [low–high], confidence
python3 ic_api.py models --csv rows.csv       # export all fields
python3 ic_api.py models --json               # raw response
python3 ic_api.py models --version 1.0.0      # figures as published under v1.0.0
python3 ic_api.py models --as-of 2026-09-01   # rows in force on a date
python3 ic_api.py model gpt-5.5-medium        # one row, every field
python3 ic_api.py uncertainty gpt-5.5-medium  # per-factor breakdown of the band
python3 ic_api.py providers                   # routing, grid, PUE, clean-energy parameters
python3 ic_api.py factors                     # energy-to-carbon factors and routing scenarios
python3 ic_api.py coverage                    # what is published and what is deliberately absent
python3 ic_api.py meta                        # versions, citation, usage rule, licences (no key needed)
```

Every keyed call prints the remaining rate limit to stderr.

## Manage keys

```bash
python3 ic_api.py keys
python3 ic_api.py rotate-key <id>   # new secret saved locally, old one revoked
python3 ic_api.py revoke-key <id>
```

Key management uses your signed-in session, never the API key itself.

## Other hosts

`--base <url>` (or `INFERENCECARBON_API_BASE`) points the harness at another deployment.

## Reporting rule

Every figure the API returns is a bounded estimate: report the central value with
its low and high bounds and its confidence rating, and state the methodology
version. The `models` table prints all of them side by side for that reason.
