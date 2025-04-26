import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, PreferensiProdi, Ruang, PreferensiDosen

import copy
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict
import json
import random

def query_to_dataframe(query_result):
    dict_list = [item.__dict__ for item in query_result]
    for d in dict_list:
        d.pop("_sa_instance_state", None)
    return pd.DataFrame(dict_list)

def time_to_minutes(t):
    try:
        dt = datetime.strptime(t, "%H:%M:%S")
    except ValueError:
        dt = datetime.strptime(t, "%H:%M")
    return dt.hour * 60 + dt.minute

db: Session = next(get_db())

dosen_df = query_to_dataframe(db.query(Dosen).all())
mk_genap_df = query_to_dataframe(db.query(MkGenap).all())
data_dosen_df = query_to_dataframe(db.query(DataDosen).all())
hari_df = query_to_dataframe(db.query(Hari).all())
ruang_df = query_to_dataframe(db.query(Ruang).all())
jam_df = query_to_dataframe(db.query(Jam).all())

jam_df = jam_df.sort_values('id_jam')
day_map = dict(zip(hari_df['id_hari'], hari_df['nama_hari']))
jam_mulai_map = dict(zip(jam_df['id_jam'], jam_df['jam_awal']))
jam_selesai_map = dict(zip(jam_df['id_jam'], jam_df['jam_akhir']))

merged_df = pd.merge(
    pd.merge(data_dosen_df, dosen_df, on='id_dosen'),
    mk_genap_df, on='id_mk_genap'
)
merged_df['temp_id'] = range(1, len(merged_df) + 1)

# ------------------------
# GENERATOR SLOT & JADWAL
# ------------------------

def slot_generator():
    slots = []
    id_counter = 1
    for hari in hari_df['nama_hari']:
        for ruang in ruang_df['nama_ruang']:
            for jam in jam_df.itertuples():
                slots.append({
                    "id_slot": id_counter,
                    "id_mk": None,
                    "mata_kuliah": None,
                    "id_dosen": None,
                    "dosen": None,
                    "ruang": ruang,
                    "hari": hari,
                    "jam_mulai": jam.jam_awal,
                    "jam_selesai": jam.jam_akhir,
                    "semester": None,
                    "kelas": None,
                    "sks": None,
                    "metode": None,
                    "status": None,
                    "temp_id": None
                })
                id_counter += 1
    return slots

def create_random_schedule():
    schedule = slot_generator()
    merged_shuffled = merged_df.sample(frac=1).iterrows()

    room_allocations = defaultdict(list)
    teacher_allocations = defaultdict(list)
    class_allocations = defaultdict(list)

    for _, row in merged_shuffled:
        id_mk = row['id_mk_genap']
        mata_kuliah = row['nama_mk_genap']
        id_dosen = row['id_dosen']
        dosen = row['nama_dosen']
        kelas = row['kelas']
        sks = int(row['sks'])
        semester = row['smt']
        metode = row['metode']
        temp_id = row['temp_id']

        possible_positions = list(range(len(schedule) - sks + 1))
        random.shuffle(possible_positions)

        candidate_blocks = []
        for i in possible_positions:
            block = schedule[i:i+sks]
            if not all(slot['mata_kuliah'] is None for slot in block):
                continue
            if not all(slot['hari'] == block[0]['hari'] for slot in block):
                continue
            if not all(slot['ruang'] == block[0]['ruang'] for slot in block):
                continue
            hari_block = block[0]['hari']
            time_block = (time_to_minutes(block[0]['jam_mulai']), time_to_minutes(block[-1]['jam_selesai']))
            kelas_already = len(class_allocations[(kelas, hari_block)]) > 0
            candidate_blocks.append((block, time_block, kelas_already))
        
        if candidate_blocks:
            selected_block = candidate_blocks[0][0]
            for slot in selected_block:
                slot.update({
                    "id_mk": id_mk,
                    "mata_kuliah": mata_kuliah,
                    "id_dosen": id_dosen,
                    "dosen": dosen,
                    "kelas": kelas,
                    "sks": sks,
                    "semester": semester,
                    "metode": metode,
                    "temp_id": temp_id
                })
            hari_block = selected_block[0]['hari']
            time_block = (time_to_minutes(selected_block[0]['jam_mulai']),
                          time_to_minutes(selected_block[-1]['jam_selesai']))
            room_allocations[(selected_block[0]['ruang'], hari_block)].append(time_block)
            teacher_allocations[(dosen, hari_block)].append(time_block)
            class_allocations[(kelas, hari_block)].append(time_block)
        else:
            print(f"Gagal menempatkan: {kelas} - {mata_kuliah} - {dosen}")
    
    return schedule

