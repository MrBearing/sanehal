#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
env_file="${project_root}/.env"
domain_id=${ROS_DOMAIN_ID:-42}

group_id() {
  local group_name=$1
  getent group "${group_name}" | cut -d: -f3
}

video_gid=$(group_id video || true)
render_gid=$(group_id render || true)
video_gid=${video_gid:-$(stat -c '%g' /dev/dri/card0 2>/dev/null || echo 0)}
render_gid=${render_gid:-$(stat -c '%g' /dev/dri/renderD128 2>/dev/null || echo "${video_gid}")}

umask 077
{
  echo "ROS_IMAGE=${ROS_IMAGE:-osrf/ros:jazzy-desktop@sha256:e1c05248ece3bc328386d0509a041a97a5de872a5606418118748875c539c66f}"
  echo "ROS_DOMAIN_ID=${domain_id}"
  echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
  echo "ROS_AUTOMATIC_DISCOVERY_RANGE=${ROS_AUTOMATIC_DISCOVERY_RANGE:-SUBNET}"
  echo "ROS_STATIC_PEERS=${ROS_STATIC_PEERS:-}"
  echo "HOST_UID=$(id -u)"
  echo "HOST_GID=$(id -g)"
  echo "VIDEO_GID=${video_gid}"
  echo "RENDER_GID=${render_gid}"
  echo "DISPLAY=${DISPLAY:-}"
  echo "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-}"
  echo "XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-}"
} > "${env_file}"

if [ -n "${DISPLAY:-}" ]; then
  if ! command -v xauth >/dev/null 2>&1; then
    echo "xauth is required to prepare authenticated X11/XWayland access." >&2
    exit 1
  fi
  mkdir -p "${project_root}/.docker/run"
  touch "${project_root}/.docker/run/xauthority"
  chmod 600 "${project_root}/.docker/run/xauthority"
  xauth nlist "${DISPLAY}" | sed -e 's/^..../ffff/' | \
    xauth -f "${project_root}/.docker/run/xauthority" nmerge -
fi

echo "Wrote ${env_file} with ROS_DOMAIN_ID=${domain_id}."
echo "Use the same ROS_DOMAIN_ID and RMW_IMPLEMENTATION on the Robot."
