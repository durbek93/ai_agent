#!/bin/bash

echo "🚀 Запускаем ИИ-Агента..."

docker run -it --rm --gpus all --env-file .env \
  -v "$(pwd)/downloads:/app/downloads" \
  -v "$(pwd)/transcripts:/app/transcripts" \
  -v "$(pwd)/results:/app/results" \
  -v "$(pwd)/cache:/root/.cache/whisper" \
  ai_agent
