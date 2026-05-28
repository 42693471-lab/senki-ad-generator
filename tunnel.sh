#!/bin/bash
LOCKFILE="/tmp/lovart-tunnel.lock"
URLFILE="/Users/luanbabaiyunrousui/lovart-tool/public-url.txt"

# Prevent duplicates
if [ -f "$LOCKFILE" ]; then
  pid=$(cat "$LOCKFILE" 2>/dev/null)
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "Tunnel already running (pid=$pid)"
    exit 0
  fi
fi
echo $$ > "$LOCKFILE"

cleanup() {
  rm -f "$LOCKFILE"
}
trap cleanup EXIT INT TERM

while true; do
  echo "[$(date '+%H:%M:%S')] Tunnel connecting..."
  # NOTE: do NOT use -N — localhost.run requires a PTY for auth
  ssh -T \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=15 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o ConnectTimeout=30 \
    -R 80:localhost:8766 nokey@localhost.run 2>&1 | while IFS= read -r line; do
    echo "$line"
    if echo "$line" | grep -qE 'https?://[a-zA-Z0-9]+\.lhr\.life'; then
      url=$(echo "$line" | grep -oE 'https?://[a-zA-Z0-9][^ ]*\.lhr\.life' | head -1)
      if [ -n "$url" ]; then
        echo "$url" > "$URLFILE"
        echo "[$(date '+%H:%M:%S')] URL: $url"
      fi
    fi
  done
  echo "[$(date '+%H:%M:%S')] Tunnel died, restarting in 10s..."
  sleep 10
done
