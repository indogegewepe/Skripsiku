from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, Ruang

import copy
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict
import random

def query_to_dataframe(query_result):
    """Convert a list of SQLAlchemy model instances to a pandas DataFrame."""
    dict_list = [item.__dict__ for item in query_result]
    # Remove SQLAlchemy internal state before converting
    for d in dict_list:
        d.pop("_sa_instance_state", None)
    return pd.DataFrame(dict_list)
def query_to_dataframe(query_result):
    """Convert a list of SQLAlchemy model instances to a pandas DataFrame."""
    dict_list = [item.__dict__ for item in query_result]
    # Hapus atribut internal SQLAlchemy
    for d in dict_list:
        d.pop("_sa_instance_state", None)
    return pd.DataFrame(dict_list)

# Mendapatkan session secara langsung (pastikan untuk menutup session setelah selesai)
db: Session = next(get_db())

# Mengambil data dari database
dosen_records = db.query(Dosen).all()
mk_genap_records = db.query(MkGenap).all()
data_dosen_records = db.query(DataDosen).all()
hari_records = db.query(Hari).all()
ruang_records = db.query(Ruang).all()
jam_records = db.query(Jam).all()

# Mengonversi query result menjadi DataFrame
dosen_df = query_to_dataframe(dosen_records)
mk_genap_df = query_to_dataframe(mk_genap_records)
data_dosen_df = query_to_dataframe(data_dosen_records)
hari_df = query_to_dataframe(hari_records)
ruang_df = query_to_dataframe(ruang_records)
jam_df = query_to_dataframe(jam_records)

# Fungsi konversi waktu ke menit
def time_to_minutes(t):
    try:
        dt = datetime.strptime(t, "%H:%M:%S")
    except ValueError:
        dt = datetime.strptime(t, "%H:%M")
    return dt.hour * 60 + dt.minute

# Urutkan jam_df sebelum generate slot
jam_df = jam_df.sort_values('id_jam')

# Gabungkan data menggunakan merge
merged_df = pd.merge(
    pd.merge(data_dosen_df, dosen_df, on='id_dosen'),
    mk_genap_df, on='id_mk_genap'
)

# Tambahkan temporary id secara unik untuk setiap baris di merged_df
merged_df['temp_id'] = range(1, len(merged_df) + 1)

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
                    "kelas": None,
                    "sks": None,
                    "metode": None,
                    "temp_id": None  # Akan diisi jika slot terisi course
                })
                id_counter += 1
    return slots

def create_random_schedule():
    schedule = slot_generator()
    merged_shuffled = merged_df.iterrows()
    
    # Tracking alokasi (untuk referensi)
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
        metode = row['metode']
        temp_id = row['temp_id']  # temporary id course
        
        possible_positions = list(range(len(schedule) - sks + 1))
        random.shuffle(possible_positions)
        
        candidate_blocks = []
        for i in possible_positions:
            block = schedule[i:i+sks]
            if not all(slot['mata_kuliah'] is None for slot in block) or not all(slot['hari'] == block[0]['hari'] for slot in block):
                continue
            if not all(slot['ruang'] == block[0]['ruang'] for slot in block):
                continue
            hari = block[0]['hari']
            ruang = block[0]['ruang']
            time_block = (time_to_minutes(block[0]['jam_mulai']), time_to_minutes(block[-1]['jam_selesai']))
            kelas_already = len(class_allocations[(kelas, hari)]) > 0
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
                    "metode": metode,
                    "temp_id": temp_id
                })
            hari = selected_block[0]['hari']
            ruang = selected_block[0]['ruang']
            time_block = (time_to_minutes(selected_block[0]['jam_mulai']),
                          time_to_minutes(selected_block[-1]['jam_selesai']))
            room_allocations[(ruang, hari)].append(time_block)
            teacher_allocations[(dosen, hari)].append(time_block)
            class_allocations[(kelas, hari)].append(time_block)
        else:
            print(f"Gagal menempatkan: {kelas} - {mata_kuliah} - {dosen}")
    
    return schedule

def detect_time_conflicts(intervals):
    conflicts = []
    intervals.sort(key=lambda x: x[0])
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i-1][1]:
            conflicts.append((intervals[i-1][2], intervals[i][2]))
    return conflicts

