#!/usr/bin/env bash
# Key audit for the InferenceCarbon framework repository.
#
# Run this BEFORE the first push to GitHub, not before the visibility flip:
# the audit is an audit of the COMMIT HISTORY, not the working tree. A key
# deleted in a later commit remains readable in the earlier commit forever.
#
# This script automates steps 2–4 of the audit (scanners, history grep,
# non-key leaks). Step 1 — inventorying, from the provider consoles, every
# credential the engine could possibly hold — and step 5 — rotating anything
# found — are human steps and cannot be scripted.
set -uo pipefail

fail=0
note() { printf '\n== %s ==\n' "$*"; }

note "Step 2a: gitleaks over commit history"
if command -v gitleaks >/dev/null; then
  gitleaks git . --redact --verbose || fail=1
  note "Step 2b: gitleaks over working tree (incl. untracked)"
  gitleaks dir . --redact --verbose || fail=1
else
  echo "gitleaks not installed — install from https://github.com/gitleaks/gitleaks"; fail=1
fi

note "Step 2c: trufflehog (verifies live credentials against providers)"
if command -v trufflehog >/dev/null; then
  trufflehog git "file://$(pwd)" --results=verified,unknown || fail=1
else
  echo "trufflehog not installed — install from https://github.com/trufflesecurity/trufflehog"; fail=1
fi

note "Step 3: history grep for provider key patterns"
if git rev-list --all | xargs git grep -nIE \
    'sk-ant-|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}|AKIA[0-9A-Z]{16}' -- 2>/dev/null; then
  echo 'MATCHES FOUND ^'; fail=1
else
  echo "no key-pattern matches"
fi
if git rev-list --all | xargs git grep -nIl \
    'BEGIN .*PRIVATE KEY|client_secret|refresh_token|Authorization: Bearer' -- 2>/dev/null; then
  echo 'MATCHES FOUND ^ (review each file above)'; fail=1
else
  echo "no private-key/OAuth-material matches"
fi

note "Step 4a: commit author identities (publishable?)"
git log --format='%an <%ae>' | sort -u

note "Step 4b: absolute paths / home directories"
if git grep -nI -e '/Users/' -e '/home/' -- . 2>/dev/null | grep -v 'audit_history.sh'; then
  echo 'MATCHES FOUND ^ (config files, notebook metadata, log headers)'; fail=1
else
  echo "no absolute-path matches in tree"
fi

note "Step 4c: reminders that cannot be grepped"
cat <<'EOF'
 [ ] Read the prompt corpus once, deliberately — the hard-task reasoning
     prompts and the 10,000-token inputs will be public.
 [ ] No third-party benchmark series values anywhere (Section 5.3).
 [ ] No billing account identifiers: account ids, org ids, payment details.
     (The frozen campaign's per-provider budget caps and spend estimates are
     published deliberately: providers.json, the scheduled prompts and the
     corpus run logs.)
EOF

note "Result"
if [ "$fail" -ne 0 ]; then
  echo "AUDIT INCOMPLETE OR FINDINGS PRESENT — do not push."
  echo "If a credential was found: rotate it in the provider console FIRST,"
  echo "then discard the history (rm -rf .git && git init) rather than rewriting it."
  exit 1
fi
echo "Automated checks passed. Complete the manual items above before pushing."
