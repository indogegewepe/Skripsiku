import asyncio
import copy
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
semester_df = query_to_dataframe(db.query(MkGenap).distinct('smt').all())

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
    merged_shuffled = merged_df.sample(frac=1).iterrows()

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

        possible_positions = [
            i for i in range(len(schedule) - sks + 1)
            if all(
                slot['semester'] == adjusted_semester and 
                slot['mata_kuliah'] is None 
                for slot in schedule[i:i+sks]
            )
        ]
        random.shuffle(possible_positions)

        # Cari blok yang memenuhi syarat
        for i in possible_positions:
            block = schedule[i:i+sks]
            
            # Syarat: hari sama dan ruang sama
            if all(slot['hari'] == block[0]['hari'] and 
                   slot['ruang'] == block[0]['ruang'] 
                   for slot in block):
                
                # Update data slot
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
            print(f"Gagal menempatkan: {kelas} - {mata_kuliah} - {dosen} - {original_semester}")
            return 400, "gagal menempatkan mata kuliah"
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
        if hari:
            if isinstance(hari, list):
                restricted_days = [day_map.get(day, day) for day in hari]
            else:
                restricted_days = [day_map.get(hari, hari)]
            prodi_preferences["restricted_days"].extend(restricted_days)
        
        if jam_mulai_id is not None and jam_selesai_id is not None:
            start = jam_mulai_map.get(jam_mulai_id)
            end = jam_selesai_map.get(jam_selesai_id)
            if start and end:
                prodi_preferences["restricted_time_ranges"].append((start, end))
                
    return prodi_preferences

# Helper to check if two time intervals overlap (exclusive end/start)
def intervals_overlap(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1

def minutes_to_time(minutes):
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours:02d}:{minutes:02d}"

