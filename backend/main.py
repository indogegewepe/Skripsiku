from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, Ruang
from schemas import DosenSchema, MkGenapSchema, DataDosenSchema, HariSchema, JamSchema, RuangSchema, DataDosenCreate
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from sqlalchemy.orm import joinedload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
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
    try:
        return db.query(DataDosen)\
            .options(joinedload(DataDosen.dosen), joinedload(DataDosen.mk_genap))\
            .all()
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching data: {str(e)}"
        )

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

# Endpoint untuk menambahkan data dosen
@app.post("/data_dosen")
def create_data_dosen(data: DataDosenCreate, db: Session = Depends(get_db)):
    try:
        # Cek duplikasi data
        existing = db.query(DataDosen).filter(
            DataDosen.id_dosen == data.id_dosen,
            DataDosen.id_mk_genap == data.id_mk_genap
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Data already exists")
            
        new_data = DataDosen(**data.dict())
        db.add(new_data)
        db.commit()
        db.refresh(new_data)
        return new_data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint untuk menghapus data dosen
@app.delete("/dosen/{id_dosen}/{id_mk_genap}")
def delete_data_dosen(id_dosen: int, id_mk_genap: int, db: Session = Depends(get_db)):
    try:
        data = db.query(DataDosen).filter(
            DataDosen.id_dosen == id_dosen,
            DataDosen.id_mk_genap == id_mk_genap
        ).first()
        
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        db.delete(data)
        db.commit()
        return {"message": "Data deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
