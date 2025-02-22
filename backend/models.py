from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class Dosen(Base):
    __tablename__ = "tbl_dosen"
    
    id_dosen = Column(Integer, primary_key=True, index=True)
    nama_dosen = Column(String, nullable=False)

class DataDosen(Base):
    __tablename__ = "tbl_data_dosen"
    
    id_dosen = Column(Integer, ForeignKey("tbl_dosen.id_dosen"), primary_key=True)
    id_mk_genap = Column(Integer, ForeignKey("tbl_mk_genap.id_mk_genap"), primary_key=True)
    kelas = Column(String, nullable=False)

class MkGenap(Base):
    __tablename__ = "tbl_mk_genap"
    
    id_mk_genap = Column(Integer, primary_key=True, index=True)
    nama_mk_genap = Column(String, nullable=False)
    smt = Column(Integer, nullable=False)
    sks = Column(Integer, nullable=False)
    sifat = Column(String, nullable=False)
    kategori = Column(String, nullable=False)
    metode = Column(String, nullable=False)

class Hari(Base):
    __tablename__ = "tbl_hari"
    
    id_hari = Column(Integer, primary_key=True, index=True)
    nama_hari = Column(String, nullable=False)

class Jam(Base):
    __tablename__ = "tbl_jam"
    
    id_jam = Column(Integer, primary_key=True, index=True)
    jam_awal = Column(String, nullable=False)
    jam_akhir = Column(String, nullable=False)

class Ruang(Base):
    __tablename__ = "tbl_ruang"
    
    id_ruang = Column(Integer, primary_key=True, index=True)
    nama_ruang = Column(String, nullable=False)

