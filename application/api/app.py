from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import requests
from sqlalchemy.orm import Session
from typing import Tuple
import os

from database import get_db, engine, Base, DBUser
from utils import hash_password, verify_password, DUMMY_HASH, load_keys, create_token, decode_token

# tells FastAPI to look for a "Bearer" token in the headers
# tokenUrl is the endpoint where users login to get the token (for the swagger ui)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

RESOURCES_BASE_URL = os.getenv("RESOURCES_BASE_URL", "http://localhost:8001")

# lifespan context manager to create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_keys()
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # yield while running app
    yield

    print("Shutting down")

app = FastAPI(lifespan=lifespan)

class User(BaseModel):
    username: str
    password: str
    role: str = "user"

@app.post("/register")
def register_user(user: User, db: Session = Depends(get_db)):
    existing_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if existing_user:
        raise HTTPException(400, "This username already exists!")
    user_dict = user.model_dump()
    # Rewrite password to hashed password for safe db storage 
    user_dict['password'] = hash_password(user.password)

    db_user = DBUser(**user_dict)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"success": True, "message": "User created successfully!"}

@app.post("/login")
def login_user(user: User, db: Session = Depends(get_db)):
    # use dummy password hash in case user not found to avoid timing attacks
    password_hash = DUMMY_HASH
    db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if db_user:
        password_hash = db_user.password

    # compute the hash comparison before checking the result, to avoid another timing attack
    pw_match = verify_password(user.password, password_hash)
    if not pw_match or not db_user:
        raise HTTPException(400, "The provided password is not correct or the user does not exist")

    token = create_token("user", db_user.id, db_user.role, {"username": db_user.username})

    return {"success": True, "message": "Successfully logged in!", "data": token}

def get_current_user(token: str = Depends(oauth2_scheme)) -> Tuple[int, str]:
    payload = decode_token(token)
    if payload == None:
        raise HTTPException(401, "Invalid or expired token.")
    if payload["type"] != "user":
        raise HTTPException(403, "Only user tokens supported!")
    if not "user_id" in payload:
        raise HTTPException(401, "User id not present!")
    user_id = payload["user_id"]
    if not "user_role" in payload:
        raise HTTPException(401, "User role not present!")
    user_role = payload["user_role"]
    return user_id, user_role

def relay_request(url: str, token: str, json_body: dict):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, headers=headers, json=json_body)
    if not response.ok:
        try:
            error_detail = response.json().get("detail", response.text)
        except ValueError:
            error_detail = response.text
            
        # Re-raise the exact status code and message from the target app
        raise HTTPException(
            status_code=response.status_code,
            detail=error_detail
        )
    return response.json()

@app.post("/bucket")
def request_bucket_create(payload: dict = Body(...), current_user: Tuple[int, str] = Depends(get_current_user)):
    user_id, role = current_user
    system_token = create_token("system", user_id, role, {"action": "create_bucket"})
    return relay_request(url=f"{RESOURCES_BASE_URL}/bucket", token=system_token, json_body=payload)

@app.post("/transaction")
def request_add_transaction(payload: dict = Body(...), current_user: Tuple[int, str] = Depends(get_current_user)):
    user_id, role = current_user
    system_token = create_token("system", user_id, role, {"action": "add_transaction"})
    return relay_request(url=f"{RESOURCES_BASE_URL}/transaction", token=system_token, json_body=payload)

@app.post("/export/{bucket_id}")
def request_export(bucket_id: int, current_user: dict = Depends(get_current_user)):
    return ""