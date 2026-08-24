#!/usr/bin/env bash
set -euo pipefail

if [[ "${ROS_DISTRO:-}" != "jazzy" ]]; then
  echo "Source ROS 2 Jazzy first: source /opt/ros/jazzy/setup.bash" >&2
  exit 1
fi

for command_name in vcs rosdep colcon; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Missing required command: ${command_name}" >&2
    exit 1
  fi
done

THIS_FILE=${BASH_SOURCE[0]}
THIS_PROJECT_ROOT=$(realpath "$(dirname "$(realpath "${THIS_FILE}")")")

# Install ROS2 dependency
## From git repos
echo "Start to install dependent repos(vcs)"
colcon_ws=$(realpath "${THIS_PROJECT_ROOT}/../..")

vcs import \
  --recursive \
  --skip-existing \
  --input "${THIS_PROJECT_ROOT}/build_depends.repos" \
  "${colcon_ws}/src"

## From apt repositories
echo "Start to install dependent binarys(rosdep )"
rosdep update
rosdep install -r -y -i \
  --from-paths "${colcon_ws}/src" \
  --rosdistro jazzy

unset colcon_ws
unset THIS_FILE
unset THIS_PROJECT_ROOT
unset THIS_REPOSITORY_NAME
echo "finish to install dependencies!"
