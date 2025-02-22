from pydantic import BaseModel
from typing import Optional

class DosenSchema(BaseModel):
    id_dosen: int
    nama_dosen: str

    class Config:
        orm_mode = True

class MkGenapSchema(BaseModel):
    id_mk_genap: int
    nama_mk_genap: str
    metode: str  # Pastikan field ini ada di model

    class Config:
        orm_mode = True

class DataDosenSchema(BaseModel):
    id_dosen: int
    id_mk_genap: int
    kelas: str
    dosen: Optional[DosenSchema] = None
    mk_genap: Optional[MkGenapSchema] = None

    class Config:
        orm_mode = True

class HariSchema(BaseModel):
    id_hari: int
    nama_hari: str

    class Config:
        from_attributes = True

class JamSchema(BaseModel):
    id_jam: int
    jam_awal: str
    jam_akhir: str

    class Config:
        from_attributes = True

class RuangSchema(BaseModel):
    id_ruang: int
    nama_ruang: str

    class Config:
        from_attributes = True

# Tambahkan di file schemas.py
from pydantic import BaseModel

class DataDosenCreate(BaseModel):
    id_dosen: int
    id_mk_genap: int
    kelas: str  # Tambahkan field kelas sesuai model

    class Config:
        orm_mode = True