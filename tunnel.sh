#!/bin/bash
while true; do
  ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
    -o ExitOnForwardFailure=yes \
    -R 80:localhost:8766 nokey@localhost.run 2>&1 | while IFS= read -r line; do
    echo "$line"
    if echo "$line" | grep -qE 'https?://[a-zA-Z0-9]'; then
      url=$(echo "$line" | grep -oE 'https?://[a-zA-Z0-9][^ ]+')
      if echo "$url" | grep -qv 'localhost.run/docs\|localhost.run/faq\|twitter.com'; then
        echo "$url" > /Users/luanbabaiyunrousui/lovart-tool/public-url.txt
      fi
    fi
  done
  sleep 10
done
