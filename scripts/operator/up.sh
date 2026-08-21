#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "${project_root}"

if [ ! -f .env ]; then
  echo "Run scripts/operator/configure.sh first." >&2
  exit 1
fi

set -a
source .env
set +a

compose_files=(-f compose.operator.yaml)

if [ -n "${DISPLAY:-}" ]; then
  if ! command -v xauth >/dev/null 2>&1; then
    echo "xauth is required for RViz X11/XWayland access." >&2
    exit 1
  fi
  mkdir -p .docker/run
  touch .docker/run/xauthority
  chmod 600 .docker/run/xauthority
  xauth nlist "${DISPLAY}" | sed -e 's/^..../ffff/' | \
    xauth -f .docker/run/xauthority nmerge -
  compose_files+=(-f compose.operator.x11.yaml)
else
  echo "DISPLAY is not set. RViz requires X11 or XWayland for OGRE/GLX." >&2
  exit 1
fi

exec docker compose "${compose_files[@]}" up --build operator
