Berikut adalah versi **perbaikan README**-mu yang telah disesuaikan **dengan diagram arsitektur** yang kamu lampirkan (`diagram.png`) dan juga penyempurnaan struktur, penulisan, dan tata bahasa agar lebih profesional, jelas, dan konsisten:

---

# 🐺 UAD Course Scheduler - GWO Enhanced

**Web-Based Academic Scheduling System with Dynamic Constraints**
*(Nuxt.js Frontend + FastAPI Backend + Supabase)*

![Nuxt.js](https://img.shields.io/badge/Nuxt.js-3.8.0-green?logo=nuxt.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-blue?logo=fastapi)
![Supabase](https://img.shields.io/badge/Supabase-3.0.0-orange?logo=supabase)

[![Open in GitHub](https://img.shields.io/badge/Repo-Skripsiku-24292e?style=for-the-badge\&logo=github)](https://github.com/indogegewepe/Skripsiku)

---

## 🌐 Live Demo

🚀 Akses langsung sistem: [penjadwalan-uad.vercel.app](https://penjadwalan-uad.vercel.app/)

---

## 🧠 Diagram Arsitektur Sistem

![Architecture Diagram](https://raw.githubusercontent.com/indogegewepe/Skripsiku/refs/heads/master/diagram.png)

---

## 🔧 Stack Teknologi

| Komponen     | Teknologi                                |
| ------------ | ---------------------------------------- |
| **Frontend** | Nuxt.js 3, Tailwind CSS, Pinia           |
| **Backend**  | FastAPI, Python 3.11, Uvicorn            |
| **Database** | Supabase (PostgreSQL) + RLS              |
| **Optimasi** | Grey Wolf Optimizer (GWO), NumPy, Pandas |
| **Deploy**   | Vercel (Frontend), Railway (Backend)     |

---

## 🚀 Fitur Utama

### 1. 🧩 Dynamic Constraints UI

* Tambah/ubah constraints secara real-time via dashboard admin
* Validasi dinamis menggunakan Supabase RPC
* Sistem prioritas multi-level

### 2. 🐺 Hybrid GWO Engine

```python
# Contoh pemanggilan GWO dari endpoint FastAPI
@router.post("/optimize")
async def run_optimization():
    optimizer = GWOScheduler(
        constraints=await fetch_dynamic_constraints(),
        max_iter=100
    )
    return await optimizer.run_async()
```

* Optimasi jadwal dengan paralelisasi menggunakan `asyncio`
* Hasil cache tersimpan otomatis di Supabase

### 3. 📊 Academic Analytics

* Visualisasi heatmap beban dosen
* Pelacakan historis perubahan jadwal
* Auto-generate KRS berdasarkan hasil optimasi

---

## 📂 Struktur Repositori

```bash
Skripsiku/
├── frontend/            # Nuxt.js 3
│   ├── composables/     # Visualisasi GWO
│   └── pages/admin/     # Manajemen constraints
│
├── backend/             # FastAPI
│   ├── routers/         # API endpoints
│   └── gwo/             # Algoritma GWO
│
├── supabase/            # SQL dan trigger RLS
│   ├── triggers/        
│   └── functions/       
│
└── docker/              # Setup container
```

---

## ⚙️ Instalasi Lokal

1. **Clone Repositori**

   ```bash
   git clone https://github.com/indogegewepe/Skripsiku
   ```

2. **Instalasi Frontend**

   ```bash
   cd frontend
   npm install
   cp .env.example .env
   ```

3. **Instalasi Backend**

   ```bash
   cd ../backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

4. **Konfigurasi Supabase**

   * Buat project baru di [Supabase](https://supabase.io)
   * Import file `/supabase/schema.sql`
   * Sesuaikan `.env` frontend & backend dengan kredensial Supabase

5. **Jalankan Sistem**

   ```bash
   # Frontend (port 3000)
   npm run dev

   # Backend (port 8000)
   uvicorn main:app --reload
   ```

---

## 📈 Perbandingan Kinerja

| Metode             | Manual (Excel) | Sistem GWO    | Peningkatan         |
| ------------------ | -------------- | ------------- | ------------------- |
| Kompleksitas Waktu | O(n³)          | O(n log n)    | 68% lebih cepat     |
| Deteksi Konflik    | 72% manual     | 100% otomatis | +28% akurasi        |
| Waktu Re-Schedule  | 2-3 hari       | <5 menit      | 99% efisiensi waktu |

---

## 🤝 Cara Berkontribusi

1. Fork repositori
2. Buat branch fitur:

   ```bash
   git checkout -b feat/namafitur
   ```
3. Commit perubahan:

   ```bash
   git commit -m "feat: tambah fitur X"
   ```
4. Push & buat Pull Request

➡️ Lihat panduan lengkap di [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah [Academic Free License 3.0](LICENSE) — hanya untuk penggunaan edukasi.

---

**Dibuat dengan ❤️ oleh Bagas Uwaidha**
🔗 [Portfolio](#) | 📧 [bagasuwaidha007@gmail.com](mailto:bagasuwaidha007@gmail.com)
