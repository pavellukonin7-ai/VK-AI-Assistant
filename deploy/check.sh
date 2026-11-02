#!/usr/bin/env bash
set -Eeuo pipefail

target_dir="/opt/vk-ai-bot"

echo "SERVICE=$(systemctl is-active vk-ai-bot.service 2>/dev/null || true)"
echo "ENABLED=$(systemctl is-enabled vk-ai-bot.service 2>/dev/null || true)"
echo "MODEL=$(sed -n 's/^OPENAI_MODEL=//p' "$target_dir/.env" | tail -1)"
echo "BASE_URL=$(sed -n 's/^OPENAI_BASE_URL=//p' "$target_dir/.env" | tail -1)"
echo "CONTEXT=$(sed -n 's/^MAX_CONTEXT_MESSAGES=//p' "$target_dir/.env" | tail -1)"
echo "USER_FILES=$(find "$target_dir/users" -maxdepth 1 -type f -name '*.json' | wc -l)"
journalctl -u vk-ai-bot.service -n 20 --no-pager

