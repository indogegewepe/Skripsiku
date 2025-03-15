from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Dosen(Base):
    __tablename__ = "tbl_dosen"
    
    id_dosen = Column(Integer, primary_key=True)
    nama_dosen = Column(String, nullable=False)
    
    # Relasi
    data_dosen = relationship("DataDosen", back_populates="dosen")
    preferensi = relationship("Preferensi", back_populates="dosen")
    
class MkGenap(Base):
    __tablename__ = "tbl_mk_genap"
    
    id_mk_genap = Column(Integer, primary_key=True)
    nama_mk_genap = Column(String, nullable=False)
    smt = Column(Integer, nullable=False)
    sks = Column(Integer, nullable=False)
    sifat = Column(String, nullable=False)
    metode = Column(String, nullable=False)
    
    # Relasi
    data_dosen = relationship("DataDosen", back_populates="mk_genap")

class DataDosen(Base):
    __tablename__ = "tbl_data_dosen"
    
    id_dosen = Column(Integer, ForeignKey("tbl_dosen.id_dosen"), primary_key=True)
    id_mk_genap = Column(Integer, ForeignKey("tbl_mk_genap.id_mk_genap"), primary_key=True)
    kelas = Column(String, nullable=False)
    
    # Relasi
    dosen = relationship("Dosen", back_populates="data_dosen")
    mk_genap = relationship("MkGenap", back_populates="data_dosen")
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

class Preferensi(Base):
    __tablename__ = "tbl_preferensi_dosen"
    
    id_dosen = Column(Integer, ForeignKey("tbl_dosen.id_dosen"), primary_key=True)
    type = Column(String, nullable=False, primary_key=True)  # Tambahkan primary_key di sini
    value = Column(String, nullable=False)

    dosen = relationship("Dosen", back_populates="preferensi")
