#!/usr/bin/env bash
# Copyright (c) 2025 Lumières Lausanne
# See docs/copyright.md

# Usage: wait-for-it.sh host:port [-- command args]
# Waits for a host:port to be available, then runs the command.

set -e

HOST_PORT="$1"
shift

HOST="${HOST_PORT%%:*}"
PORT="${HOST_PORT##*:}"

TIMEOUT=60

for i in $(seq 1 $TIMEOUT); do
    if nc -z "$HOST" "$PORT"; then
        echo "Host $HOST:$PORT is available."
        exec "$@"
        exit 0
    fi
    echo "Waiting for $HOST:$PORT... ($i/$TIMEOUT)"
    sleep 1
done

echo "Timeout waiting for $HOST:$PORT"
exit 1
