from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, Ruang, PreferensiDosen

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

def collect_conflicts(schedule, db: Session):
    conflict_temp_ids = set()
    lecturer_preferences = get_lecturer_preferences(db)
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
        
    def optimize(self, fitness_function, create_solution_function, collect_conflicts_func):
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
            
            print(f"Iterasi {iteration+1}/{self.max_iterations} - Best Fitness: {best_fitness}")
            
            new_population = []
            for i in range(self.population_size):
                if random.random() < 0.05:
                    new_solution = create_solution_function()
                else:
                    new_solution = self.update_position(
                        population[i], alpha, beta, delta, a, create_solution_function, fitness_function
                    )
                new_population.append(new_solution)
                fitness_values[i] = fitness_function(new_solution)
            population = new_population
        
        print("Optimasi Selesai!")
        print(f"Best Fitness: {best_fitness}")
        
        # Tandai slot-slot konflik pada solusi terbaik
        conflicts_detail = collect_conflicts_func(best_solution)
        conflict_numbers = set()
        for value in conflicts_detail.values():
            if isinstance(value, (set, list)):
                conflict_numbers.update(map(str, value))
            for slot in best_solution:
                tid = str(slot.get("temp_id", ""))
                if tid in conflict_numbers:
                    if tid in map(str, conflicts_detail['conflict_temp_ids']):
                        slot["status"] = "red"
                    elif tid in map(str, conflicts_detail['preference_conflict_temp_ids']):
                        slot["status"] = "yellow"
        return best_solution, best_fitness
    
    def update_position(self, current_solution, alpha, beta, delta, a, create_solution_function, fitness_function):
        new_solution = copy.deepcopy(current_solution)
        conflicts = collect_conflicts(new_solution, db)
        conflict_temp_ids = conflicts.get('conflict_temp_ids', set())
        if not conflict_temp_ids:
            return new_solution
        for tid in conflict_temp_ids:
            indices = [i for i, slot in enumerate(new_solution) if slot.get('temp_id') == tid]
            if not indices:
                continue
            candidate = None
            for source in [alpha, beta, delta]:
                source_block = [slot for slot in source if slot.get('temp_id') == tid]
                if source_block:
                    candidate = source_block[0]
                    break
            if candidate:
                course_info = {key: candidate[key] for key in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']}
                temp_solution = copy.deepcopy(new_solution)
                for idx in indices:
                    temp_solution[idx].update({k: None for k in ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']})
                success = any(self.schedule_course(temp_solution, course_info, relax=True) for _ in range(5))
                if not success:
                    success = self.schedule_course(temp_solution, course_info, force=True)
                if success:
                    new_solution = temp_solution
        return new_solution
    
    def schedule_course(self, schedule, course, force=False, relax=False):
        keys = ['id_mk', 'mata_kuliah', 'id_dosen', 'dosen', 'kelas', 'sks', 'semester', 'metode', 'temp_id']
        id_mk, mata_kuliah, id_dosen, dosen, kelas, sks, semester, metode, temp_id = (course[k] for k in keys)
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

def run_gwo_optimization(create_random_schedule_func, fitness_func, conflicts_func, pop_size, max_iter):
    gwo = GreyWolfOptimizer(population_size=pop_size, max_iterations=max_iter)
    return gwo.optimize(fitness_func, create_random_schedule_func, conflicts_func)

if __name__ == "__main__":
    pop_size = 5  
    max_iter = 5

    best_schedule, best_fitness = run_gwo_optimization(
        create_random_schedule,
        lambda sol: calculate_fitness(sol, db),
        lambda sol: collect_conflicts(sol, db),
        pop_size,
        max_iter
    )
    
    print(f"Optimasi selesai! Fitness terbaik: {best_fitness}")
    
    total_terisi = sum(1 for slot in best_schedule if slot['mata_kuliah'] is not None)
    print(f"Total slot terisi: {total_terisi}")
    
    total_sks = merged_df['sks'].sum()
    print("Jadwal Sudah Lengkap" if total_terisi == total_sks else "Jadwal Belum Lengkap")
    
    with open('backend/output.json', 'w') as f:
        json.dump(best_schedule, f, indent=4)