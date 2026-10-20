from cachetools import TTLCache
from contextlib import asynccontextmanager
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer
from database import get_db, engine, Base, DBBucket, DBTransaction
from utils import load_keys, decode_token
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict, Field
from typing import Tuple
from datetime import datetime
import os

# tells FastAPI to look for a "Bearer" token in the headers
# tokenUrl is the endpoint where users login to get the token (for the swagger ui)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8000/login")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_keys()
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # yield while running app
    yield

    print("Shutting down")

app = FastAPI(lifespan=lifespan)

used_system_tokens = TTLCache(maxsize=10000, ttl=600)

# returns the user_id and action assigned to this system token
def get_system_token(token: str = Depends(oauth2_scheme)) -> Tuple[int, str, str]:
    if token in used_system_tokens:
        raise HTTPException(401, "Token has already been used.")

    payload = decode_token(token)
    if payload == None:
        raise HTTPException(401, "Invalid or expired token!")
    if payload["type"] != "system":
        raise HTTPException(403, "Only user tokens supported!")
    if "action" not in payload:
        raise HTTPException(403, "System token is missing action!")
    action = payload["action"]
    if "user_id" not in payload:
        raise HTTPException(403, "System token is missing user_id!")
    user_id = payload["user_id"]
    if "user_role" not in payload:
        raise HTTPException(403, "System token is missing user_role!")
    user_role = payload["user_role"]
    used_system_tokens[token] = True
    return (user_id, action, user_role)

class BucketCreate(BaseModel):
    bucket_name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )

@app.post("/bucket")
def create_bucket(bucket: BucketCreate, token: Tuple[int, str, str] = Depends(get_system_token), db: Session = Depends(get_db)):
    user_id, action, _ = token
    if action != "create_bucket":
        raise HTTPException(401, "Token does not allow bucket creation!")

    if bucket.bucket_name == "":
        raise HTTPException(400, "bucket_name cannot be empty!")

    if db.query(DBBucket).filter(DBBucket.name == bucket.bucket_name).first():
        raise HTTPException(400, "This bucket_name is already taken!")

    db_bucket = DBBucket(name=bucket.bucket_name, user_id=user_id)
    db.add(db_bucket)
    db.commit()
    db.refresh(db_bucket)

    return {"details": "Successfully created bucket!", "data": db_bucket}

class BucketReassign(BaseModel):
    new_user_id: int = Field(
        gt=0
    )

@app.post("/bucket/{bucket_name}/reassign")
def reassign_bucket(reassign: BucketReassign, bucket_name: str, token: Tuple[int, str, str] = Depends(get_system_token), db: Session = Depends(get_db)):
    _, action, user_role = token
    if user_role != "admin":
        raise HTTPException(403, "Only admin users can reassign buckets!")
    if action != "reassign_bucket":
        raise HTTPException(401, "Token does not allow bucket reassignment!")

    bucket = db.query(DBBucket).filter(DBBucket.name == bucket_name).first()
    if not bucket:
        raise HTTPException(404, "Bucket not found!")

    bucket.user_id = reassign.new_user_id
    # TODO: audit logs for reassign / admin activities
    db.commit()
    db.refresh(bucket)

    return {"details": "Successfully reassigned bucket!", "data": bucket}

class Transaction(BaseModel):
    id: int
    amount: float
    timestamp: datetime

    # tells pydantic to read the data from the attributes of the SQLAlchemy model
    model_config = ConfigDict(from_attributes=True)
class TransactionsResponse(BaseModel):
    data: list[Transaction]

@app.get("/bucket/{bucket_name}/transactions", response_model=TransactionsResponse)
def get_transactions(bucket_name: str, token: Tuple[int, str, str] = Depends(get_system_token), db: Session = Depends(get_db)):
    _, action, _ = token
    if action != "get_transactions":
        raise HTTPException(401, "Token does not allow getting transactions!")
    bucket = db.query(DBBucket).where(DBBucket.name == bucket_name).first()
    if not bucket:
        raise HTTPException(404, "Bucket not found!")

    transactions = db.query(DBTransaction).where(DBTransaction.bucket_id == bucket.id).all()
    return {"data": transactions}

class TransactionAdd(BaseModel):
    bucket_name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    amount: Decimal = Field(
        max_digits=10,
        decimal_places=2
    )

@app.post("/transaction")
def add_transaction(transaction: TransactionAdd, token: Tuple[int, str, str] = Depends(get_system_token), db: Session = Depends(get_db)):
    user_id, action, _ = token
    if action != "add_transaction":
        raise HTTPException(401, "Token does not allow adding transactions!")
    bucket = db.query(DBBucket).where(DBBucket.name == transaction.bucket_name, DBBucket.user_id == user_id).first()
    if not bucket:
        raise HTTPException(404, "Bucket not found!")

    db_transaction = DBTransaction(bucket_id=bucket.id, amount=transaction.amount)
    db.add(db_transaction)
    db.commit()
    return {"details": "Transaction added successfully!"}

@app.post("/exports/upload/{bucket_name}")
async def receive_export(bucket_name: str, request: Request, token: Tuple[int, str, str] = Depends(get_system_token)):
    if request.headers.get("content-type") != "text/csv":
        raise HTTPException(status_code=415, detail="Unsupported Media Type. Expected text/csv")

    csv_bytes = await request.body()

    if not csv_bytes:
        raise HTTPException(status_code=400, detail="Empty payload")

    save_directory = f"./exports/user_{token[0]}"
    os.makedirs(save_directory, exist_ok=True)
    file_path = os.path.join(save_directory, f"{bucket_name}")

    # 4. Write the bytes to a file
    with open(file_path, "wb") as f:
        f.write(csv_bytes)

    return {"message": "CSV saved successfully", "file_path": file_path}

@app.get("/exports")
async def get_export(bucket_name: str, token: Tuple[int, str, str] = Depends(get_system_token)):
    user_id, action, _ = token
    print(bucket_name)
    if action != "download_export":
        raise HTTPException(401, "Token does not allow downloading export!")

    # intentionally building the file path this way to showcase file path manipulation vulnerabilities
    file_path = os.path.join(f"./exports/user_{user_id}", f"{bucket_name}")

    print(f"Looking for file at: {file_path}")  # Debugging line

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    with open(file_path, "rb") as f:
        csv_bytes = f.read()

    return Response(content=csv_bytes, media_type="text/csv")
