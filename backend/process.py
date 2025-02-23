from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Hari, Jam, Ruang, DataDosen

app = FastAPI()

