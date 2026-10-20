#!/usr/bin/env bash

set -e

API_URL="${API_URL:-http://localhost:8000}"
RUN_ID="${1:-$(date +%s)}"
PASSWORD="${PASSWORD:-password}"

ADMIN="admin-${RUN_ID}"
USER_ONE="user-one-${RUN_ID}"
USER_TWO="user-two-${RUN_ID}"
BUCKET="bucket-${RUN_ID}"

echo "Using run ID: ${RUN_ID}"
echo "Using API: ${API_URL}"

# Register an admin and two regular users.
curl -sS -X POST "${API_URL}/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${ADMIN}\",\"password\":\"${PASSWORD}\",\"role\":\"admin\"}"
echo

curl -sS -X POST "${API_URL}/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USER_ONE}\",\"password\":\"${PASSWORD}\"}"
echo

curl -sS -X POST "${API_URL}/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USER_TWO}\",\"password\":\"${PASSWORD}\"}"
echo

# Log in and keep the returned JWTs for authenticated requests.
ADMIN_TOKEN="$(
  curl -sS -X POST "${API_URL}/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${ADMIN}\",\"password\":\"${PASSWORD}\"}" |
    jq -r '.data'
)"

USER_ONE_TOKEN="$(
  curl -sS -X POST "${API_URL}/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${USER_ONE}\",\"password\":\"${PASSWORD}\"}" |
    jq -r '.data'
)"

USER_TWO_LOGIN="$(
  curl -sS -X POST "${API_URL}/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${USER_TWO}\",\"password\":\"${PASSWORD}\"}"
)"
USER_TWO_TOKEN="$(jq -r '.data' <<<"${USER_TWO_LOGIN}")"
USER_TWO_ID="$(
  jq -r '.data' <<<"${USER_TWO_LOGIN}" |
    cut -d. -f2 |
    tr '_-' '/+' |
    base64 -d 2>/dev/null |
    jq -r '.user_id'
)"

# Create a bucket and add a transaction as the first user.
curl -sS -X POST "${API_URL}/bucket" \
  -H "Authorization: Bearer ${USER_ONE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"bucket_name\":\"${BUCKET}\"}"
echo

curl -sS -X POST "${API_URL}/transaction" \
  -H "Authorization: Bearer ${USER_ONE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"bucket_name\":\"${BUCKET}\",\"amount\":\"12.50\"}"
echo

# Reassign the bucket as the admin.
curl -sS -X POST "${API_URL}/bucket/${BUCKET}/reassign" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"new_user_id\":${USER_TWO_ID}}"
echo

# Add a transaction as the second user after reassignment.
curl -sS -X POST "${API_URL}/transaction" \
  -H "Authorization: Bearer ${USER_TWO_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"bucket_name\":\"${BUCKET}\",\"amount\":\"7.25\"}"
echo

# Request an export and then download it.
curl -sS -X POST "${API_URL}/bucket/${BUCKET}/export" \
  -H "Authorization: Bearer ${USER_TWO_TOKEN}"
echo

sleep 1

curl -sS -X GET "${API_URL}/exports?bucket_name=${BUCKET}" \
  -H "Authorization: Bearer ${USER_TWO_TOKEN}"
echo
