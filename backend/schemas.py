from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Union

class DosenSchema(BaseModel):
    id_dosen: int
    nama_dosen: str

    model_config = ConfigDict(from_attributes=True)

class MkGenapSchema(BaseModel):
    id_mk_genap: int
    nama_mk_genap: str
    smt: int
    sks: int
    sifat: str
    kategori: str
    metode: str

    model_config = ConfigDict(from_attributes=True)
    
class MataKuliahSchema(BaseModel):
    
    id_mk_genap: int
    nama_mk_genap: str
    smt: int
    sks: int
    sifat: str
    metode: str
    kategori: str
    kelas: str
    
    model_config = ConfigDict(from_attributes=True)

class DataDosenSchema(BaseModel):
    id_dosen: int
    id_mk_genap: int
    kelas: str
    dosen: Optional[DosenSchema] = None
    mk_genap: Optional[MkGenapSchema] = None

    model_config = ConfigDict(from_attributes=True)

class DosenWithMkSchema(BaseModel):
    id_dosen: int
    nama_dosen: str
    mata_kuliah: List[MataKuliahSchema] = []  # List mata kuliah untuk dosen

    model_config = ConfigDict(from_attributes=True)

class HariSchema(BaseModel):
    id_hari: int
    nama_hari: str

    model_config = ConfigDict(from_attributes=True)

class JamSchema(BaseModel):
    id_jam: int
    jam_awal: str
    jam_akhir: str

    model_config = ConfigDict(from_attributes=True)

class RuangSchema(BaseModel):
    id_ruang: int
    nama_ruang: str

    model_config = ConfigDict(from_attributes=True)

class DataDosenCreate(BaseModel):
    id_dosen: int
    id_mk_genap: int
    kelas: str

    model_config = ConfigDict(from_attributes=True)

class PreferensiSchema(BaseModel):
    id_preferensi: Optional[int] = None
    dosen_id: int
    hari: Optional[Union[int, List[int]]] = None
    jam_selesai_id: int
    jam_mulai_id: int

    model_config = ConfigDict(from_attributes=True)

class ScheduleRequest(BaseModel):
    population_size: int = Field(..., gt=3, lt=101, description="Population size harus antara 4-100")
    max_iterations: int = Field(..., gt=3, lt=101, description="Max iterations harus antara 4-100")

class ProdiScemas(BaseModel):
    id: int
    hari: Optional[Union[int, List[int]]] = None
    jam_mulai_id: int
    jam_selesai_id: int

    model_config = ConfigDict(from_attributes=True)