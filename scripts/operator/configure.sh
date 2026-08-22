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

gamepad_by_id=${GAMEPAD_BY_ID:-}
gamepad_model=${GAMEPAD_MODEL:-DualSense}
gamepad_device=
input_gid=
if [ -n "${gamepad_by_id}" ]; then
  case "${gamepad_model}" in
    DualShock3|DualShock4|DualSense) ;;
    *)
      echo "GAMEPAD_MODEL must be DualShock3, DualShock4, or DualSense." >&2
      exit 1
      ;;
  esac
  case "${gamepad_by_id}" in
    /dev/input/by-id/*-event-joystick) ;;
    *)
      echo "GAMEPAD_BY_ID must be an absolute *-event-joystick path under /dev/input/by-id." >&2
      exit 1
      ;;
  esac
  if [ ! -L "${gamepad_by_id}" ]; then
    echo "Gamepad link does not exist: ${gamepad_by_id}" >&2
    exit 1
  fi
  gamepad_device=$(readlink -f "${gamepad_by_id}")
  case "${gamepad_device}" in
    /dev/input/event[0-9]*) ;;
    *)
      echo "Gamepad link must resolve to /dev/input/eventN, got: ${gamepad_device}" >&2
      exit 1
      ;;
  esac
  if [ ! -c "${gamepad_device}" ]; then
    echo "Gamepad event device is not a character device: ${gamepad_device}" >&2
    exit 1
  fi
  device_permissions=$(stat -c '%A' "${gamepad_device}")
  if [ "${device_permissions:4:1}" != "r" ]; then
    echo "Gamepad event device is not group-readable: ${gamepad_device}" >&2
    exit 1
  fi
  input_gid=$(stat -c '%g' "${gamepad_device}")
  if [ "${input_gid}" = "0" ]; then
    echo "Refusing gamepad device owned by root group (GID 0): ${gamepad_device}" >&2
    echo "Fix the host udev/input group assignment before enabling teleop." >&2
    exit 1
  fi
fi

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
  echo "GAMEPAD_BY_ID=${gamepad_by_id}"
  echo "GAMEPAD_DEVICE=${gamepad_device}"
  echo "GAMEPAD_MODEL=${gamepad_model}"
  echo "INPUT_GID=${input_gid}"
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
if [ -n "${gamepad_device}" ]; then
  echo "Selected ${gamepad_model} at ${gamepad_by_id} (${gamepad_device}, GID ${input_gid})."
fi
echo "Use the same ROS_DOMAIN_ID and RMW_IMPLEMENTATION on the Robot."
