#!/bin/bash

echo "🚀 Запускаем ИИ-Агента на Oracle Cloud (ARM)..."

# 1. Удаляем старый контейнер, если он завис или существует
docker stop my_ai_bot || true
docker rm my_ai_bot || true

# 2. Запуск новой версии
docker run -d \
  --name my_ai_bot \
  --restart unless-stopped \
  --env-file .env \
  -v "$(pwd)/downloads:/app/downloads" \
  -v "$(pwd)/results:/app/results" \
  ai_agent python3 -u duplicatmain.py 
