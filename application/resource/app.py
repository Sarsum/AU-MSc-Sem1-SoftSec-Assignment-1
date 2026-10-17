from cachetools import TTLCache
from contextlib import asynccontextmanager
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import get_db, engine, Base, DBBucket, DBTransaction
from utils import load_keys, decode_token
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Any, Tuple

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
def get_system_token(token: str = Depends(oauth2_scheme)) -> Tuple[int, str]:
    if token in used_system_tokens:
        raise HTTPException(401, "Token has already been used.")

    payload = decode_token(token)
    if payload == None:
        raise HTTPException(401, "Invalid or expired token!")
    if payload["type"] != "system":
        raise HTTPException(403, "Only user tokens supported!")
    action = payload["action"]
    if not action:
        raise HTTPException(403, "System token is missing action!")
    user_id = payload["user_id"]
    if not user_id:
        raise HTTPException(403, "System token is missing user_id!")
    used_system_tokens[token] = True
    return (user_id, action)

class BucketCreate(BaseModel):
    bucket_name: str

@app.post("/bucket")
def create_bucket(bucket: BucketCreate, token: Tuple[int, str] = Depends(get_system_token), db: Session = Depends(get_db)):
    user_id, action = token
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

    return {"success": True, "message": "Successfully created bucket!", "data": db_bucket}

class TransactionAdd(BaseModel):
    bucket_name: str
    amount: Decimal = Field(
        max_digits=10,
        decimal_places=2
    )

@app.post("/transaction")
def add_transaction(transaction: TransactionAdd, token: Tuple[int, str] = Depends(get_system_token), db: Session = Depends(get_db)):
    user_id, _ = token
    bucket = db.query(DBBucket).where(DBBucket.name == transaction.bucket_name, DBBucket.user_id == user_id).first()
    if not bucket:
        raise HTTPException(404, "Bucket not found!")

    db_transaction = DBTransaction(bucket_id=bucket.id, amount=transaction.amount)
    db.add(db_transaction)
    db.commit()
    return {"details": "Transaction added successfully!"}