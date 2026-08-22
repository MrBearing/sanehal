ARG ROS_IMAGE=osrf/ros:jazzy-desktop@sha256:e1c05248ece3bc328386d0509a041a97a5de872a5606418118748875c539c66f
FROM ${ROS_IMAGE}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG USER_NAME=operator
ARG USER_UID=1000
ARG USER_GID=1000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1-mesa-dri \
        mesa-utils \
        git \
        python3-colcon-common-extensions \
        python3-rosdep \
        python3-vcstool \
        qtwayland5 \
        ros-jazzy-joy \
        ros-jazzy-slam-toolbox \
        ros-jazzy-tf2-tools \
    && rm -rf /var/lib/apt/lists/* \
    && if ! getent group "${USER_GID}" >/dev/null; then groupadd --gid "${USER_GID}" sanehal; fi \
    && usermod --uid "${USER_UID}" --gid "${USER_GID}" --login "${USER_NAME}" \
        --home "/home/${USER_NAME}" --move-home ubuntu \
    && usermod --groups '' "${USER_NAME}"

WORKDIR /opt/sanehal_operator_ws
COPY docker/operator/operator_depends.repos operator_depends.repos
RUN mkdir -p src \
    && vcs import src < operator_depends.repos
COPY sanehal_operator src/sanehal_operator

RUN source /opt/ros/jazzy/setup.bash \
    && rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy \
    && colcon build --merge-install --packages-up-to sanehal_operator p9n_test \
    && rm -rf build log \
    && chown -R "${USER_UID}:${USER_GID}" /opt/sanehal_operator_ws \
    && mkdir -p /workspaces/sanehal/build /workspaces/sanehal/install /workspaces/sanehal/log \
    && chown -R "${USER_UID}:${USER_GID}" /workspaces

COPY docker/operator/entrypoint.sh /usr/local/bin/sanehal-operator-entrypoint
RUN chmod 0755 /usr/local/bin/sanehal-operator-entrypoint

USER ${USER_NAME}
WORKDIR /home/${USER_NAME}
ENTRYPOINT ["/usr/local/bin/sanehal-operator-entrypoint"]
CMD ["ros2", "launch", "sanehal_operator", "operator.launch.py"]