# Fungsi untuk mengambil konfigurasi preferensi dosen
def get_lecturer_preferences():
    return {
        "Ardiansyah, Dr., S.T., M.Cs.": [
            {"type": "time_before", "value": 720}  # Tidak ada kelas sebelum 12:00 PM (720 menit)
        ],
        "Ali Tarmuji, S.T., M.Cs.": [
            {"type": "restricted_day", "value": "sabtu"}  # Tidak ada kelas pada hari Sabtu
        ],
        "Bambang Robiin, S.T., M.T.": [
            {"type": "time_after", "value": 720}  # Tidak ingin kelas setelah 12:00 PM
        ],
        "Tedy Setiadi, Drs., M.T.": [
            {"type": "restricted_day", "value": "sabtu, kamis"}  # Tidak ada kelas pada hari Sabtu atau Kamis
        ]
    }

def collect_conflicts(schedule):
    conflict_temp_ids = set()
    lecturer_preferences = get_lecturer_preferences()
    preference_conflict_temp_ids = set()
    
    # --- (A) Konsistensi Ruangan dalam satu temp_id ---
    temp_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is not None and slot.get('temp_id') is not None:
            temp_groups[slot['temp_id']].append(slot)
    room_consistency_conflicts = []
    for tid, slots in temp_groups.items():
        ruangan_set = {slot['ruang'] for slot in slots}
        if len(ruangan_set) > 1:
            conflict_temp_ids.add(tid)
            room_consistency_conflicts.append({
                'temp_id': tid,
                'ruangan': list(ruangan_set),
                'slot_ids': [slot['id_slot'] for slot in slots]
            })
    
    # --- (D) Urutan Slot: Temp_id yang sama harus berurutan ---
    sequence_conflicts = []
    for tid, slots in temp_groups.items():
        if len(slots) > 1:
            sorted_slots = sorted(slots, key=lambda s: s['id_slot'])
            expected_ids = list(range(sorted_slots[0]['id_slot'], sorted_slots[0]['id_slot'] + len(sorted_slots)))
            actual_ids = [slot['id_slot'] for slot in sorted_slots]
            if actual_ids != expected_ids:
                conflict_temp_ids.add(tid)
                sequence_conflicts.append({
                    'temp_id': tid,
                    'expected_ids': expected_ids,
                    'actual_ids': actual_ids
                })
    
    # --- (B) Konflik Dosen: Dosen tidak boleh mengajar 2 course berbeda pada jam/hari yang sama ---
    teacher_conflicts = []
    teacher_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        key = (slot['dosen'], slot['hari'].lower())
        teacher_groups[key].append(slot)
    for (dosen, hari), slots in teacher_groups.items():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                start_i = time_to_minutes(slots[i]['jam_mulai'])
                end_i = time_to_minutes(slots[i]['jam_selesai'])
                start_j = time_to_minutes(slots[j]['jam_mulai'])
                if start_j < end_i and slots[i]['mata_kuliah'] != slots[j]['mata_kuliah']:
                    # Tambahkan temp_id dari kedua slot (jika ada)
                    tid_i = slots[i].get('temp_id')
                    tid_j = slots[j].get('temp_id')
                    if tid_i is not None:
                        conflict_temp_ids.add(tid_i)
                    if tid_j is not None:
                        conflict_temp_ids.add(tid_j)
                    teacher_conflicts.append((slots[i]['id_slot'], slots[j]['id_slot']))
    
    # --- (C) Konflik Ruangan: Ruang yang sama tidak boleh digunakan untuk 2 kelas berbeda pada jam/hari yang sama ---
    room_conflicts = []
    room_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        key = (slot['ruang'], slot['hari'].lower())
        room_groups[key].append(slot)
    for (ruang, hari), slots in room_groups.items():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                start_i = time_to_minutes(slots[i]['jam_mulai'])
                end_i = time_to_minutes(slots[i]['jam_selesai'])
                start_j = time_to_minutes(slots[j]['jam_mulai'])
                if start_j < end_i and slots[i]['kelas'] != slots[j]['kelas']:
                    tid_i = slots[i].get('temp_id')
                    tid_j = slots[j].get('temp_id')
                    if tid_i is not None:
                        conflict_temp_ids.add(tid_i)
                    if tid_j is not None:
                        conflict_temp_ids.add(tid_j)
                    room_conflicts.append((slots[i]['id_slot'], slots[j]['id_slot']))
    
    # --- Preferensi Dosen: ---
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        start = time_to_minutes(slot['jam_mulai'])
        tid = slot.get('temp_id')
        dosen = str(slot['dosen'])
        hari = slot['hari'].lower()
        if dosen in lecturer_preferences:
            for pref in lecturer_preferences[dosen]:
                violated = False
                if pref["type"] == "time_before" and start < pref["value"]:
                    violated = True
                elif pref["type"] == "time_after" and start >= pref["value"]:
                    violated = True
                elif pref["type"] == "restricted_day":
                    days = [d.strip() for d in pref["value"].split(',')]
                    if hari in days:
                        violated = True
                if violated and tid is not None:
                    preference_conflict_temp_ids.add(tid)
    
    # --- SKS Conflict: Jumlah slot pada course harus sesuai dengan SKS ---
    sks_conflicts = []
    course_teacher_class = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        key = (slot['mata_kuliah'], slot['dosen'], slot['kelas'])
        course_teacher_class[key].append(slot)
    for key, slots in course_teacher_class.items():
        expected_slots = slots[0]['sks']
        if len(slots) != expected_slots:
            for s in slots:
                tid = s.get('temp_id')
                if tid is not None:
                    conflict_temp_ids.add(tid)
            sks_conflicts.append({
                'course_key': key,
                'expected': expected_slots,
                'actual': len(slots)
            })
    
    return {
        'conflict_temp_ids': conflict_temp_ids,
        'preference_conflict_temp_ids': preference_conflict_temp_ids,
        'teacher_conflicts': teacher_conflicts,   
        'room_conflicts': room_conflicts,           
        'room_consistency_conflicts': room_consistency_conflicts,  
        'sequence_conflicts': sequence_conflicts,   
        'sks_conflicts': sks_conflicts,
    }

