#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "${project_root}"

if [ ! -f .env ]; then
  echo "Run scripts/operator/configure.sh first." >&2
  exit 1
fi

compose_files=(-f compose.operator.yaml)

gamepad_device=$(sed -n 's/^GAMEPAD_DEVICE=//p' .env | tail -n 1)
if [ -n "${gamepad_device}" ]; then
  if [ ! -c "${gamepad_device}" ]; then
    echo "Configured gamepad device disappeared. Reconnect USB and rerun configure.sh." >&2
    exit 1
  fi
  compose_files+=(-f compose.operator.gamepad.yaml)
fi

display_name=${DISPLAY:-$(sed -n 's/^DISPLAY=//p' .env | tail -n 1)}

if [ -n "${display_name}" ]; then
  export DISPLAY=${display_name}
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
  if [ -d /dev/dri ]; then
    compose_files+=(-f compose.operator.gpu.yaml)
  else
    echo "No /dev/dri found; using Mesa software rendering."
    compose_files+=(-f compose.operator.software-rendering.yaml)
  fi
else
  echo "DISPLAY is not set. RViz requires X11 or XWayland for OGRE/GLX." >&2
  exit 1
fi

exec docker compose "${compose_files[@]}" up --build operator
