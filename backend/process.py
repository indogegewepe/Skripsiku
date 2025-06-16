import asyncio
import time
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Dosen, DataDosen, MkGenap, Hari, Jam, PreferensiProdi, Ruang, PreferensiDosen

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

semester_genap = [2, 4, 6, 8]
semester_ganjil = [1, 3, 5, 7]

def slot_generator():
    slots = []
    id_counter = 1
    for semester in semester_genap:
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
                        "semester": semester,
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
    merged_shuffled = merged_df.sort_values(by='sks', ascending=False).iterrows()

    for _, row in merged_shuffled:
        id_mk = row['id_mk_genap']
        mata_kuliah = row['nama_mk_genap']
        id_dosen = row['id_dosen']
        dosen = row['nama_dosen']
        kelas = row['kelas']
        sks = int(row['sks'])
        original_semester = row['smt']
        
        adjusted_semester = original_semester + 1 if original_semester % 2 != 0 else original_semester
        
        metode = row['metode']
        temp_id = row['temp_id']

        possible_positions = []
        for i in range(len(schedule) - sks + 1):
            block = schedule[i:i + sks]
            if all(
            slot['mata_kuliah'] is None and
            slot['hari'] == block[0]['hari'] and
            slot['ruang'] == block[0]['ruang'] and
            slot['semester'] == adjusted_semester 
            for slot in block):
                possible_positions.append(block)

        if not possible_positions:
            continue
        
        random.shuffle(possible_positions)
        for block in possible_positions:
                for slot in block:
                    slot.update({
                        "id_mk": id_mk,
                        "mata_kuliah": mata_kuliah,
                        "id_dosen": id_dosen,
                        "dosen": dosen,
                        "kelas": kelas,
                        "sks": sks,
                        "semester": adjusted_semester,
                        "metode": metode,
                        "temp_id": temp_id
                    })
                break
        else:
            print(f"Gagal menempatkan: {kelas} - {mata_kuliah} - {dosen} - Semester {adjusted_semester}")
            return 400, "gagal menempatkan mata kuliah"
    return schedule

# def create_random_schedule():
#     try:
#         schedule = slot_generator()
#         merged_shuffled = merged_df.sort_values(by='sks', ascending=False).iterrows()

#         for _, row in merged_shuffled:
#             id_mk = row['id_mk_genap']
#             mata_kuliah = row['nama_mk_genap']
#             id_dosen = row['id_dosen']
#             dosen = row['nama_dosen']
#             kelas = row['kelas']
#             sks = int(row['sks'])
#             original_semester = row['smt']

#             adjusted_semester = original_semester + 1 if original_semester % 2 != 0 else original_semester

#             metode = row['metode']
#             temp_id = row['temp_id']

#             possible_positions = []
#             for i in range(len(schedule) - sks + 1):
#                 block = schedule[i:i + sks]
#                 if all(
#                     slot['mata_kuliah'] is None and
#                     slot['hari'] == block[0]['hari'] and
#                     slot['ruang'] == block[0]['ruang'] and
#                     slot['semester'] == adjusted_semester
#                     for slot in block):
#                     possible_positions.append(block)

#             if not possible_positions:
#                 continue

#             random.shuffle(possible_positions)
#             for block in possible_positions:
#                 for slot in block:
#                     slot.update({
#                         "id_mk": id_mk,
#                         "mata_kuliah": mata_kuliah,
#                         "id_dosen": id_dosen,
#                         "dosen": dosen,
#                         "kelas": kelas,
#                         "sks": sks,
#                         "semester": adjusted_semester,
#                         "metode": metode,
#                         "temp_id": temp_id
#                     })
#                 break
#         return schedule
#     except Exception as e:
#         print("Terjadi kesalahan saat menyusun jadwal:")
#         print(e)
#         return 400, "Gagal menyusun jadwal karena kesalahan internal"

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

print("Preferensi Dosen:", get_lecturer_preferences(db))
print("Preferensi Prodi:", get_prodi_preferences(db))