def collect_conflicts(schedule, db: Session):
    conflict_temp_ids = set()
    lecturer_preferences = get_lecturer_preferences(db)
    prodi_prefs = get_prodi_preferences(db)
    preference_conflict_temp_ids = set()

    # Inisialisasi semua daftar konflik
    room_consistency_conflicts = []
    teacher_conflicts = []        # Untuk konflik dosen (B)
    room_conflicts = []           # Untuk konflik ruangan (C)
    class_conflicts = []          # Untuk konflik kelas (E)
    lecturer_preference_conflicts = []  # Untuk preferensi dosen (D)
    prodi_preference_conflicts = []     # Untuk preferensi prodi (F)

    # (A) Konsistensi Ruangan
    temp_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is not None and slot.get('temp_id') is not None:
            temp_groups[slot['temp_id']].append(slot)
    for tid, slots in temp_groups.items():
        # Lewati jika semua slot dalam temp_id ini adalah online
        if all(slot.get('metode', 'offline').lower() == 'online' for slot in slots):
            continue
        # Cek apakah ada lebih dari satu ruangan berbeda
        unique_rooms = {slot['ruang'] for slot in slots}
        if len(unique_rooms) > 1:
            conflict_temp_ids.add(tid)
            room_consistency_conflicts.append({
                'temp_id': tid,
                'ruangan': list(unique_rooms),
                'slot_ids': [slot['id_slot'] for slot in slots]
            })

    # (B) Konflik Dosen
    teacher_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        teacher_groups[(slot['dosen'], slot['hari'].lower())].append(slot)
    
    for (dosen, hari), slots in teacher_groups.items():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                slot1 = slots[i]
                slot2 = slots[j]
                start1 = time_to_minutes(slot1['jam_mulai'])
                end1 = time_to_minutes(slot1['jam_selesai'])
                start2 = time_to_minutes(slot2['jam_mulai'])
                end2 = time_to_minutes(slot2['jam_selesai'])
                
                if intervals_overlap(start1, end1, start2, end2):
                    # Tambahkan temp_id ke set
                    for tid in (slot1.get('temp_id'), slot2.get('temp_id')):
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    
                    # Catat detail konflik
                    teacher_conflicts.append({
                        'dosen': dosen,
                        'hari': hari,
                        'slot1': {
                            'id_slot': slot1['id_slot'],
                            'temp_id': slot1.get('temp_id'),
                            'mata_kuliah': slot1['mata_kuliah'],
                            'jam': f"{slot1['jam_mulai']} - {slot1['jam_selesai']}"
                        },
                        'slot2': {
                            'id_slot': slot2['id_slot'],
                            'temp_id': slot2.get('temp_id'),
                            'mata_kuliah': slot2['mata_kuliah'],
                            'jam': f"{slot2['jam_mulai']} - {slot2['jam_selesai']}"
                        },
                        'overlap_time': f"{minutes_to_time(max(start1, start2))} - {minutes_to_time(min(end1, end2))}"
                    })

    # (C) Konflik Ruangan
    room_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        room_groups[(slot['ruang'], slot['hari'].lower())].append(slot)
    
    for (ruang, hari), slots in room_groups.items():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                slot1 = slots[i]
                slot2 = slots[j]
                start1 = time_to_minutes(slot1['jam_mulai'])
                end1 = time_to_minutes(slot1['jam_selesai'])
                start2 = time_to_minutes(slot2['jam_mulai'])
                end2 = time_to_minutes(slot2['jam_selesai'])
                
                if intervals_overlap(start1, end1, start2, end2) and slot1['kelas'] != slot2['kelas']:
                    # Tambahkan temp_id ke set
                    for tid in (slot1.get('temp_id'), slot2.get('temp_id')):
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    
                    # Catat detail konflik
                    room_conflicts.append({
                        'ruang': ruang,
                        'hari': hari,
                        'slot1': {
                            'id_slot': slot1['id_slot'],
                            'temp_id': slot1.get('temp_id'),
                            'kelas': slot1['kelas'],
                            'jam': f"{slot1['jam_mulai']} - {slot1['jam_selesai']}"
                        },
                        'slot2': {
                            'id_slot': slot2['id_slot'],
                            'temp_id': slot2.get('temp_id'),
                            'kelas': slot2['kelas'],
                            'jam': f"{slot2['jam_mulai']} - {slot2['jam_selesai']}"
                        },
                        'overlap_time': f"{minutes_to_time(max(start1, start2))} - {minutes_to_time(min(end1, end2))}"
                    })

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
                lecturer_preference_conflicts.append({
                    'temp_id': tid,
                    'dosen': dosen,
                    'alasan': 'Hari terlarang',
                    'hari': slot_day,
                    'slot_id': slot['id_slot'],
                    'jam': f"{slot['jam_mulai']} - {slot['jam_selesai']}"
                })
                preference_conflict_temp_ids.add(tid)
                continue
            if prefs['time_range']:
                allowed_start = time_to_minutes(prefs['time_range'][0])
                allowed_end = time_to_minutes(prefs['time_range'][1])
                slot_end = time_to_minutes(slot['jam_selesai'])
                if slot_start < allowed_start or slot_end > allowed_end:
                    lecturer_preference_conflicts.append({
                        'temp_id': tid,
                        'dosen': dosen,
                        'alasan': 'Waktu di luar preferensi',
                        'preferensi_waktu': f"{prefs['time_range'][0]} - {prefs['time_range'][1]}",
                        'hari': slot_day,
                        'slot_id': slot['id_slot'],
                        'jam': f"{slot['jam_mulai']} - {slot['jam_selesai']}"
                    })
                    preference_conflict_temp_ids.add(tid)
    
    # (E) Konflik Kelas
    class_groups = defaultdict(list)
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue
        class_groups[(slot['kelas'], slot['hari'].lower(), slot['semester'])].append(slot)
    
    for (kelas, hari, semester), slots in class_groups.items():
        slots.sort(key=lambda s: time_to_minutes(s['jam_mulai']))
        for i in range(len(slots)):
            for j in range(i+1, len(slots)):
                slot1 = slots[i]
                slot2 = slots[j]
                start1 = time_to_minutes(slot1['jam_mulai'])
                end1 = time_to_minutes(slot1['jam_selesai'])
                start2 = time_to_minutes(slot2['jam_mulai'])
                end2 = time_to_minutes(slot2['jam_selesai'])
                
                if intervals_overlap(start1, end1, start2, end2):
                    # Tambahkan temp_id ke set
                    for tid in (slot1.get('temp_id'), slot2.get('temp_id')):
                        if tid is not None:
                            conflict_temp_ids.add(tid)
                    
                    # Catat detail konflik
                    class_conflicts.append({
                        'kelas': kelas,
                        'semester': semester,
                        'hari': hari,
                        'slot1': {
                            'id_slot': slot1['id_slot'],
                            'temp_id': slot1.get('temp_id'),
                            'mata_kuliah': slot1['mata_kuliah'],
                            'jam': f"{slot1['jam_mulai']} - {slot1['jam_selesai']}"
                        },
                        'slot2': {
                            'id_slot': slot2['id_slot'],
                            'temp_id': slot2.get('temp_id'),
                            'mata_kuliah': slot2['mata_kuliah'],
                            'jam': f"{slot2['jam_mulai']} - {slot2['jam_selesai']}"
                        },
                        'overlap_time': f"{minutes_to_time(max(start1, start2))} - {minutes_to_time(min(end1, end2))}"
                    })

    # (F) Konflik Preferensi Prodi
    for slot in schedule:
        if slot['mata_kuliah'] is None:
            continue

        tid = slot.get('temp_id')
        slot_day = slot['hari'].lower()
        slot_start = time_to_minutes(slot['jam_mulai'])
        slot_end = time_to_minutes(slot['jam_selesai'])
        
        # Cek hari terlarang prodi
        restricted_days = [day.lower() for day in prodi_prefs.get('restricted_days', [])]
        for time_range in prodi_prefs.get('restricted_time_ranges', []):
            restricted_day = time_range['day'].lower()
            restricted_start = time_to_minutes(time_range['start'])
            restricted_end = time_to_minutes(time_range['end'])
            
            if slot_day == restricted_day and intervals_overlap(slot_start, slot_end, restricted_start, restricted_end):
                prodi_preference_conflicts.append({
                    'temp_id': tid,
                    'alasan': 'Konflik waktu terlarang prodi',
                    'hari': slot_day,
                    'waktu_terlarang': f"{time_range['start']} - {time_range['end']}",
                    'slot_id': slot['id_slot'],
                    'jam': f"{slot['jam_mulai']} - {slot['jam_selesai']}"
                })
                preference_conflict_temp_ids.add(tid)

    return {
        'conflict_temp_ids': conflict_temp_ids,
        'preference_conflict_temp_ids': preference_conflict_temp_ids,
        'room_consistency_conflicts': room_consistency_conflicts,
        'teacher_conflicts': teacher_conflicts,
        'room_conflicts': room_conflicts,
        'class_conflicts': class_conflicts,
        'lecturer_preference_conflicts': lecturer_preference_conflicts,
        'prodi_preference_conflicts': prodi_preference_conflicts
    }