def get_lecturer_preferences(db: Session):
    query = (
        select(
            Dosen.nama_dosen,
            PreferensiDosen.hari,              
            PreferensiDosen.jam_mulai_id,        
            PreferensiDosen.jam_selesai_id       
        )
        .join(PreferensiDosen, Dosen.id_dosen == PreferensiDosen.dosen_id)
    )
    results = db.execute(query).fetchall()
    lecturer_preferences = {}
    for nama_dosen, hari, jam_mulai_id, jam_selesai_id in results:
        if hari:
            if isinstance(hari, list):
                restricted_days = [day_map.get(day_id, day_id) for day_id in hari]
            else:
                restricted_days = [day_map.get(hari, hari)]
        else:
            restricted_days = []
        if jam_mulai_id is not None and jam_selesai_id is not None:
            time_range = [jam_mulai_map.get(jam_mulai_id), jam_selesai_map.get(jam_selesai_id)]
        else:
            time_range = []
        lecturer_preferences[nama_dosen] = {
            "restricted_days": restricted_days,
            "time_range": time_range
        }
    return lecturer_preferences

def get_prodi_preferences(db: Session):
    query = (
        select(
            PreferensiProdi.hari,
            PreferensiProdi.jam_mulai_id,
            PreferensiProdi.jam_selesai_id
        )
    )
    results = db.execute(query).fetchall()
    prodi_preferences = {
        "restricted_days": [],
        "restricted_time_ranges": []
    }
    for hari, jam_mulai_id, jam_selesai_id in results:
        # Proses hari terlarang
        if hari:
            if isinstance(hari, list):
                restricted_days = [day_map.get(day, day) for day in hari]
            else:
                restricted_days = [day_map.get(hari, hari)]
            prodi_preferences["restricted_days"].extend(restricted_days)
        
        # Proses rentang waktu terlarang
        if jam_mulai_id is not None and jam_selesai_id is not None:
            start = jam_mulai_map.get(jam_mulai_id)
            end = jam_selesai_map.get(jam_selesai_id)
            if start and end:
                prodi_preferences["restricted_time_ranges"].append((start, end))
                
    return prodi_preferences

