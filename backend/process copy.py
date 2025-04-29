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

def update_position(schedule, alpha, beta, delta, a, hard_constraints, soft_constraints):
    new_schedule = copy.deepcopy(schedule)

    # Kelompokkan slot berdasarkan temp_id
    temp_id_groups = defaultdict(list)
    for slot in new_schedule:
        if slot['temp_id'] is not None:
            temp_id_groups[slot['temp_id']].append(slot)

    # Kelompokkan slot dalam alpha, beta, delta berdasarkan temp_id
    alpha_temp_id_groups = defaultdict(list)
    for slot in alpha:
        if slot['temp_id'] is not None:
            alpha_temp_id_groups[slot['temp_id']].append(slot)

    beta_temp_id_groups = defaultdict(list)
    for slot in beta:
        if slot['temp_id'] is not None:
            beta_temp_id_groups[slot['temp_id']].append(slot)

    delta_temp_id_groups = defaultdict(list)
    for slot in delta:
        if slot['temp_id'] is not None:
            delta_temp_id_groups[slot['temp_id']].append(slot)

    # Prioritaskan pemindahan berdasarkan hard constraints (conflict_temp_ids)
    for temp_id in hard_constraints:
        if temp_id not in temp_id_groups:
            continue

        slots_to_move = temp_id_groups[temp_id]
        sks = len(slots_to_move)  # Jumlah SKS berdasarkan jumlah slot

        # Cari lokasi baru berdasarkan rumus GWO
        r = random.random()
        if r <= 0.2 and temp_id in alpha_temp_id_groups:
            selected_group = alpha_temp_id_groups[temp_id]
        elif 0.2 < r <= 0.5 and temp_id in beta_temp_id_groups:
            selected_group = beta_temp_id_groups[temp_id]
        else:
            selected_group = delta_temp_id_groups[temp_id]

        # Jika tidak ada lokasi referensi, lewati
        if not selected_group:
            continue

        # Cari blok kosong yang sesuai dengan jumlah SKS
        possible_positions = []
        for i in range(len(new_schedule) - sks + 1):
            block = new_schedule[i:i + sks]
            if all(slot['mata_kuliah'] is None for slot in block) and \
               all(slot['hari'] == block[0]['hari'] for slot in block) and \
               all(slot['ruang'] == block[0]['ruang'] for slot in block):
                possible_positions.append(block)

        # Jika tidak ada posisi yang memungkinkan, lewati
        if not possible_positions:
            continue

        # Pilih posisi baru berdasarkan rumus GWO
        new_block = random.choice(possible_positions)

        # Pindahkan data ke posisi baru
        for old_slot, new_slot, ref_slot in zip(slots_to_move, new_block, selected_group):
            new_slot.update({
                "id_mk": old_slot["id_mk"],          # Ambil dari old_slot
                "mata_kuliah": old_slot["mata_kuliah"],
                "id_dosen": old_slot["id_dosen"],
                "dosen": old_slot["dosen"],
                "semester": old_slot["semester"],
                "kelas": old_slot["kelas"],
                "sks": old_slot["sks"],              # SKS dipertahankan
                "metode": old_slot["metode"],
                "temp_id": old_slot["temp_id"]
            })

            # Kosongkan slot lama
            old_slot.update({
                "id_mk": None,
                "mata_kuliah": None,
                "id_dosen": None,
                "dosen": None,
                "semester": None,
                "kelas": None,
                "sks": None,
                "metode": None,
                "temp_id": None
            })

    # Tangani soft constraints (preference_conflict_temp_ids) jika diperlukan
    for temp_id in soft_constraints:
        if temp_id not in temp_id_groups:
            continue

        slots_to_move = temp_id_groups[temp_id]
        sks = len(slots_to_move)  # Jumlah SKS berdasarkan jumlah slot

        # Cari lokasi baru berdasarkan rumus GWO
        r = random.random()
        if r <= 0.1 and temp_id in alpha_temp_id_groups:
            selected_group = alpha_temp_id_groups[temp_id]
        elif 0.4 < r <= 0.7 and temp_id in beta_temp_id_groups:
            selected_group = beta_temp_id_groups[temp_id]
        else:
            selected_group = delta_temp_id_groups[temp_id]

        # Jika tidak ada lokasi referensi, lewati
        if not selected_group:
            continue

        # Cari blok kosong yang sesuai dengan jumlah SKS
        possible_positions = []
        for i in range(len(new_schedule) - sks + 1):
            block = new_schedule[i:i + sks]
            if all(slot['mata_kuliah'] is None for slot in block) and \
               all(slot['hari'] == block[0]['hari'] for slot in block) and \
               all(slot['ruang'] == block[0]['ruang'] for slot in block):
                possible_positions.append(block)

        # Jika tidak ada posisi yang memungkinkan, lewati
        if not possible_positions:
            continue

        # Pilih posisi baru berdasarkan rumus GWO
        new_block = random.choice(possible_positions)

        # Pindahkan data ke posisi baru
        for old_slot, new_slot, ref_slot in zip(slots_to_move, new_block, selected_group):
            new_slot.update({
                "id_mk": old_slot["id_mk"],          # Ambil dari old_slot
                "mata_kuliah": old_slot["mata_kuliah"],
                "id_dosen": old_slot["id_dosen"],
                "dosen": old_slot["dosen"],
                "semester": old_slot["semester"],
                "kelas": old_slot["kelas"],
                "sks": old_slot["sks"],              # SKS dipertahankan
                "metode": old_slot["metode"],
                "temp_id": old_slot["temp_id"]
            })

            # Kosongkan slot lama
            old_slot.update({
                "id_mk": None,
                "mata_kuliah": None,
                "id_dosen": None,
                "dosen": None,
                "semester": None,
                "kelas": None,
                "sks": None,
                "metode": None,
                "temp_id": None
            })

    return new_schedule

