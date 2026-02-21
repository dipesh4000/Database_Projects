from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from .. import models, schemas, utils

router = APIRouter(
    prefix="/vote",
    tags=['Vote']
)


@router.post("/")
def create():
    return {"message": "vote"}