def collect_conflicts(schedule, db: Session):
    conflict_temp_ids = set()
    lecturer_preferences = get_lecturer_preferences(db)
    prodi_prefs = get_prodi_preferences(db)
    preference_conflict_temp_ids = set()

    # (A) Konsistensi Ruangan
    temp_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is not None and slot.get('temp_id') is not None:
            temp_groups[slot['temp_id']].append(slot)
    room_consistency_conflicts = []
    for tid, slots in temp_groups.items():
        if len({slot['ruang'] for slot in slots}) > 1:
            conflict_temp_ids.add(tid)
            room_consistency_conflicts.append({
                'temp_id': tid,
                'ruangan': list({slot['ruang'] for slot in slots}),
                'slot_ids': [slot['id_slot'] for slot in slots]
            })
    
    # (B) Konflik Dosen
    teacher_conflicts = []
    teacher_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        teacher_groups[(slot['dosen'], slot['hari'].lower())].append(slot)
    for slots in teacher_groups.values():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                if time_to_minutes(slots[j]['jam_mulai']) < time_to_minutes(slots[i]['jam_selesai']) \
                   and slots[i]['mata_kuliah'] != slots[j]['mata_kuliah']:
                    for tid in (slots[i].get('temp_id'), slots[j].get('temp_id')):
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    teacher_conflicts.append((slots[i]['id_slot'], slots[j]['id_slot']))

    # (C) Konflik Ruangan
    room_conflicts = []
    room_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        room_groups[(slot['ruang'], slot['hari'].lower())].append(slot)
    for slots in room_groups.values():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                if time_to_minutes(slots[j]['jam_mulai']) < time_to_minutes(slots[i]['jam_selesai']) \
                   and slots[i]['kelas'] != slots[j]['kelas']:
                    for tid in (slots[i].get('temp_id'), slots[j].get('temp_id')):
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    room_conflicts.append((slots[i]['id_slot'], slots[j]['id_slot']))

    # (D) Konflik Preferensi Dosen
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        tid = slot.get('temp_id')
        dosen = str(slot['dosen'])
        slot_day = slot['hari'].lower()
        slot_start = time_to_minutes(slot['jam_mulai'])
        if dosen in lecturer_preferences:
            prefs = lecturer_preferences[dosen]
            restricted_days = [day.lower() for day in prefs['restricted_days']] if prefs['restricted_days'] else []
            if restricted_days and slot_day in restricted_days:
                if tid is not None:
                    preference_conflict_temp_ids.add(tid)
                continue
            if prefs['time_range']:
                allowed_start = time_to_minutes(prefs['time_range'][0])
                allowed_end = time_to_minutes(prefs['time_range'][1])
                if slot_start < allowed_start or slot_start >= allowed_end:
                    if tid is not None:
                        preference_conflict_temp_ids.add(tid)

    # (E) Konflik Kelas
    class_conflicts = []
    class_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        class_groups[(slot['kelas'], slot['hari'].lower(), slot['semester'])].append(slot)
    for slots in class_groups.values():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                if time_to_minutes(slots[j]['jam_mulai']) < time_to_minutes(slots[i]['jam_selesai']):
                    for tid in (slots[i].get('temp_id'), slots[j].get('temp_id')):
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    class_conflicts.append((slots[i]['id_slot'], slots[j]['id_slot']))
    
    # (F) Konflik Preferensi Prodi
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue

        tid = slot.get('temp_id')
        slot_day = slot['hari'].lower()
        slot_start = time_to_minutes(slot['jam_mulai'])
        
        # Cek hari terlarang prodi
        restricted_days = [day.lower() for day in prodi_prefs.get('restricted_days', [])]
        restricted_time_ranges = prodi_prefs.get('restricted_time_ranges', [])
        
        # Iterasi semua rentang waktu terlarang prodi
        for time_range in restricted_time_ranges:
            restricted_start = time_to_minutes(time_range[0])
            restricted_end = time_to_minutes(time_range[1])
            
            if (
                slot_day in restricted_days and
                restricted_start <= slot_start < restricted_end
            ):
                if tid is not None:
                    preference_conflict_temp_ids.add(tid)

    return {
        'class_conflicts': class_conflicts,
        'conflict_temp_ids': conflict_temp_ids,
        'preference_conflict_temp_ids': preference_conflict_temp_ids,
        'teacher_conflicts': teacher_conflicts,
        'room_conflicts': room_conflicts,
        'room_consistency_conflicts': room_consistency_conflicts
    }

def calculate_fitness(schedule, db: Session):
    conflicts = collect_conflicts(schedule, db)
    penalty = (len(conflicts['teacher_conflicts']) +
               len(conflicts['room_conflicts']) +
               len(conflicts['room_consistency_conflicts']) +
               len(conflicts['class_conflicts']) +
               0.5 * len(conflicts['preference_conflict_temp_ids']))
    return penalty

