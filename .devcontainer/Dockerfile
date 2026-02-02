# Copyright (c) Lumières Lausanne 2026
# See docs/copyright.md
#
# Custom devcontainer image to fix Yarn GPG error
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

# Remove broken Yarn repo and update apt
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update
