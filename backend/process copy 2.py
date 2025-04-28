import copy
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, PreferensiProdi, Ruang, PreferensiDosen

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

    # (C) Konflik Ruangan
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
        'conflict_temp_ids': conflict_temp_ids,
        'preference_conflict_temp_ids': preference_conflict_temp_ids
    }

def calculate_fitness(schedule, db: Session):
    conflicts = collect_conflicts(schedule, db)
    penalty = (
        len(conflicts['conflict_temp_ids']) +
        0.5 * len(conflicts['preference_conflict_temp_ids'])
    )
    return penalty

def fitness_function(solution):
    return sum(x**2 for x in solution)

def initialize_population(population_size):
    return [create_random_schedule() for _ in range(population_size)]

def update_position(schedule, alpha, beta, delta, a):
    new_schedule = copy.deepcopy(schedule)
    
    # Hitung parameter A dan C
    A1 = 2 * a * random.random() - a
    A2 = 2 * a * random.random() - a
    A3 = 2 * a * random.random() - a
    C1 = 2 * random.random()
    C2 = 2 * random.random()
    C3 = 2 * random.random()

    for slot in new_schedule:
        if slot['temp_id'] is None:
            continue
            
        # Dapatkan posisi pemimpin
        alpha_slot = next((s for s in alpha if s['temp_id'] == slot['temp_id']), None)
        beta_slot = next((s for s in beta if s['temp_id'] == slot['temp_id']), None)
        delta_slot = next((s for s in delta if s['temp_id'] == slot['temp_id']), None)

        # Hitung pergerakan menggunakan rumus GWO
        if alpha_slot and beta_slot and delta_slot:
            # Contoh implementasi numerik (butuh adaptasi lebih lanjut)
            D_alpha = abs(C1 * alpha_slot['id_slot'] - slot['id_slot'])
            D_beta = abs(C2 * beta_slot['id_slot'] - slot['id_slot'])
            D_delta = abs(C3 * delta_slot['id_slot'] - slot['id_slot'])
            
            X1 = alpha_slot['id_slot'] - A1 * D_alpha
            X2 = beta_slot['id_slot'] - A2 * D_beta
            X3 = delta_slot['id_slot'] - A3 * D_delta
            
            new_pos = (X1 + X2 + X3) // 3
            
            # Pindahkan ke posisi baru jika memungkinkan
            target_slot = next((s for s in new_schedule if s['id_slot'] == new_pos), None)
            if target_slot and target_slot['mata_kuliah'] is None:
                target_slot.update(slot)
                slot.clear()
    return new_schedule

class GreyWolfOptimizer:
    def __init__(self, population_size, max_iterations):
        self.population_size = population_size
        self.max_iterations = max_iterations

    def optimize(self, fitness_function, create_solution_function, db):
        # Inisialisasi populasi
        population = [create_solution_function() for _ in range(self.population_size)]
        alpha = beta = delta = None
        alpha_fit = beta_fit = delta_fit = float('inf')

        for schedule in population:
            conflicts = collect_conflicts(schedule, db)
            hard_constraints = conflicts['conflict_temp_ids']
            soft_constraints = conflicts['preference_conflict_temp_ids']

        for iter in range(self.max_iterations):
            # Hitung fitness
            fitness = [fitness_function(ind) for ind in population]
            
            # Update Alpha, Beta, Delta
            sorted_pairs = sorted(zip(population, fitness), key=lambda x: x[1])
            new_alpha, new_alpha_fit = sorted_pairs[0]
            new_beta, new_beta_fit = sorted_pairs[1]
            new_delta, new_delta_fit = sorted_pairs[2]

            if new_alpha_fit < alpha_fit:
                alpha, beta, delta = new_alpha, new_beta, new_delta
                alpha_fit, beta_fit, delta_fit = new_alpha_fit, new_beta_fit, new_delta_fit

            # Update parameter a
            a = 2 * (1 - iter/self.max_iterations)

            # Generate populasi baru
            new_population = []
            for i in range(self.population_size):
                # Pilih wolf untuk diupdate
                wolf = copy.deepcopy(population[i])
                
                # Update posisi berdasarkan Alpha, Beta, Delta
                updated_wolf = update_position(wolf, alpha, beta, delta, a)
                new_population.append(updated_wolf)

            population = new_population

            print(f"Iteration {iter+1}, Best Fitness: {alpha_fit}")

        return alpha, alpha_fit

if __name__ == "__main__":
    # Parameter GWO
    population_size = 10
    max_iterations = 50

    # Inisialisasi GWO
    gwo = GreyWolfOptimizer(population_size, max_iterations)

    # Optimasi
    best_schedule, best_fitness = gwo.optimize(
        fitness_function=lambda s: calculate_fitness(s, db),
        create_solution_function=create_random_schedule,
        db=db
    )

    total_terisi = sum(1 for slot in best_schedule if slot['mata_kuliah'] is not None)
    print(f"Total slot terisi: {total_terisi}")
    
    total_sks = merged_df['sks'].sum()
    print("Jadwal Sudah Lengkap" if total_terisi == total_sks else "Jadwal Belum Lengkap")
    
    print("Fitness Terbaik:", best_fitness)
    with open('backend/output.json', 'w') as f:
        json.dump(best_schedule, f, indent=4)