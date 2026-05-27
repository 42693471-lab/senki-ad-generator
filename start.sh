#!/bin/bash
cd "$(dirname "$0")"

echo " Lovart 批量做图工作台"
echo ""

# Check env vars
if [ -z "$LOVART_ACCESS_KEY" ] || [ -z "$LOVART_SECRET_KEY" ]; then
  # try to source from .zshrc
  source ~/.zshrc 2>/dev/null
  if [ -z "$LOVART_ACCESS_KEY" ] || [ -z "$LOVART_SECRET_KEY" ]; then
    echo "❌ LOVART_ACCESS_KEY 和 LOVART_SECRET_KEY 未设置"
    echo "   请在 ~/.zshrc 中设置后运行: source ~/.zshrc"
    exit 1
  fi
fi

echo " 启动服务 → http://localhost:8765"
python3 server.py
