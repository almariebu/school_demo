#!/usr/bin/env bash
# Builds the custom image (frappe version-15 + school_demo) with frappe_docker's layered Containerfile.
set -euo pipefail
cd "$(dirname "$0")"

FRAPPE_DOCKER_DIR="${FRAPPE_DOCKER_DIR:-./frappe_docker}"
if [ ! -d "$FRAPPE_DOCKER_DIR" ]; then
  git clone --depth 1 https://github.com/frappe/frappe_docker "$FRAPPE_DOCKER_DIR"
fi

docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=APPS_JSON_BASE64="$(base64 -w0 apps.json)" \
  --tag="${CUSTOM_IMAGE:-school_demo}:${CUSTOM_TAG:-latest}" \
  --file="$FRAPPE_DOCKER_DIR/images/layered/Containerfile" \
  "$FRAPPE_DOCKER_DIR"
