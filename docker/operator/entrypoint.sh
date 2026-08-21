#!/usr/bin/env bash
set -e

source /opt/ros/jazzy/setup.bash
source /opt/sanehal_operator_ws/install/setup.bash

if [ -n "${XDG_RUNTIME_DIR:-}" ]; then
  mkdir -p "${XDG_RUNTIME_DIR}"
  chmod 0700 "${XDG_RUNTIME_DIR}"
fi

if [ -f /workspaces/sanehal/install/setup.bash ]; then
  source /workspaces/sanehal/install/setup.bash
fi

exec "$@"
