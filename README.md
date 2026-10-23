# Preface
This is the repository for an assignment for the software security lecture. It contains intentionally planted security vulnerabilities and intends only as a proof of concept.

**Hence, it should NOT be used in this state in any production environment.**

# Application Overview
A **budget application** to manage income and expenses across multiple named buckets / accounts per user. The user role can create and delete its own buckets and add / remove expenses from it, while the admin role can delete all buckets. Lastly, the expenses of a bucket can be exported as a CSV-file, which offers the possibility to use a dependency for the generation of a CSV file.

# Building / Running

## Initial Preparation
To generate the cryptographic key pair used for the JWT tokens:
```bash
openssl genpkey -algorithm ed25519 -out private.pem
openssl pkey -in private.pem -pubout -out public.pem
```

## Running
```bash
podman compose up -d
```
Alternatively:
```bash
docker compose up -d
```

# Seeding & Automatic verification / usage of API endpoint
```bash
bash seed.sh
```

# Manual Testing
## Registration
```bash
curl -sS -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"<username>\",\"password\":\"<password>\"}"
```

## Login
```bash
curl -sS -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"<username>\",\"password\":\"<password>\"}"
```

## Bucket Creation
```bash
curl -sS -X POST "http://localhost:8000/bucket" \
  -H "Authorization: Bearer <user-jwt>" \
  -H "Content-Type: application/json" \
  -d "{\"bucket_name\":\"<bucket-name>\"}"
```

## Adding Transation to Bucket
```bash
curl -sS -X POST "http://localhost:8000/transaction" \
  -H "Authorization: Bearer <user-jwt>" \
  -H "Content-Type: application/json" \
  -d "{\"bucket_name\":\"<bucket-name>\",\"amount\":\"12.50\"}"
```

## Requesting / initializing bucket export
```bash
curl -sS -X POST "http://localhost:8000/bucket/<bucket-name>/export" \
  -H "Authorization: Bearer <user-jwt>"
```

## Downloading finished export
```bash
curl -sS -X GET "http://localhost:8000/bucket/exports?bucket_name=<bucket-name>" \
  -H "Authorization: Bearer <user-jwt>"
```

## Admin Action: Reassign Bucket
```bash
curl -sS -X POST "http://localhost:8000/bucket/<bucket-name>/reassign" \
  -H "Authorization: Bearer <admin-jwt>" \
  -H "Content-Type: application/json" \
  -d "{\"new_user_id\":<other-user-id>}"
```