def collect_conflicts(schedule, db: Session, prodi_id=None):
    conflict_temp_ids = set()
    lecturer_preferences = get_lecturer_preferences(db)
    prodi_prefs = get_prodi_preferences(db)

    room_consistency_conflicts = []
    semester_consistency_conflicts = []
    teacher_conflicts = []
    room_conflicts = []
    class_conflicts = []
    lecturer_preference_conflicts = []
    prodi_preference_conflicts = []
    preference_conflict_temp_ids = set()

    # (A) Konsistensi Ruangan dan Semester
    temp_groups = defaultdict(list)
    for slot in schedule:
        tid = slot.get('temp_id')
        if slot['mata_kuliah'] and tid is not None:
            temp_groups[tid].append(slot)
    for tid, slots in temp_groups.items():
        rooms = {slot['ruang'] for slot in slots}
        semesters = {slot.get('semester') for slot in slots}
        if len(rooms) > 1:
            conflict_temp_ids.add(tid)
            room_consistency_conflicts.append({
                'temp_id': tid,
                'ruangan': list(rooms),
                'slot_ids': [slot['id_slot'] for slot in slots]
            })
        if len(semesters) > 1:
            conflict_temp_ids.add(tid)
            semester_consistency_conflicts.append({
                'temp_id': tid,
                'semesters': list(semesters),
                'slot_ids': [slot['id_slot'] for slot in slots]
            })

    # (B) Konflik Dosen
    teacher_groups = defaultdict(list)
    for slot in schedule:
        if not slot['mata_kuliah']:
            continue
        teacher_groups[(slot['dosen'], slot['hari'].lower())].append(slot)
    for (dosen, hari), slots in teacher_groups.items():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                s1, s2 = slots[i], slots[j]
                if time_to_minutes(s2['jam_mulai']) < time_to_minutes(s1['jam_selesai']) and s1['mata_kuliah'] != s2['mata_kuliah']:
                    for s in (s1, s2):
                        tid = s.get('temp_id')
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    teacher_conflicts.append({
                        'dosen': dosen,
                        'hari': hari,
                        'slot_ids': [s1['id_slot'], s2['id_slot']]
                    })

    # (C) Konflik Ruangan
    room_groups = defaultdict(list)
    for slot in schedule:
        if not slot['mata_kuliah']:
            continue
        if slot['metode'] == "Online":
            continue
        room_groups[(slot['ruang'], slot['hari'].lower())].append(slot)
    for (ruang, hari), slots in room_groups.items():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                s1, s2 = slots[i], slots[j]
                if time_to_minutes(s2['jam_mulai']) <= time_to_minutes(s1['jam_selesai']) and s1['kelas'] != s2['kelas']:
                    for s in (s1, s2):
                        tid = s.get('temp_id')
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    room_conflicts.append({
                        'ruang': ruang,
                        'hari': hari,
                        'slot_ids': [s1['id_slot'], s2['id_slot']]
                    })

    # (D) Konflik Preferensi Dosen
    for slot in schedule:
        if not slot['mata_kuliah']:
            continue
        tid = slot.get('temp_id')
        if tid is None:
            continue
        dosen = str(slot['dosen'])
        hari = slot['hari'].lower()
        start = time_to_minutes(slot['jam_mulai'])

        if dosen not in lecturer_preferences:
            continue

        prefs = lecturer_preferences[dosen]
        for pref in prefs:
            if isinstance(pref, list):  # preferensi hari (daftar hari yang tidak boleh)
                if hari in pref:
                    lecturer_preference_conflicts.append({
                        'temp_id': tid,
                        'type': 'day',
                        'dosen': dosen,
                        'restricted_days': pref,
                        'slot_id': slot['id_slot']
                    })
                    preference_conflict_temp_ids.add(tid)
                    break
            elif isinstance(pref, dict):  # preferensi waktu
                jam_mulai_id = pref.get('jam_mulai_id')
                jam_selesai_id = pref.get('jam_selesai_id')
                if jam_mulai_id and jam_selesai_id:
                    allowed_start = time_to_minutes(jam_mulai_id)
                    allowed_end = time_to_minutes(jam_selesai_id)
                    if not (allowed_start <= start < allowed_end):
                        lecturer_preference_conflicts.append({
                            'temp_id': tid,
                            'type': 'time',
                            'dosen': dosen,
                            'allowed': (jam_mulai_id, jam_selesai_id),
                            'slot_id': slot['id_slot']
                        })
                        preference_conflict_temp_ids.add(tid)
                        break

    # (E) Konflik Kelas
    class_groups = defaultdict(list)
    for slot in schedule:
        if not slot['mata_kuliah']:
            continue
        class_groups[(slot['kelas'], slot['semester'], slot['hari'].lower())].append(slot)

    for key, slots in class_groups.items():
        # Hanya periksa bentrok jika semester dan kelas sama (berarti angkatan sama)
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                s1, s2 = slots[i], slots[j]
                if time_to_minutes(s2['jam_mulai']) < time_to_minutes(s1['jam_selesai']):
                    # Tambahkan validasi: skip jika dosennya berbeda dan ruangnya berbeda
                    if s1['dosen'] != s2['dosen'] and s1['ruang'] != s2['ruang']:
                        continue  # tidak dianggap bentrok
                    for s in (s1, s2):
                        tid = s.get('temp_id')
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    class_conflicts.append({
                        'kelas': key[0],
                        'hari': key[2],
                        'semester': key[1],
                        'slot_ids': [s1['id_slot'], s2['id_slot']]
                    })

    # (F) Konflik Preferensi Prodi
    for slot in schedule:
        if not slot['mata_kuliah']:
            continue
        tid = slot.get('temp_id')
        hari = slot['hari'].lower()
        start = time_to_minutes(slot['jam_mulai'])

        # Global restrictions
        rd = [d.lower() for d in prodi_prefs.get('restricted_days', [])]
        rtr = prodi_prefs.get('restricted_time_ranges', [])
        if hari in rd:
            for tr in rtr:
                rs, re = time_to_minutes(tr[0]), time_to_minutes(tr[1])
                if rs <= start < re:
                    prodi_preference_conflicts.append({
                        'temp_id': tid,
                        'type': 'global',
                        'restricted': tr,
                        'slot_id': slot['id_slot']
                    })
                    preference_conflict_temp_ids.add(tid)
                    break

        # Per-program preferences
        prefs = prodi_prefs.get(prodi_id, [])
        for pref in prefs:
            days = pref.get('hari') or []
            if isinstance(days, (int, str)):
                days = [int(days)] if str(days).isdigit() else []
            if hari in days:
                prodi_preference_conflicts.append({
                    'temp_id': tid,
                    'type': 'day_specific',
                    'slot_id': slot['id_slot'],
                    'restricted_days': days
                })
                preference_conflict_temp_ids.add(tid)
                continue
            if pref.get('jam_mulai_id') and pref.get('jam_selesai_id'):
                as_, ae = time_to_minutes(pref['jam_mulai_id']), time_to_minutes(pref['jam_selesai_id'])
                if start < as_ or start >= ae:
                    prodi_preference_conflicts.append({
                        'temp_id': tid,
                        'type': 'time_specific',
                        'allowed': (pref['jam_mulai_id'], pref['jam_selesai_id']),
                        'slot_id': slot['id_slot']
                    })
                    preference_conflict_temp_ids.add(tid)

    return {
        'conflict_temp_ids': conflict_temp_ids,
        'room_consistency_conflicts': room_consistency_conflicts,
        'semester_consistency_conflicts': semester_consistency_conflicts,
        'teacher_conflicts': teacher_conflicts,
        'room_conflicts': room_conflicts,
        'class_conflicts': class_conflicts,
        'lecturer_preference_conflicts': lecturer_preference_conflicts,
        'preference_conflict_temp_ids': preference_conflict_temp_ids
    }

