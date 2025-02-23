from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict
from typing import List
import random

from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, Ruang
from schemas import DosenSchema, MkGenapSchema, DosenWithMkSchema, HariSchema, JamSchema, RuangSchema, DataDosenCreate, DataDosenSchema

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# Endpoint untuk mendapatkan semua dosen
@app.get("/dosen", response_model=list[DosenSchema])
def get_all_dosen(db: Session = Depends(get_db)):
    return db.query(Dosen).order_by(Dosen.id_dosen).all()

# Endpoint untuk mendapatkan semua dosen berdasarkan id
@app.get("/dosen/{id_dosen}", response_model=DosenSchema)
def get_dosen_by_id(id_dosen: int, db: Session = Depends(get_db)):
    dosen = db.query(Dosen).filter(Dosen.id_dosen == id_dosen).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")
    return dosen

# Endpoint untuk mendapatkan semua mata kuliah genap
@app.get("/mk_genap", response_model=list[MkGenapSchema])
def get_all_mk_genap(db: Session = Depends(get_db)):
    return db.query(MkGenap).order_by(MkGenap.smt).all()

# Endpoint untuk mendapatkan kelas, id dosen, id mk
@app.get("/tbl_data_dosen", response_model=List[DataDosenSchema])
def get_selected_fields(db: Session = Depends(get_db)):
    return db.query(DataDosen.id_dosen, DataDosen.id_mk_genap, DataDosen.kelas).all()

# Endpoint untuk mendapatkan semua data dosen
@app.get("/data_dosen", response_model=List[DosenWithMkSchema])
def get_all_data_dosen(db: Session = Depends(get_db)):
    try:
        # Ambil semua data dosen
        all_dosen = db.query(Dosen).all()
        
        # Ambil semua data dosen beserta relasinya
        data = db.query(DataDosen)\
            .options(
                joinedload(DataDosen.dosen),
                joinedload(DataDosen.mk_genap)
            )\
            .all()

        # Kelompokkan data berdasarkan dosen
        dosen_map = defaultdict(lambda: {"mata_kuliah": []})

        # Tambahkan semua dosen ke dalam map
        for dosen in all_dosen:
            dosen_map[dosen.id_dosen] = {
                "id_dosen": dosen.id_dosen,
                "nama_dosen": dosen.nama_dosen,
                "mata_kuliah": []
            }

        # Tambahkan mata kuliah untuk dosen yang memiliki
        for item in data:
            dosen_id = item.id_dosen
            if item.mk_genap:
                dosen_map[dosen_id]["mata_kuliah"].append({
                    "kelas": item.kelas,  # Ambil kelas dari tbl_data_dosen
                    "id_mk_genap": item.mk_genap.id_mk_genap,
                    "nama_mk_genap": item.mk_genap.nama_mk_genap,
                    "smt": item.mk_genap.smt,
                    "sks": item.mk_genap.sks,
                    "sifat": item.mk_genap.sifat,
                    "metode": item.mk_genap.metode
                })

        # Konversi ke list
        result = list(dosen_map.values())
        return result

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
@app.delete("/data_dosen/{id_dosen}/{id_mk_genap}")
def delete_data_dosen(id_dosen: int, id_mk_genap: int, db: Session = Depends(get_db)):
    try:
        # Cari data yang ingin dihapus
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

@app.get("/slot_waktu")
def get_slot_waktu(db: Session = Depends(get_db)):
    ruang_list = [ruang.nama_ruang for ruang in db.query(Ruang).all()]
    hari_list = [hari.nama_hari for hari in db.query(Hari).all()]
    jam_list = db.query(Jam.id_jam, Jam.jam_awal, Jam.jam_akhir).order_by(Jam.id_jam).all()
    
    # Gabungkan data_dosen dengan nama_dosen
    data_dosen_list = db.query(
        DataDosen.kelas, DataDosen.id_mk_genap, Dosen.nama_dosen
    ).join(Dosen, DataDosen.id_dosen == Dosen.id_dosen).all()

    # Buat dictionary untuk akses cepat ke data mata kuliah berdasarkan id_mk_genap
    mata_kuliah_list = {
        mk.id_mk_genap: mk for mk in db.query(MkGenap).all()
    }

    # Buat daftar semua kemungkinan slot waktu
    all_slots = []
    id_counter = 0
    used_slots = set()

    for hari in hari_list:
        for jam in jam_list:
            for ruang in ruang_list:
                id_counter += 1
                all_slots.append({
                    "id_slot": id_counter,
                    "mata_kuliah": None,
                    "dosen": None,
                    "ruang": ruang,
                    "hari": hari,
                    "jam_mulai": jam.jam_awal,
                    "jam_selesai": jam.jam_akhir,
                    "kelas": None,
                    "sks": None,
                    "metode": None
                })

    # Jadwal yang terisi
    id_counter = 0
    for data_dosen in data_dosen_list:
        mk = mata_kuliah_list.get(data_dosen.id_mk_genap)
        if not mk:
            continue

        sks = mk.sks
        metode = mk.metode
        nama_mata_kuliah = mk.nama_mk_genap
        nama_dosen = data_dosen.nama_dosen
        
        # Tentukan hari dan ruangan
        hari_terpilih = random.choice(hari_list)
        ruangan = None if metode == "online" else random.choice(ruang_list)

        # Pilih slot waktu yang cukup untuk SKS
        available_slots = [i for i in range(len(jam_list) - sks + 1)]
        random.shuffle(available_slots)

        for start_slot in available_slots:
            selected_jam = jam_list[start_slot:start_slot + sks]
            jam_awal = selected_jam[0].jam_awal
            jam_akhir = selected_jam[-1].jam_akhir

            slot_key = (hari_terpilih, jam_awal, jam_akhir) if metode == "online" else (ruangan, hari_terpilih, jam_awal, jam_akhir)
            if slot_key in used_slots:
                continue

            used_slots.add(slot_key)
            id_counter += 1

            # Perbarui slot yang sesuai
            for slot in all_slots:
                if (
                    slot["hari"] == hari_terpilih and
                    slot["jam_mulai"] == jam_awal and
                    slot["jam_selesai"] == jam_akhir and
                    (slot["ruang"] == ruangan or metode == "online")
                ):
                    slot.update({
                        "mata_kuliah": nama_mata_kuliah,
                        "dosen": nama_dosen,
                        "kelas": data_dosen.kelas,
                        "sks": sks,
                        "metode": metode
                    })
                    break

    return all_slots