def calculate_fitness(schedule, db: Session):
    conflicts = collect_conflicts(schedule, db)
    penalty = (
        len(conflicts['conflict_temp_ids']) +
        0.5 * len(conflicts['preference_conflict_temp_ids'])
    )
    return penalty

def update_position(schedule, alpha, beta, delta, a, collect_conflicts, db, fitness_function):
    # 1) Copy jadwal lama
    new_schedule = copy.deepcopy(schedule)

    # 2) Dapatkan konflik temp_id
    conflicts = collect_conflicts(new_schedule, db)
    hard_constraints = conflicts['conflict_temp_ids']
    soft_constraints = conflicts['preference_conflict_temp_ids']

    # 3) Siapkan grouping per temp_id
    def group_by_temp(sched):
        groups = defaultdict(list)
        for slot in sched:
            tid = slot.get('temp_id')
            if tid is not None:
                groups[tid].append(slot)
        return groups

    base_groups  = group_by_temp(new_schedule)
    alpha_groups = group_by_temp(alpha)
    beta_groups  = group_by_temp(beta)
    delta_groups = group_by_temp(delta)

    # fields yang ingin kita swap atomik
    SWAP_KEYS = [
        "id_mk", "mata_kuliah", "id_dosen", "dosen",
        "semester", "kelas", "sks", "metode", "temp_id"
    ]

    moved_temp_ids = set()

    def handle_constraints(constraint_ids, is_soft=False):
        for tid in constraint_ids:
            if tid not in base_groups:
                continue

            slots_to_move = base_groups[tid]
            sks = len(slots_to_move)
            
            original_semester = slots_to_move[0]['semester']

            r1 = random.random()
            A1 = 2 * a * r1 - a
            r1 = random.random()
            A2 = 2 * a * r1 - a
            r1= random.random()
            A3 = 2 * a * r1 - a

            # 2) Pilih ref_group berdasar |A|
            if abs(A1) <= abs(A2) and abs(A1) <= abs(A3):
                ref_group = alpha_groups.get(tid, [])
            elif abs(A2) <= abs(A3):
                ref_group = beta_groups.get(tid, [])
            else:
                ref_group = delta_groups.get(tid, [])

            if not ref_group:
                continue

            moved_temp_ids.add(tid)

            possible_indices = []
            total = len(new_schedule)
            for i in range(total - sks + 1):
                block = new_schedule[i : i + sks]
                
                # Syarat 1: hari dan ruang sama
                hari_ruang_ok = all(
                    slot['hari'] == block[0]['hari'] and 
                    slot['ruang'] == block[0]['ruang']
                    for slot in block
                )
                
                # Syarat 2: semester sama dengan asal
                semester_ok = all(slot['semester'] == original_semester for slot in block)
                
                # Syarat 3: slot kosong dan belum dipindah
                slot_kosong = all(
                    slot['mata_kuliah'] is None and 
                    slot.get('temp_id') not in moved_temp_ids
                    for slot in block
                )

                if hari_ruang_ok and semester_ok and slot_kosong:
                    possible_indices.append(i)

            if not possible_indices:
                continue

            start = random.choice(possible_indices)
            new_block = new_schedule[start : start + sks]

            # 4) Swap data atomik antara old_slot ↔ new_slot
            for old_slot, new_slot, _ in zip(slots_to_move, new_block, ref_group):
                old_data = {k: old_slot[k] for k in SWAP_KEYS}
                new_data = {k: new_slot[k] for k in SWAP_KEYS}

                # old_slot ← new_data (kosong), new_slot ← old_data (full)
                old_slot.update(new_data)
                new_slot.update(old_data)

    # Terapkan hard constraints dulu
    handle_constraints(hard_constraints, is_soft=False)
    # Lalu soft preferences
    handle_constraints(soft_constraints, is_soft=True)

    return new_schedule