def calculate_fitness(schedule, db: Session):
    conflicts = collect_conflicts(schedule, db)
    penalty = (
        len(conflicts['conflict_temp_ids']) +
        0.5 * len(conflicts['preference_conflict_temp_ids'])
    )
    print(f"Total conflicts: {len(conflicts['conflict_temp_ids'])}, Preference conflicts: {len(conflicts['preference_conflict_temp_ids'])}")
    return penalty

def update_position(schedule, alpha, beta, delta, a, collect_conflicts, db, fitness_function):
    new_schedule = [dict(slot) for slot in schedule]

    conflicts = collect_conflicts(new_schedule, db)
    # print(f"Konflik: {conflicts}")
    hard_constraints = conflicts['conflict_temp_ids']
    soft_constraints = conflicts['preference_conflict_temp_ids']

    temp_id_groups = defaultdict(list)
    for slot in new_schedule:
        if slot['temp_id'] is not None:
            temp_id_groups[slot['temp_id']].append(slot)

    def group_by_temp(schedule):
        temp_groups = defaultdict(list)
        for slot in schedule:
            if slot['temp_id'] is not None:
                temp_groups[slot['temp_id']].append(slot)
        return temp_groups

    alpha_groups = group_by_temp(alpha)
    beta_groups = group_by_temp(beta)
    delta_groups = group_by_temp(delta)

    def handle_constraints(constraint_ids, is_soft=False):
        for temp_id in constraint_ids:
            if temp_id not in temp_id_groups:
                continue

            slots_to_move = temp_id_groups[temp_id]
            sks = len(slots_to_move)

            r1 = random.random()
            A1 = 2 * a * r1 - a
            r1 = random.random()
            A2 = 2 * a * r1 - a
            r1= random.random()
            A3 = 2 * a * r1 - a

            if abs(A1) <= abs(A2) and abs(A1) <= abs(A3):
                ref_group = alpha_groups.get(temp_id, [])
            elif abs(A2) <= abs(A3):
                ref_group = beta_groups.get(temp_id, [])
            else:
                ref_group = delta_groups.get(temp_id, [])

            if not ref_group:
                continue

            possible_positions = []
            for i in range(len(new_schedule) - sks + 1):
                block = new_schedule[i:i + sks]
                selected_semester = ref_group[0]['semester']
                if all(
                    slot['mata_kuliah'] is None and
                    slot['hari'] == block[0]['hari'] and
                    slot['ruang'] == block[0]['ruang'] and
                    slot['semester'] == selected_semester and
                    not any(
                        s['id_dosen'] == slots_to_move[0]['id_dosen'] and
                        s['hari'] == slot['hari'] and
                        time_to_minutes(s['jam_mulai']) < time_to_minutes(slot['jam_selesai']) and
                        time_to_minutes(s['jam_selesai']) > time_to_minutes(slot['jam_mulai'])
                        for s in new_schedule if s['id_dosen'] is not None
                    )
                    for slot in block):
                    possible_positions.append(block)
                    
            if not possible_positions:
                continue

            new_block = random.choice(possible_positions)

            for old_slot, new_slot, ref_slot in zip(slots_to_move, new_block, ref_group):
                new_slot.update({
                    "id_mk": old_slot["id_mk"],
                    "mata_kuliah": old_slot["mata_kuliah"],
                    "id_dosen": old_slot["id_dosen"],
                    "dosen": old_slot["dosen"],
                    "semester": old_slot["semester"],
                    "kelas": old_slot["kelas"],
                    "sks": old_slot["sks"],
                    "metode": old_slot["metode"],
                    "temp_id": old_slot["temp_id"]
                })

                old_slot.update({
                    "id_mk": None, "mata_kuliah": None,
                    "id_dosen": None, "dosen": None, "kelas": None,
                    "sks": None, "metode": None,
                    "temp_id": None
                })

    handle_constraints(hard_constraints)
    handle_constraints(soft_constraints, is_soft=True)

    return new_schedule

