import asyncio
from io import BytesIO
import json
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import pandas as pd
from sqlalchemy.orm import Session, joinedload
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from typing import List

from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, PreferensiDosen, PreferensiProdi, Ruang
from schemas import DosenSchema, MkGenapSchema, DosenWithMkSchema, HariSchema, JamSchema, PreferensiSchema, RuangSchema, DataDosenCreate, DataDosenSchema, ScheduleRequest
from process import run_gwo_optimization, create_random_schedule, calculate_fitness, collect_conflicts

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

log_clients = []

async def broadcast_log(message: str):
    # Buat list untuk menyimpan client yang sudah tertutup
    disconnected = []
    for client in log_clients:
        try:
            await client.send_text(message)
        except RuntimeError as e:
            print(f"WebSocket client disconnected: {e}")
            disconnected.append(client)
    for client in disconnected:
        log_clients.remove(client)


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    log_clients.append(websocket)
    try:
        while True:
            await asyncio.sleep(3600)
    except WebSocketDisconnect:
        log_clients.remove(websocket)

@app.get("/dosen", response_model=list[DosenSchema])
def get_all_dosen(db: Session = Depends(get_db)):
    return db.query(Dosen).order_by(Dosen.id_dosen).all()

@app.get("/dosen/{id_dosen}", response_model=DosenSchema)
def get_dosen_by_id(id_dosen: int, db: Session = Depends(get_db)):
    dosen = db.query(Dosen).filter(Dosen.id_dosen == id_dosen).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")
    return dosen

@app.post("/dosen", response_model=DosenSchema)
def create_dosen(dosen: DosenSchema, db: Session = Depends(get_db)):
    try:
        new_dosen = Dosen(**dosen.dict())
        db.add(new_dosen)
        db.commit()
        db.refresh(new_dosen)
        return new_dosen
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/dosen/{id_dosen}")
def delete_dosen(id_dosen: int, db: Session = Depends(get_db)):
    try:
        dosen = db.query(Dosen).filter(Dosen.id_dosen == id_dosen).first()
        if not dosen:
            raise HTTPException(status_code=404, detail="Dosen not found")
        
        db.delete(dosen)
        db.commit()
        return {"message": "Dosen deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/dosen/{id_dosen}", response_model=DosenSchema)
def update_dosen(id_dosen: int, dosen: DosenSchema, db: Session = Depends(get_db)):
    try:
        db_dosen = db.query(Dosen).filter(Dosen.id_dosen == id_dosen).first()
        if not db_dosen:
            raise HTTPException(status_code=404, detail="Dosen not found")
        
        db_dosen.nama_dosen = dosen.nama_dosen
        db.commit()
        db.refresh(db_dosen)
        return db_dosen
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mk_genap", response_model=list[MkGenapSchema])
def get_all_mk_genap(db: Session = Depends(get_db)):
    return db.query(MkGenap).order_by(MkGenap.smt).all()

@app.get("/mk_genap/{id_mk_genap}", response_model=MkGenapSchema)
def get_mk_genap_by_id(id_mk_genap: int, db: Session = Depends(get_db)):
    mk_genap = db.query(MkGenap).filter(MkGenap.id_mk_genap == id_mk_genap).first()
    if not mk_genap:
        raise HTTPException(status_code=404, detail="Mata kuliah not found")
    return mk_genap

@app.post("/mk_genap", response_model=MkGenapSchema)
def create_mk_genap(mk_genap: MkGenapSchema, db: Session = Depends(get_db)):
    try:
        new_mk_genap = MkGenap(**mk_genap.dict())
        db.add(new_mk_genap)
        db.commit()
        db.refresh(new_mk_genap)
        return new_mk_genap
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/mk_genap/{id_mk_genap}")
def delete_mk_genap(id_mk_genap: int, db: Session = Depends(get_db)):
    try:
        mk_genap = db.query(MkGenap).filter(MkGenap.id_mk_genap == id_mk_genap).first()
        if not mk_genap:
            raise HTTPException(status_code=404, detail="Mata kuliah not found")
        
        db.delete(mk_genap)
        db.commit()
        return {"message": "Mata kuliah deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/mk_genap/{id_mk_genap}", response_model=MkGenapSchema)
