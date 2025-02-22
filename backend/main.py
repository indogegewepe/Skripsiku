from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Dosen, MkGenap, DataDosen, Hari, Jam, Ruang
from schemas import DosenSchema, MkGenapSchema, DataDosenSchema, HariSchema, JamSchema, RuangSchema
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Bisa diganti dengan ["http://localhost:3000"] untuk lebih aman
    allow_credentials=True,
    allow_methods=["*"],  # Bisa disesuaikan ["GET", "POST", "DELETE", "PUT"]
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Hello, FastAPI!"}

# Endpoint untuk mendapatkan semua dosen
@app.get("/dosen", response_model=list[DosenSchema])
def get_all_dosen(db: Session = Depends(get_db)):
    return db.query(Dosen).all()

# Endpoint untuk mendapatkan semua mata kuliah genap
@app.get("/mk_genap", response_model=list[MkGenapSchema])
def get_all_mk_genap(db: Session = Depends(get_db)):
    return db.query(MkGenap).all()

# Endpoint untuk mendapatkan semua data dosen
@app.get("/data_dosen", response_model=list[DataDosenSchema])
def get_all_data_dosen(db: Session = Depends(get_db)):
    return db.query(DataDosen).all()

# Endpoint untuk mendapatkan semua hari
@app.get("/hari", response_model=list[HariSchema])
def get_all_hari(db: Session = Depends(get_db)):
    return db.query(Hari).all()

# Endpoint untuk mendapatkan semua jam
@app.get("/jam", response_model=list[JamSchema])
def get_all_jam(db: Session = Depends(get_db)):
    return db.query(Jam).all()

# Endpoint untuk mendapatkan semua ruang
@app.get("/ruang", response_model=list[RuangSchema])
def get_all_ruang(db: Session = Depends(get_db)):
    return db.query(Ruang).all()