class GreyWolfOptimizer:
    def __init__(self, population_size, max_iterations):
        self.population_size = population_size
        self.max_iterations = max_iterations

    def optimize(self, fitness_function, create_solution_function, collect_conflicts, db: Session):
        # Inisialisasi populasi
        population = [create_solution_function() for _ in range(self.population_size)]
        fitness_values = [fitness_function(schedule) for schedule in population]
        for schedule in population:
            conflicts = collect_conflicts(schedule, db)
            hard_constraints = conflicts['conflict_temp_ids']
            soft_constraints = conflicts['preference_conflict_temp_ids']

        # Inisialisasi Alpha, Beta, Delta
        alpha, beta, delta = None, None, None
        alpha_fitness, beta_fitness, delta_fitness = float('inf'), float('inf'), float('inf')

        for iteration in range(self.max_iterations):
            # Update Alpha, Beta, Delta
            for i in range(self.population_size):
                fitness = fitness_values[i]
                if fitness < alpha_fitness:
                    alpha, beta, delta = population[i], alpha, beta
                    alpha_fitness, beta_fitness, delta_fitness = fitness, alpha_fitness, beta_fitness
                elif fitness < beta_fitness:
                    beta, delta = population[i], beta
                    beta_fitness, delta_fitness = fitness, beta_fitness
                elif fitness < delta_fitness:
                    delta = population[i]
                    delta_fitness = fitness

            # Parameter a
            a = 2 * (1 - iteration / self.max_iterations)

            # Update populasi
            new_population = []
            for schedule in population:
                new_schedule = update_position(schedule, alpha, beta, delta, a, hard_constraints, soft_constraints)
                new_population.append(new_schedule)
            population = new_population

            # Hitung fitness baru
            fitness_values = [fitness_function(schedule) for schedule in population]

            # Logging
            print(f"Iterasi {iteration+1}/{self.max_iterations}, Best Fitness: {alpha_fitness}")

        return alpha, alpha_fitness

if __name__ == "__main__":
    # Parameter GWO
    population_size = 30
    max_iterations = 30

    # Inisialisasi GWO
    gwo = GreyWolfOptimizer(population_size, max_iterations)

    # Optimasi
    best_schedule, best_fitness = gwo.optimize(
        fitness_function=lambda schedule: calculate_fitness(schedule, db),
        create_solution_function=create_random_schedule, 
        collect_conflicts=collect_conflicts, db=db
    )

    total_terisi = sum(1 for slot in best_schedule if slot['mata_kuliah'] is not None)
    print(f"Total slot terisi: {total_terisi}")
    
    total_sks = merged_df['sks'].sum()
    print("Jadwal Sudah Lengkap" if total_terisi == total_sks else "Jadwal Belum Lengkap")
    
    print("Fitness Terbaik:", best_fitness)
    with open('backend/output.json', 'w') as f:
        json.dump(best_schedule, f, indent=4)