def update_mk_genap(id_mk_genap: int, mk_genap: MkGenapSchema, db: Session = Depends(get_db)):
    try:
        db_mk_genap = db.query(MkGenap).filter(MkGenap.id_mk_genap == id_mk_genap).first()
        if not db_mk_genap:
            raise HTTPException(status_code=404, detail="Mata kuliah not found")
        
        db_mk_genap.nama_mk_genap = mk_genap.nama_mk_genap
        db_mk_genap.smt = mk_genap.smt
        db_mk_genap.sks = mk_genap.sks
        db_mk_genap.sifat = mk_genap.sifat
        db_mk_genap.metode = mk_genap.metode
        db.commit()
        db.refresh(db_mk_genap)
        return db_mk_genap
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data_dosen", response_model=List[DosenWithMkSchema])
def get_all_data_dosen(db: Session = Depends(get_db)):
    try:
        # Ambil semua data dosen
        all_dosen = db.query(Dosen).all()
        # Buat mapping awal dengan key id_dosen
        dosen_map = {
            dosen.id_dosen: {
                "id_dosen": dosen.id_dosen,
                "nama_dosen": dosen.nama_dosen,
                "mata_kuliah": []
            }
            for dosen in all_dosen
        }
        # Ambil semua data data_dosen dengan memuat relasi dosen dan mk_genap
        data = db.query(DataDosen)\
            .options(
                joinedload(DataDosen.dosen),
                joinedload(DataDosen.mk_genap)
            )\
            .all()
        
        for item in data:
            dosen_id = item.id_dosen
            if item.mk_genap:
                # Tambahkan data mata kuliah (dengan kelas dari tabel data_dosen)
                dosen_map[dosen_id]["mata_kuliah"].append({
                    "kelas": item.kelas,
                    "id_mk_genap": item.mk_genap.id_mk_genap,
                    "nama_mk_genap": item.mk_genap.nama_mk_genap,
                    "smt": item.mk_genap.smt,
                    "sks": item.mk_genap.sks,
                    "sifat": item.mk_genap.sifat,
                    "metode": item.mk_genap.metode,
                    "kategori": item.mk_genap.kategori
                })
        
        result = list(dosen_map.values())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching data: {str(e)}"
        )
    
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

    
@app.get("/tbl_data_dosen", response_model=List[DataDosenSchema])
def get_selected_fields(db: Session = Depends(get_db)):
    return db.query(DataDosen.id_dosen, DataDosen.id_mk_genap, DataDosen.kelas).all()

@app.get("/hari", response_model=list[HariSchema])
def get_all_hari(db: Session = Depends(get_db)):
    return db.query(Hari).all()

@app.get("/hari/{id_hari}", response_model=HariSchema)
def get_hari_by_id(id_hari: int, db: Session = Depends(get_db)):
    hari = db.query(Hari).filter(Hari.id_hari == id_hari).first()
    if not hari:
        raise HTTPException(status_code=404, detail="Hari not found")
    return hari

