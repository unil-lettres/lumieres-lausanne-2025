#!/usr/bin/env bash

# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lumières.Lausanne is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# This copyright notice MUST APPEAR in all copies of the file.

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
