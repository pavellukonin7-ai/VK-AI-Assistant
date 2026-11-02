#!/usr/bin/env bash
set -Eeuo pipefail

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_dir="/opt/vk-ai-bot"
service_file="/etc/systemd/system/vk-ai-bot.service"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Запустите установщик от root." >&2
  exit 1
fi

if ! id vkbot >/dev/null 2>&1; then
  useradd --system --home-dir "$target_dir" --shell /usr/sbin/nologin vkbot
fi

install -d -m 0750 -o root -g vkbot "$target_dir"
install -d -m 0750 -o vkbot -g vkbot "$target_dir/users"
install -d -m 0750 -o vkbot -g vkbot "$target_dir/.vkbottle"

if [[ -f "$target_dir/.env" ]]; then
  cp -a "$target_dir/.env" "/root/vk-ai-bot.env.backup.$(date -u +%Y%m%dT%H%M%SZ)"
fi

rsync -a --delete \
  --exclude '.env' \
  --exclude '.venv' \
  --exclude 'users/' \
  --exclude '__pycache__/' \
  "$source_dir/" "$target_dir/"

if [[ ! -f "$target_dir/.env" ]]; then
  install -m 0640 -o root -g vkbot "$source_dir/.env.example" "$target_dir/.env"
  echo "Создан $target_dir/.env. Заполните VK_TOKEN и OPENAI_API_KEY." >&2
fi

python3 -m venv "$target_dir/.venv"
"$target_dir/.venv/bin/pip" install --upgrade pip
"$target_dir/.venv/bin/pip" install -r "$target_dir/requirements.txt"

chown -R root:vkbot "$target_dir"
chown -R vkbot:vkbot "$target_dir/users"
chown -R vkbot:vkbot "$target_dir/.vkbottle"
chmod 0640 "$target_dir/.env"
install -m 0644 "$source_dir/deploy/vk-ai-bot.service" "$service_file"

systemctl daemon-reload
if grep -Eq '^VK_TOKEN=.+$' "$target_dir/.env" && \
   grep -Eq '^OPENAI_API_KEY=.+$' "$target_dir/.env"; then
  systemctl enable --now vk-ai-bot.service
  systemctl restart vk-ai-bot.service
  systemctl --no-pager --full status vk-ai-bot.service
else
  systemctl disable vk-ai-bot.service >/dev/null 2>&1 || true
  echo "Сервис установлен, но не запущен: заполните два секретных ключа в .env." >&2
fi

