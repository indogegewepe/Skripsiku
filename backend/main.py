import json
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from typing import List

from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, PreferensiDosen, Ruang
from schemas import DosenSchema, MkGenapSchema, DosenWithMkSchema, HariSchema, JamSchema, RuangSchema, DataDosenCreate, DataDosenSchema, ScheduleRequest
from process import run_gwo_optimization, create_random_schedule, calculate_fitness, collect_conflicts

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

@app.get("/dosen", response_model=list[DosenSchema])
def get_all_dosen(db: Session = Depends(get_db)):
    return db.query(Dosen).order_by(Dosen.id_dosen).all()

@app.get("/dosen/{id_dosen}", response_model=DosenSchema)
def get_dosen_by_id(id_dosen: int, db: Session = Depends(get_db)):
    dosen = db.query(Dosen).filter(Dosen.id_dosen == id_dosen).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")
    return dosen

@app.get("/mk_genap", response_model=list[MkGenapSchema])
def get_all_mk_genap(db: Session = Depends(get_db)):
    return db.query(MkGenap).order_by(MkGenap.smt).all()

@app.get("/data_dosen", response_model=List[DosenWithMkSchema])
def get_all_data_dosen(db: Session = Depends(get_db)):
    try:
        all_dosen = db.query(Dosen).all()
        data = db.query(DataDosen)\
            .options(
                joinedload(DataDosen.dosen),
                joinedload(DataDosen.mk_genap)
            )\
            .all()
        dosen_map = defaultdict(lambda: {"mata_kuliah": []})
        for dosen in all_dosen:
            dosen_map[dosen.id_dosen] = {
                "id_dosen": dosen.id_dosen,
                "nama_dosen": dosen.nama_dosen,
                "mata_kuliah": []
            }
        for item in data:
            dosen_id = item.id_dosen
            if item.mk_genap:
                dosen_map[dosen_id]["mata_kuliah"].append({
                    "kelas": item.kelas,
                    "id_mk_genap": item.mk_genap.id_mk_genap,
                    "nama_mk_genap": item.mk_genap.nama_mk_genap,
                    "smt": item.mk_genap.smt,
                    "sks": item.mk_genap.sks,
                    "sifat": item.mk_genap.sifat,
                    "metode": item.mk_genap.metode
                })
        result = list(dosen_map.values())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching data: {str(e)}"
        )
    
@app.get("/tbl_data_dosen", response_model=List[DataDosenSchema])
def get_selected_fields(db: Session = Depends(get_db)):
    return db.query(DataDosen.id_dosen, DataDosen.id_mk_genap, DataDosen.kelas).all()

@app.get("/hari", response_model=list[HariSchema])
def get_all_hari(db: Session = Depends(get_db)):
    return db.query(Hari).all()

@app.get("/jam", response_model=list[JamSchema])
def get_all_jam(db: Session = Depends(get_db)):
    return db.query(Jam).all()

@app.get("/ruang", response_model=list[RuangSchema])
def get_all_ruang(db: Session = Depends(get_db)):
    return db.query(Ruang).all()

@app.get("/preferensi_dosen")
def get_preferensi_dosen(db: Session = Depends(get_db)):
    return db.query(PreferensiDosen).all()

@app.post("/data_dosen")
def create_data_dosen(data: DataDosenCreate, db: Session = Depends(get_db)):
    try:
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
    
@app.delete("/data_dosen/{id_dosen}/{id_mk_genap}")
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

@app.post("/generate-schedule/")
def generate_schedule(request: ScheduleRequest, db: Session = Depends(get_db)):
    try:
        best_schedule, best_fitness = run_gwo_optimization(
            create_random_schedule,
            lambda sol: calculate_fitness(sol, db),
            lambda sol: collect_conflicts(sol, db),
            request.population_size,
            request.max_iterations
        )
        with open('./output.json', 'w') as f:
            json.dump(best_schedule, f, indent=4)
        return {
            "fitness": best_fitness
        }
    except Exception as e:
        import traceback
        print(f"Error in generate_schedule: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate schedule: {str(e)}")

@app.get("/schedule")
def get_schedule():
    import json
    with open("output.json") as f:
        data = json.load(f)
    return data
