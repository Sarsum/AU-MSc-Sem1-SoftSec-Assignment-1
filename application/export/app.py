from cachetools import TTLCache
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from utils import load_keys, decode_token
from pydantic import BaseModel, Field
from typing import Tuple
import os
import requests
from csv_generator import format_to_csv

# tells FastAPI to look for a "Bearer" token in the headers
# tokenUrl is the endpoint where users login to get the token (for the swagger ui)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8000/login")

RESOURCES_BASE_URL = os.getenv("RESOURCES_BASE_URL", "http://localhost:8001")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_keys()

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
    if not "action" in payload:
        raise HTTPException(403, "System token is missing action!")
    action = payload["action"]
    if not "user_id" in payload:
        raise HTTPException(403, "System token is missing user_id!")
    user_id = payload["user_id"]
    if not "user_role" in payload:
        raise HTTPException(403, "System token is missing user_role!")
    user_role = payload["user_role"]
    used_system_tokens[token] = True
    return (user_id, action, user_role)

class ExportRequest(BaseModel):
    bucket_name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
    )
    export_token: str
    upload_token: str

def process_export_request(request: ExportRequest):
    headers = {
        "Authorization": f"Bearer {request.export_token}"
    }
    response = requests.get(f"{RESOURCES_BASE_URL}/bucket/{request.bucket_name}/transactions", headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve transactions for bucket '{request.bucket_name}'. Status code: {response.status_code}, Response: {response.text}")
        return

    transactions = response.json().get("data", [])
    csv_data = format_to_csv(["ID", "Amount", "Timestamp"], [t.values() for t in transactions])

    upload_headers = {
        "Authorization": f"Bearer {request.upload_token}",
        "Content-Type": "text/csv"
    }
    response = requests.post(f"{RESOURCES_BASE_URL}/exports/upload/{request.bucket_name}", headers=upload_headers, data=csv_data)
    if response.status_code != 200: 
        print(f"Failed to upload CSV for bucket '{request.bucket_name}'. Status code: {response.status_code}, Response: {response.text}")


@app.post("/export-transactions")
def get_transactions(request: ExportRequest, background_tasks: BackgroundTasks, token: Tuple[int, str, str] = Depends(get_system_token)):
    _, action, _ = token
    if action != "export_transactions":
        raise HTTPException(401, "Token does not allow transaction export!")
    # we assume that the export_token and upload_token are valid and do not check them at this point,
    # as this endpoint can only be called by the api service
    
    background_tasks.add_task(process_export_request, request)

    return {"details": f"Transaction export for bucket '{request.bucket_name}' has been queued!"}