def calculate_fitness(schedule):
    conflicts = collect_conflicts(schedule)
    penalty = 0.0
    # Setiap konflik (berdasarkan temp_id) diberi penalty 1, kecuali preferensi yang diberi 0.5
    penalty += len(conflicts['teacher_conflicts']) * 1.0
    penalty += len(conflicts['room_conflicts']) * 1.0
    penalty += len(conflicts['room_consistency_conflicts']) * 1.0
    penalty += len(conflicts['sequence_conflicts']) * 1.0
    penalty += len(conflicts['sks_conflicts']) * 1.0
    penalty += len(conflicts['preference_conflict_temp_ids']) * 0.5
    return penalty

class GreyWolfOptimizer:
    def __init__(self, population_size=10, max_iterations=50):
        self.population_size = population_size
        self.max_iterations = max_iterations
        
    def optimize(self, fitness_function, create_solution_function, collect_conflicts_func):
        # Inisialisasi populasi
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
            alpha_fitness = fitness_values[sorted_indices[0]]
            
            if alpha_fitness < best_fitness:
                best_fitness = alpha_fitness
                best_solution = copy.deepcopy(alpha)
            
            print(f"Iterasi {iteration+1}/{self.max_iterations} - Best Fitness: {best_fitness}")
            
            new_population = []
            for i in range(self.population_size):
                # Dengan probabilitas kecil lakukan random restart
                if random.random() < 0.05:
                    new_solution = create_solution_function()
                else:
                    new_solution = self.update_position(population[i], alpha, beta, delta, a, create_solution_function, fitness_function)
                new_population.append(new_solution)
                fitness_values[i] = fitness_function(new_solution)
            
            population = new_population
        
        print("Optimasi Selesai!")
        print(f"Best Fitness: {best_fitness}")
        
        cek_konflik = collect_conflicts_func(best_solution)
        conflict_numbers = set()
        print(cek_konflik)

        # Gabungkan semua angka dari semua jenis konflik
        for key, value in cek_konflik.items():
            if isinstance(value, (set, list)):
                conflict_numbers.update(map(str, value))  # Ubah semua angka ke string untuk konsistensi

        # Tandai jadwal dengan status 'code_red' jika 'temp_id' sama persis dengan angka konflik
        for slot in best_solution:
            temp_id = str(slot.get("temp_id", ""))
            if temp_id in conflict_numbers:
                if "status" in slot and slot["status"]:
                    if "code_red" not in slot["status"]:
                        slot["status"] += ", code_red"
                else:
                    slot["status"] = "code_red"
        return best_solution, best_fitness
    
    def update_position(self, current_solution, alpha, beta, delta, a, create_solution_function, fitness_function):
        new_solution = copy.deepcopy(current_solution)
        
        # Dapatkan temp_id yang mengalami konflik dari solusi saat ini
        conflicts = collect_conflicts(new_solution)
        conflict_temp_ids = conflicts.get('conflict_temp_ids', set())
        
        # Jika tidak ada konflik, kembalikan solusi tanpa perubahan
        if not conflict_temp_ids:
            return new_solution
        
        # Fokus pada setiap temp_id yang bermasalah
        for tid in conflict_temp_ids:
            # Dapatkan indeks slot yang memiliki temp_id ini
            indices = [i for i, slot in enumerate(new_solution) if slot.get('temp_id') == tid]
            if not indices:
                continue 
            
            candidate = None
            for source in [alpha, beta, delta]:
                source_block = [slot for slot in source if slot.get('temp_id') == tid]
                if source_block:
                    candidate = source_block[0]
                    break
            
            if candidate is not None:
                course_info = {
                    'id_mk': candidate['id_mk'],
                    'mata_kuliah': candidate['mata_kuliah'],
                    'id_dosen': candidate['id_dosen'],
                    'dosen': candidate['dosen'],
                    'kelas': candidate['kelas'],
                    'sks': candidate['sks'],
                    'metode': candidate['metode'],
                    'temp_id': candidate['temp_id']
                }
                # Buat salinan sementara dari solusi untuk mencoba repair
                temp_solution = copy.deepcopy(new_solution)
                # Reset blok pada temp_solution
                for idx in indices:
                    temp_solution[idx].update({
                        "id_mk": None,
                        "mata_kuliah": None,
                        "id_dosen": None,
                        "dosen": None,
                        "kelas": None,
                        "sks": None,
                        "metode": None,
                        "temp_id": None
                    })
                # Coba jadwalkan ulang kursus pada temp_solution dengan opsi relax
                repair_attempts = 5
                success = False
                for _ in range(repair_attempts):
                    if self.schedule_course(temp_solution, course_info, relax=True):
                        success = True
                        break
                if not success:
                    # Jika repair dengan relax gagal, coba dengan force
                    if self.schedule_course(temp_solution, course_info, force=True):
                        success = True
                # Jika berhasil, update new_solution dengan temp_solution untuk blok tersebut
                if success:
                    new_solution = temp_solution
                # Jika tidak berhasil, biarkan blok asli tidak diubah (tidak direset)
        
        return new_solution
    
    def schedule_course(self, schedule, course, force=False, relax=False):
        id_mk = course['id_mk']
        mata_kuliah = course['mata_kuliah']
        id_dosen = course['id_dosen']
        dosen = course['dosen']
        kelas = course['kelas']
        sks = course['sks']
        metode = course['metode']
        temp_id = course['temp_id']
        
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
                time_diff = abs(time_to_minutes(block[j]['jam_mulai']) - time_to_minutes(block[j-1]['jam_selesai']))
                if not relax and time_diff != 0:
                    valid = False
                    break
                elif relax and time_diff > 5:
                    valid = False
                    break
            if valid:
                possible_positions.append(i)
        
        if possible_positions:
            pos = random.choice(possible_positions)
            block = schedule[pos:pos+sks]
            for slot in block:
                slot.update({
                    "id_mk": id_mk,
                    "mata_kuliah": mata_kuliah,
                    "id_dosen": id_dosen,
                    "dosen": dosen,
                    "kelas": kelas,
                    "sks": sks,
                    "metode": metode,
                    "temp_id": temp_id
                })
            return True
        
        if force and sks == 1:
            empty_slots = [i for i, slot in enumerate(schedule) if slot['mata_kuliah'] is None]
            if empty_slots:
                pos = random.choice(empty_slots)
                schedule[pos].update({
                    "id_mk": id_mk,
                    "mata_kuliah": mata_kuliah,
                    "id_dosen": id_dosen,
                    "dosen": dosen,
                    "kelas": kelas,
                    "sks": sks,
                    "metode": metode,
                    "temp_id": temp_id
                })
                return True
        
        return False

def run_gwo_optimization(create_random_schedule_func, calculate_fitness_func, collect_conflicts_func, population_size=10, max_iterations=100):
    gwo = GreyWolfOptimizer(population_size, max_iterations)
    best_solution, best_fitness = gwo.optimize(calculate_fitness_func, create_random_schedule_func, collect_conflicts_func)
    return best_solution, best_fitness

if __name__ == "__main__":
    best_schedule, best_fitness = run_gwo_optimization(
        create_random_schedule,
        calculate_fitness,
        collect_conflicts,
        population_size=10,
        max_iterations=50
    )
    
    print(f"Optimasi selesai! Fitness terbaik: {best_fitness}")
    
    total_terisi = sum(1 for slot in best_schedule if slot['mata_kuliah'] is not None)
    print(f"Total slot terisi: {total_terisi}")
    
    total_sks = merged_df['sks'].sum()
    if total_terisi == total_sks:
        print("Jadwal Sudah Lengkap")
    else:
        print("Jadwal Belum Lengkap")