class GreyWolfOptimizer:
    def __init__(self, population_size=10, max_iterations=50):
        self.population_size = population_size
        self.max_iterations = max_iterations
        
    async def optimize(self, fitness_function, create_solution_function, collect_conflicts_func, log_callback=None):
        population = [create_solution_function() for _ in range(self.population_size)]
        fitness_values = [fitness_function(solution) for solution in population]
        
        best_solution = None
        best_fitness = float('inf')
        a_start = 2.0
        
        for iteration in range(self.max_iterations):
            a = a_start - iteration * (a_start / self.max_iterations)
            if best_fitness <= 0:
                break
            
            sorted_indices = np.argsort(fitness_values)
            alpha = population[sorted_indices[0]]
            beta = population[sorted_indices[1]]
            delta = population[sorted_indices[2]]
            if fitness_values[sorted_indices[0]] < best_fitness:
                best_fitness = fitness_values[sorted_indices[0]]
                best_solution = copy.deepcopy(alpha)
            
            log_message = f"Iterasi {iteration+1}/{self.max_iterations} - Best Fitness: {best_fitness}"
            
            if log_callback:
                log_callback(log_message)
            
            new_population = []
            for i in range(self.population_size):
                if random.random() < 0.05:
                    new_solution = create_solution_function()
                else:
                    new_solution = self.update_position(
                        population[i], alpha, beta, delta, a, create_solution_function, fitness_function, collect_conflicts_func
                    )
                new_population.append(new_solution)
                fitness_values[i] = fitness_function(new_solution)
            population = new_population
            
            await asyncio.sleep(1)
        
        print("Optimasi Selesai!")
        print(f"Best Fitness: {best_fitness}")
        
        conflicts_detail = collect_conflicts_func(best_solution)
        print(f"Detail Konflik: {conflicts_detail}")
        conflict_numbers = set()
        for value in conflicts_detail.values():
            if isinstance(value, (set, list)):
                conflict_numbers.update(map(str, value))
        for slot in best_solution:
            tid = str(slot.get("temp_id", ""))
            if tid in conflict_numbers:
                if tid in map(str, conflicts_detail.get('preference_conflict_temp_ids', [])):
                    slot["status"] = "yellow"
                elif tid in map(str, conflicts_detail.get('conflict_temp_ids', [])):
                    slot["status"] = "red"
                
        return best_solution, best_fitness
    
    def update_position(self, current_solution, alpha, beta, delta, a, create_solution_function, fitness_function, collect_conflicts_func):
        """
        Update posisi wolf berdasarkan formula GWO standar yang diadaptasi ke domain penjadwalan
        """
        # Buat salinan solusi saat ini untuk dimodifikasi
        new_solution = copy.deepcopy(current_solution)
        
        # Untuk setiap slot dalam jadwal, kita akan menerapkan formula GWO
        for i, slot in enumerate(new_solution):
            # Jika slot sudah terisi, kita perlu memutuskan apakah akan mengubahnya
            if slot.get('mata_kuliah') is not None:
                # Koefisien untuk Alpha
                A1 = 2 * a * random.random() - a
                C1 = 2 * random.random()
                
                # Koefisien untuk Beta
                A2 = 2 * a * random.random() - a
                C2 = 2 * random.random()
                
                # Koefisien untuk Delta
                A3 = 2 * a * random.random() - a
                C3 = 2 * random.random()
                
                # Probabilitas untuk mengikuti Alpha, Beta, atau Delta
                if random.random() < 0.6:  # Alpha memiliki pengaruh terbesar
                    # Cari slot yang sesuai di Alpha
                    alpha_match = next((s for s in alpha if s.get('hari') == slot['hari'] and 
                                    abs(time_to_minutes(s.get('jam_mulai', '00:00')) - 
                                        time_to_minutes(slot.get('jam_mulai', '00:00'))) < 30), None)
                    
                    if alpha_match and random.random() < abs(C1 - A1):
                        # Terapkan properti dari alpha ke slot ini
                        for key in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']:
                            if key in alpha_match:
                                slot[key] = alpha_match[key]
                
                elif random.random() < 0.3:  # Beta memiliki pengaruh menengah
                    # Cari slot yang sesuai di Beta
                    beta_match = next((s for s in beta if s.get('hari') == slot['hari'] and 
                                    abs(time_to_minutes(s.get('jam_mulai', '00:00')) - 
                                        time_to_minutes(slot.get('jam_mulai', '00:00'))) < 30), None)
                    
                    if beta_match and random.random() < abs(C2 - A2):
                        # Terapkan properti dari beta ke slot ini
                        for key in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']:
                            if key in beta_match:
                                slot[key] = beta_match[key]
                
                elif random.random() < 0.1:  # Delta memiliki pengaruh terkecil
                    # Cari slot yang sesuai di Delta
                    delta_match = next((s for s in delta if s.get('hari') == slot['hari'] and 
                                    abs(time_to_minutes(s.get('jam_mulai', '00:00')) - 
                                        time_to_minutes(slot.get('jam_mulai', '00:00'))) < 30), None)
                    
                    if delta_match and random.random() < abs(C3 - A3):
                        # Terapkan properti dari delta ke slot ini
                        for key in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']:
                            if key in delta_match:
                                slot[key] = delta_match[key]
        
        # Tangani konflik yang mungkin terjadi setelah pembaruan
        # Tentukan mana mata kuliah yang berkonflik
        conflicts = collect_conflicts_func(new_solution)
        conflict_temp_ids = conflicts.get('conflict_temp_ids', set())
        
        # Coba resolusi konflik dengan mata kuliah yang berkonflik
        for tid in conflict_temp_ids:
            # Cari mata kuliah yang berkonflik
            conflict_slots = [i for i, slot in enumerate(new_solution) if str(slot.get('temp_id')) == str(tid)]
            
            if not conflict_slots:
                continue
                
            # Coba jadwal ulang mata kuliah yang berkonflik
            course_info = self.extract_course_info(new_solution[conflict_slots[0]])
            
            # Hapus mata kuliah yang berkonflik dari jadwal
            temp_solution = copy.deepcopy(new_solution)
            for idx in conflict_slots:
                for key in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']:
                    temp_solution[idx][key] = None
            
            # Pilih salah satu solusi terbaik (Alpha, Beta, Delta) sebagai panduan
            reference_solutions = [alpha, beta, delta]
            random.shuffle(reference_solutions)  # Tambah randomisasi
            
            for ref_solution in reference_solutions:
                # Coba temukan slot yang sama di solusi referensi
                ref_slots = [(i, slot) for i, slot in enumerate(ref_solution) 
                            if str(slot.get('temp_id')) == str(tid)]
                
                if ref_slots:
                    start_idx = ref_slots[0][0]
                    
                    # Pastikan course_sks adalah integer valid
                    try:
                        course_sks = int(course_info.get('sks', 1))
                        if course_sks <= 0:  # Validasi nilai logis
                            course_sks = 1
                    except (TypeError, ValueError):
                        # Jika konversi gagal, gunakan nilai default
                        course_sks = 1
                    
                    # Periksa apakah kita dapat menggunakan slot yang sama dengan referensi
                    can_use_same_slots = True
                    for j in range(course_sks):
                        if start_idx + j >= len(temp_solution) or temp_solution[start_idx + j]['mata_kuliah'] is not None:
                            can_use_same_slots = False
                            break
                    
                    if can_use_same_slots:
                        # Gunakan slot yang sama dengan solusi referensi
                        for j in range(course_sks):
                            for key in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'semester', 'metode', 'temp_id']:
                                temp_solution[start_idx + j][key] = course_info[key]
                        new_solution = temp_solution
                        break
            
            # Jika tidak berhasil dengan solusi referensi, coba jadwal ulang dengan random
            if any(str(slot.get('temp_id')) == str(tid) for slot in new_solution):
                # Coba jadwal ulang dengan sedikit relaksasi
                success = self.schedule_course(temp_solution, course_info, relax=True)
                if success:
                    new_solution = temp_solution
                else:
                    # Jika tidak berhasil, coba dengan pemaksaan
                    success = self.schedule_course(temp_solution, course_info, force=True)
                    if success:
                        new_solution = temp_solution
        
        # Tambahkan komponen eksplorasi dengan memodifikasi beberapa slot secara acak
        if random.random() < 0.3:  # 30% kemungkinan untuk eksplorasi
            random_slots = random.sample(range(len(new_solution)), k=min(3, len(new_solution)))
            for idx in random_slots:
                if new_solution[idx]['mata_kuliah'] is not None:
                    # Simpan informasi mata kuliah saat ini
                    course_info = self.extract_course_info(new_solution[idx])
                    
                    # Setelah menghapus mata kuliah yang berkonflik dari jadwal
                    temp_solution = copy.deepcopy(new_solution)
                    for idx in conflict_slots:
                        for key in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']:
                            temp_solution[idx][key] = None

                    # Tambahkan logging untuk debugging
                    print(f"Mencoba menjadwalkan ulang mata kuliah {course_info.get('mata_kuliah')} dengan ID {course_info.get('temp_id')}")

                    # Pastikan course_info adalah valid dan lengkap
                    if not course_info.get('mata_kuliah') or not course_info.get('temp_id'):
                        print("Data mata kuliah tidak valid untuk dijadwalkan ulang")
                        continue

                    success = False

                    # Coba jadwalkan menggunakan solusi referensi sebagai panduan
                    reference_solutions = [alpha, beta, delta]
                    random.shuffle(reference_solutions)

                    for ref_solution in reference_solutions:
                        # Coba temukan slot yang sama di solusi referensi
                        ref_slots = [(i, slot) for i, slot in enumerate(ref_solution) 
                                    if str(slot.get('temp_id')) == str(course_info.get('temp_id'))]
                        
                        if ref_slots:
                            start_idx = ref_slots[0][0]
                            
                            # Pastikan course_sks adalah integer valid
                            try:
                                course_sks = int(course_info.get('sks', 1))
                                if course_sks <= 0:  # Validasi nilai logis
                                    course_sks = 1
                            except (TypeError, ValueError):
                                course_sks = 1
                            
                            print(f"Referensi ditemukan di indeks {start_idx}, SKS: {course_sks}")
                            
                            # Periksa apakah kita dapat menggunakan slot yang sama dengan referensi
                            can_use_same_slots = True
                            for j in range(course_sks):
                                if start_idx + j >= len(temp_solution) or temp_solution[start_idx + j].get('mata_kuliah') is not None:
                                    can_use_same_slots = False
                                    break
                            
                            if can_use_same_slots:
                                print("Menggunakan slot yang sama dengan referensi")
                                # Gunakan slot yang sama dengan solusi referensi
                                for j in range(course_sks):
                                    for key in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'semester', 'metode', 'temp_id']:
                                        if course_info.get(key) is not None:
                                            temp_solution[start_idx + j][key] = course_info[key]
                                    # Jangan lupa tetapkan nilai sks yang sama
                                    temp_solution[start_idx + j]['sks'] = course_info.get('sks')
                                
                                success = True
                                new_solution = temp_solution
                                break

                    # Jika tidak berhasil dengan solusi referensi, coba jadwal ulang dengan algoritma reguler
                    if not success:
                        print("Mencoba menjadwalkan dengan algoritma reguler")
                        # Coba jadwal ulang dengan sedikit relaksasi
                        success = self.schedule_course(temp_solution, course_info, relax=True)
                        if success:
                            print("Berhasil menjadwalkan dengan relaksasi")
                            new_solution = temp_solution
                        else:
                            # Jika tidak berhasil, coba dengan pemaksaan
                            print("Mencoba menjadwalkan dengan pemaksaan")
                            success = self.schedule_course(temp_solution, course_info, force=True)
                            if success:
                                print("Berhasil menjadwalkan dengan pemaksaan")
                                new_solution = temp_solution
                            else:
                                print("Gagal menjadwalkan ulang")
        
        return new_solution

    def extract_course_info(self, slot):
        """Ekstrak informasi mata kuliah dari slot"""
        keys = ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']
        return {key: slot.get(key) for key in keys}

    def schedule_course(self, schedule, course, force=False, relax=False):
        keys = ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']
        
        course_values = {}
        for k in keys:
            course_values[k] = course.get(k)

        if course_values['sks'] is None:
            return False
        
        sks = course_values['sks']

        possible_positions = []
        for i in range(len(schedule) - sks + 1):
            block = schedule[i:i+sks]
            if not all(slot['mata_kuliah'] is None for slot in block):
                continue
            if not all(slot['hari'] == block[0]['hari'] for slot in block):
                continue
            if not all(slot['ruang'] == block[0]['ruang'] for slot in block):
                continue
            valid = True
            for j in range(1, len(block)):
                diff = abs(time_to_minutes(block[j]['jam_mulai']) - time_to_minutes(block[j-1]['jam_selesai']))
                if (not relax and diff != 0) or (relax and diff > 5):
                    valid = False
                    break
            if valid:
                possible_positions.append(i)
        if possible_positions:
            pos = random.choice(possible_positions)
            for slot in schedule[pos:pos+sks]:
                slot.update({k: course[k] for k in keys})
            return True
        if force and sks == 1:
            empty_slots = [i for i, slot in enumerate(schedule) if slot['mata_kuliah'] is None]
            if empty_slots:
                pos = random.choice(empty_slots)
                schedule[pos].update({k: course[k] for k in keys})
                return True
        return False

def run_gwo_optimization(create_random_schedule_func, fitness_func, conflicts_func, pop_size, max_iter, log_callback=None):
    gwo = GreyWolfOptimizer(population_size=pop_size, max_iterations=max_iter)
    return gwo.optimize(fitness_func, create_random_schedule_func, conflicts_func, log_callback)

if __name__ == "__main__":
    pop_size = 5  
    max_iter = 5

    best_schedule, best_fitness = asyncio.run(run_gwo_optimization(
            create_random_schedule,
            lambda sol: calculate_fitness(sol, db),
            lambda sol: collect_conflicts(sol, db),
            pop_size,
            max_iter,
            log_callback=lambda msg: print(msg))  # Optional logging
        )
    
    print(f"Optimasi selesai! Fitness terbaik: {best_fitness}")
    
    total_terisi = sum(1 for slot in best_schedule if slot['mata_kuliah'] is not None)
    print(f"Total slot terisi: {total_terisi}")
    
    total_sks = merged_df['sks'].sum()
    print("Jadwal Sudah Lengkap" if total_terisi == total_sks else "Jadwal Belum Lengkap")
    
    with open('backend/output.json', 'w') as f:
        json.dump(best_schedule, f, indent=4)