#!/bin/sh
# entrypoint.sh

set -e

export DATABASE_URL="postgresql://${DB_USER:?Variable not set}:${DB_PASSWORD:?Variable not set}@${DB_ENDPOINT:?Variable not set}/${DB_NAME:?Variable not set}?ssl=require"

exec "$@"