class GreyWolfOptimizer:
    def __init__(self, population_size, max_iterations):
        self.population_size = population_size
        self.max_iterations = max_iterations

    async def optimize(self, fitness_function, create_solution_function, collect_conflicts, db: Session, log_callback=None):
        # Inisialisasi populasi awal
        population = [create_solution_function() for _ in range(self.population_size)]
        fitness_values = [fitness_function(schedule) for schedule in population]
        print(f"Populasi awal: {fitness_values}")

        best_solution = None
        best_fitness = float('inf')

        for iteration in range(self.max_iterations):
            # Urutkan berdasarkan fitness untuk menentukan alpha, beta, delta
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

            # Parameter a
            a = 2 * (1 - iteration / self.max_iterations)

            # Update populasi berdasarkan alpha, beta, delta
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
        print("\n=== Detail Konflik ===")

        # 1. Konflik Konsistensi Ruangan
        if conflicts_detail.get('room_consistency_conflicts'):
            print("\n[Konflik Konsistensi Ruangan]")
            for conflict in conflicts_detail['room_consistency_conflicts']:
                print(f"Temp ID {conflict['temp_id']}:")
                print(f"  Ruangan berbeda: {', '.join(conflict['ruangan'])}")
                print(f"  Slot IDs terlibat: {conflict['slot_ids']}")

        # 2. Konflik Dosen
        if conflicts_detail.get('teacher_conflicts'):
            print("\n[Konflik Jadwal Dosen]")
            for conflict in conflicts_detail['teacher_conflicts']:
                print(f"Dosen {conflict['dosen']} di hari {conflict['hari']}:")
                print(f"  Slot 1: {conflict['slot1']['mata_kuliah']} ({conflict['slot1']['jam']})")
                print(f"  Slot 2: {conflict['slot2']['mata_kuliah']} ({conflict['slot2']['jam']})")
                print(f"  Tumpang tindih: {conflict['overlap_time']}")

        # 3. Konflik Ruangan
        if conflicts_detail.get('room_conflicts'):
            print("\n[Konflik Penggunaan Ruangan]")
            for conflict in conflicts_detail['room_conflicts']:
                print(f"Ruang {conflict['ruang']} di hari {conflict['hari']}:")
                print(f"  Kelas {conflict['slot1']['kelas']}: {conflict['slot1']['jam']}")
                print(f"  Kelas {conflict['slot2']['kelas']}: {conflict['slot2']['jam']}")
                print(f"  Tumpang tindih: {conflict['overlap_time']}")

        # 4. Konflik Kelas
        if conflicts_detail.get('class_conflicts'):
            print("\n[Konflik Jadwal Kelas]")
            for conflict in conflicts_detail['class_conflicts']:
                print(f"Kelas {conflict['kelas']} (Semester {conflict['semester']}) di hari {conflict['hari']}:")
                print(f"  {conflict['slot1']['mata_kuliah']} ({conflict['slot1']['jam']})")
                print(f"  {conflict['slot2']['mata_kuliah']} ({conflict['slot2']['jam']})")
                print(f"  Tumpang tindih: {conflict['overlap_time']}")

        # 5. Konflik Preferensi Dosen
        if conflicts_detail.get('lecturer_preference_conflicts'):
            print("\n[Konflik Preferensi Dosen]")
            for conflict in conflicts_detail['lecturer_preference_conflicts']:
                print(f"Dosen {conflict['dosen']} - Temp ID {conflict['temp_id']}:")
                print(f"  Alasan: {conflict['alasan']}")
                if 'preferensi_waktu' in conflict:
                    print(f"  Preferensi: {conflict['preferensi_waktu']}")
                print(f"  Jadwal bermasalah: {conflict['jam']} di hari {conflict['hari']}")

        # 6. Konflik Preferensi Prodi
        if conflicts_detail.get('prodi_preference_conflicts'):
            print("\n[Konflik Preferensi Prodi]")
            for conflict in conflicts_detail['prodi_preference_conflicts']:
                print(f"Temp ID {conflict['temp_id']}:")
                print(f"  Alasan: {conflict['alasan']}")
                print(f"  Hari: {conflict['hari']}")
                print(f"  Waktu terlarang: {conflict['waktu_terlarang']}")
                print(f"  Jadwal bermasalah: {conflict['jam']}")

        # 7. Ringkasan Konflik
        print("\n=== Ringkasan Konflik ===")
        print(f"Total Hard Conflict (ID): {len(conflicts_detail['conflict_temp_ids'])}")
        print(f"Total Soft Conflict (ID): {len(conflicts_detail['preference_conflict_temp_ids'])}")
        print("Hard Conflict IDs:", conflicts_detail['conflict_temp_ids'])
        print("Soft Conflict IDs:", conflicts_detail['preference_conflict_temp_ids'])

        # Update status slot
        for slot in best_solution:
            tid = str(slot.get("temp_id", ""))
            if tid in map(str, conflicts_detail['preference_conflict_temp_ids']):
                slot["status"] = "yellow"  # Soft conflict
            elif tid in map(str, conflicts_detail['conflict_temp_ids']):
                slot["status"] = "red"     # Hard conflict

        return best_solution, best_fitness

if __name__ == "__main__":
    population_size = 5
    max_iterations = 5

    gwo = GreyWolfOptimizer(population_size, max_iterations)

    best_schedule, best_fitness = asyncio.run(gwo.optimize(
        fitness_function=lambda schedule: calculate_fitness(schedule, db),
        create_solution_function=create_random_schedule, 
        collect_conflicts=collect_conflicts, db=db, log_callback=None
        ))

    total_terisi = sum(1 for slot in best_schedule if slot['mata_kuliah'] is not None)
    print(f"Total slot terisi: {total_terisi}")

    total_sks = merged_df['sks'].sum()
    print("Jadwal Sudah Lengkap" if total_terisi == total_sks else "Jadwal Belum Lengkap")

    with open('backend/output.json', 'w') as f:
        json.dump(best_schedule, f, indent=4)