@app.post("/hari", response_model=HariSchema)
def create_hari(hari: HariSchema, db: Session = Depends(get_db)):
    try:
        new_hari = Hari(**hari.dict())
        db.add(new_hari)
        db.commit()
        db.refresh(new_hari)
        return new_hari
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/hari/{id_hari}")
def delete_hari(id_hari: int, db: Session = Depends(get_db)):
    try:
        hari = db.query(Hari).filter(Hari.id_hari == id_hari).first()
        if not hari:
            raise HTTPException(status_code=404, detail="Hari not found")
        
        db.delete(hari)
        db.commit()
        return {"message": "Hari deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 
    
@app.put("/hari/{id_hari}", response_model=HariSchema)
def update_hari(id_hari: int, hari: HariSchema, db: Session = Depends(get_db)):
    try:
        db_hari = db.query(Hari).filter(Hari.id_hari == id_hari).first()
        if not db_hari:
            raise HTTPException(status_code=404, detail="Hari not found")
        
        db_hari.nama_hari = hari.nama_hari
        db.commit()
        db.refresh(db_hari)
        return db_hari
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jam", response_model=list[JamSchema])
def get_all_jam(db: Session = Depends(get_db)):
    return db.query(Jam).all()

@app.get("/jam/{id_jam}", response_model=JamSchema)
def get_jam_by_id(id_jam: int, db: Session = Depends(get_db)):
    jam = db.query(Jam).filter(Jam.id_jam == id_jam).first()
    if not jam:
        raise HTTPException(status_code=404, detail="Jam not found")
    return jam

@app.post("/jam", response_model=JamSchema)
def create_jam(jam: JamSchema, db: Session = Depends(get_db)):
    try:
        new_jam = Jam(**jam.dict())
        db.add(new_jam)
        db.commit()
        db.refresh(new_jam)
        return new_jam
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/jam/{id_jam}")
def delete_jam(id_jam: int, db: Session = Depends(get_db)):
    try:
        jam = db.query(Jam).filter(Jam.id_jam == id_jam).first()
        if not jam:
            raise HTTPException(status_code=404, detail="Jam not found")
        db.delete(jam)
        db.commit()
        return {"message": "Jam deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/jam/{id_jam}", response_model=JamSchema)
def update_jam(id_jam: int, jam: JamSchema, db: Session = Depends(get_db)):
    try:
        db_jam = db.query(Jam).filter(Jam.id_jam == id_jam).first()
        if not db_jam:
            raise HTTPException(status_code=404, detail="Jam not found")
        db_jam.jam_awal = jam.jam_awal
        db_jam.jam_akhir = jam.jam_akhir
        db.commit()
        db.refresh(db_jam)
        return db_jam
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ruang", response_model=list[RuangSchema])
def get_all_ruang(db: Session = Depends(get_db)):
    return db.query(Ruang).all()

@app.get("/ruang/{id_ruang}", response_model=RuangSchema)
def get_ruang_by_id(id_ruang: int, db: Session = Depends(get_db)):
    ruang = db.query(Ruang).filter(Ruang.id_ruang == id_ruang).first()
    if not ruang:
        raise HTTPException(status_code=404, detail="Ruang not found")
    return ruang

@app.post("/ruang", response_model=RuangSchema)
def create_ruang(ruang: RuangSchema, db: Session = Depends(get_db)):
    try:
        new_ruang = Ruang(**ruang.dict())
        db.add(new_ruang)
        db.commit()
        db.refresh(new_ruang)
        return new_ruang
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/ruang/{id_ruang}")
def delete_ruang(id_ruang: int, db: Session = Depends(get_db)):
    try:
        ruang = db.query(Ruang).filter(Ruang.id_ruang == id_ruang).first()
        if not ruang:
            raise HTTPException(status_code=404, detail="Ruang not found")
        
        db.delete(ruang)
        db.commit()
        return {"message": "Ruang deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/ruang/{id_ruang}", response_model=RuangSchema)
def update_ruang(id_ruang: int, ruang: RuangSchema, db: Session = Depends(get_db)):
    try:
        db_ruang = db.query(Ruang).filter(Ruang.id_ruang == id_ruang).first()
        if not db_ruang:
            raise HTTPException(status_code=404, detail="Ruang not found")
        
        db_ruang.nama_ruang = ruang.nama_ruang
        db.commit()
        db.refresh(db_ruang)
        return db_ruang
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-schedule/")
async def generate_schedule(request: ScheduleRequest, db: Session = Depends(get_db)):
    try:
        def log_callback(message: str):
            asyncio.create_task(broadcast_log(message))
        best_schedule, best_fitness = await run_gwo_optimization(
            create_random_schedule,
            lambda sol: calculate_fitness(sol, db),
            lambda sol: collect_conflicts(sol, db),
            request.population_size,
            request.max_iterations,
            log_callback=log_callback
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

@app.get("/preferensi_dosen")
def get_preferensi_dosen(db: Session = Depends(get_db)):
    return db.query(PreferensiDosen).all()

@app.post("/preferensi_dosen", response_model=PreferensiSchema)
def create_or_update_preferensi(preferensi: PreferensiSchema, db: Session = Depends(get_db)):
    db_pref = db.query(PreferensiDosen).filter(PreferensiDosen.dosen_id == preferensi.dosen_id).first()
    if db_pref:
        db_pref.hari = preferensi.hari
        db_pref.jam_mulai_id = preferensi.jam_mulai_id
        db_pref.jam_selesai_id = preferensi.jam_selesai_id
        db.commit()
        db.refresh(db_pref)
        return db_pref
    else:
        new_pref = PreferensiDosen(
            dosen_id=preferensi.dosen_id,
            hari=preferensi.hari,
            jam_mulai_id=preferensi.jam_mulai_id,
            jam_selesai_id=preferensi.jam_selesai_id
        )
        db.add(new_pref)
        db.commit()
        db.refresh(new_pref)
        return new_pref

@app.put("/preferensi_dosen/{id_preferensi}", response_model=PreferensiSchema)
def update_preferensi(id_preferensi: int, preferensi: PreferensiSchema, db: Session = Depends(get_db)):
    db_pref = db.query(PreferensiDosen).filter(PreferensiDosen.id_preferensi == id_preferensi).first()
    if not db_pref:
        raise HTTPException(status_code=404, detail="Preferensi tidak ditemukan")
    
    db_pref.hari = preferensi.hari
    db_pref.jam_mulai_id = preferensi.jam_mulai_id
    db_pref.jam_selesai_id = preferensi.jam_selesai_id
    db.commit()
    db.refresh(db_pref)
    return db_pref

@app.get("/prodi")
def get_prodi(db: Session = Depends(get_db)):
    try:
        return db.query(PreferensiProdi).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))