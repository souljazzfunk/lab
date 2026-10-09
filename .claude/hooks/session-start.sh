#!/bin/bash
# Make agent-browser usable in Claude Code on the web sessions.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install this repo's plugins. The container starts fresh each session, and
# enabledPlugins in settings.json only enables plugins that are installed.
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add "$CLAUDE_PROJECT_DIR" >/dev/null 2>&1 || true
  for plugin in pstack@lab yomiyasu@lab simple-english@lab; do
    claude plugin install "$plugin" >/dev/null 2>&1 || true
  done
fi

CHROMIUM=/opt/pw-browsers/chromium
CA=/root/.ccr/agent-proxy-ca.crt
NSSDB="$HOME/.pki/nssdb"

if ! command -v agent-browser >/dev/null 2>&1; then
  npm install -g agent-browser >/dev/null 2>&1
fi

# Use the preinstalled Chromium instead of downloading Chrome.
if [ -x "$CHROMIUM" ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export AGENT_BROWSER_EXECUTABLE_PATH=$CHROMIUM" >> "$CLAUDE_ENV_FILE"
fi

# Chromium reads trust from the NSS store, not the system CA bundle.
if [ -f "$CA" ]; then
  if ! command -v certutil >/dev/null 2>&1; then
    (apt-get install -y libnss3-tools >/dev/null 2>&1 \
      || { apt-get update >/dev/null 2>&1 && apt-get install -y libnss3-tools >/dev/null 2>&1; }) || true
  fi
  if command -v certutil >/dev/null 2>&1; then
    mkdir -p "$NSSDB"
    [ -f "$NSSDB/cert9.db" ] || certutil -N -d "sql:$NSSDB" --empty-password
    certutil -L -d "sql:$NSSDB" -n ccr-agent-proxy >/dev/null 2>&1 \
      || certutil -A -d "sql:$NSSDB" -n ccr-agent-proxy -t "C,," -i "$CA"
  fi
fi
