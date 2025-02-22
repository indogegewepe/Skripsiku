from pydantic import BaseModel

class DosenSchema(BaseModel):
    id_dosen: int
    nama_dosen: str

    class Config:
        from_attributes = True

class MkGenapSchema(BaseModel):
    id_mk_genap: int
    nama_mk_genap: str
    smt: int
    sks: int
    sifat: str
    kategori: str
    metode: str

    class Config:
        from_attributes = True

class DataDosenSchema(BaseModel):
    id_dosen: int
    id_mk_genap: int
    kelas: str

    class Config:
        from_attributes = True

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
