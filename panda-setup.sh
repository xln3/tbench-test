#!/bin/bash
set -e

apt-get update
apt-get install -y curl unzip

# Install Deno directly from release binary
DENO_DIR=/root/.deno
mkdir -p "$DENO_DIR/bin"

DENO_URL="https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip"

# Retry download up to 3 times with HTTP/1.1 fallback
for i in 1 2 3; do
  echo "Downloading Deno (attempt $i)..."
  if curl -fsSL --http1.1 --retry 3 --retry-delay 2 -o /tmp/deno.zip "$DENO_URL"; then
    break
  fi
  if [ "$i" -eq 3 ]; then
    echo "Failed to download Deno after 3 attempts"
    exit 1
  fi
  sleep 2
done

unzip -o /tmp/deno.zip -d "$DENO_DIR/bin/"
chmod +x "$DENO_DIR/bin/deno"
export PATH="$DENO_DIR/bin:$PATH"

# Verify
deno --version

# Cache PANDA dependencies
cd /panda
deno cache mod.ts