class GreyWolfOptimizer:
    def __init__(self, population_size, max_iterations):
        self.population_size = population_size
        self.max_iterations = max_iterations

    async def optimize(self, fitness_function, create_solution_function, collect_conflicts, db: Session, log_callback=None):
        population = [create_solution_function() for _ in range(self.population_size)]
        fitness_values = [fitness_function(schedule) for schedule in population]
        # print(f"Populasi awal: {fitness_values}")

        best_solution = None
        best_fitness = float('inf')

        for iteration in range(self.max_iterations):
            sorted_pop = sorted(zip(population, fitness_values), key=lambda x: x[1])
            alpha, alpha_fitness = sorted_pop[0]
            beta, beta_fitness = sorted_pop[1]
            delta, delta_fitness = sorted_pop[2]

            if alpha_fitness < best_fitness:
                best_solution = alpha
                best_fitness = alpha_fitness

            log_message = f"Iterasi {iteration+1}/{self.max_iterations} - Best Fitness: {best_fitness}"
            
            print(log_message)
            if log_callback:
                log_callback(log_message)
            if best_fitness <= 0:
                print("Early stopping: solusi optimal ditemukan.")
                break

            a = 2 * (1 - iteration / self.max_iterations)

            new_population = []
            new_fitness_values = []

            for schedule in population:
                updated_schedule = update_position(schedule, alpha, beta, delta, a, collect_conflicts, db, fitness_function)
                new_population.append(updated_schedule)
                new_fitness_values.append(fitness_function(updated_schedule))

            population = new_population
            fitness_values = new_fitness_values

            await asyncio.sleep(1)

        print("Optimasi Selesai!")
        print(f"Best Fitness: {best_fitness}")
        
        conflicts_detail = collect_conflicts(best_solution, db)
        print(f"Detail Konflik: {conflicts_detail}")
        conflict_numbers = set()
        for value in conflicts_detail.values():
            if isinstance(value, (set, list)):
                conflict_numbers.update(map(str, value))
        for slot in best_solution:
            tid = str(slot.get("temp_id", ""))
            if tid in conflict_numbers:
                if tid in map(str, conflicts_detail.get('preference_conflict_temp_ids', [])):
                    slot["status"] = "yellow"  # Soft conflict
                elif tid in map(str, conflicts_detail.get('conflict_temp_ids', [])):
                    slot["status"] = "red"     # Hard conflict
        # tracked fitness hilangkan jika selesai pengujian
        return best_solution, best_fitness

if __name__ == "__main__":
    start_time = time.time()

    population_size = 5
    max_iterations = 5

    gwo = GreyWolfOptimizer(population_size, max_iterations)

    best_schedule, best_fitness = asyncio.run(gwo.optimize(
        fitness_function=lambda schedule: calculate_fitness(schedule, db),
        create_solution_function=create_random_schedule, 
        collect_conflicts=collect_conflicts, db=db, log_callback=None
        ))

    end_time = time.time()
    duration = end_time - start_time
    print(f"Waktu : {duration:.2f} detik")

    total_terisi = sum(1 for slot in best_schedule if slot['mata_kuliah'] is not None)
    print(f"Total slot terisi: {total_terisi}")

    total_sks = merged_df['sks'].sum()
    print("Jadwal Sudah Lengkap" if total_terisi == total_sks else "Jadwal Belum Lengkap")

    with open('backend/output.json', 'w') as f:
        json.dump(best_schedule, f, indent=4)