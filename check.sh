	#!/bin/bash

echo "Checking контейнер..."

# Внутри docker_check.sh команда должна выглядеть так:
docker exec -it my_ai_bot yt-dlp --list-formats \
  --cookies downloads/cookies.txt \
  --js-runtime node \
  --remote-components ejs:github \
  https://www.youtube.com/watch?v=M5y69v1RbU0
