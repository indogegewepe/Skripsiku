import random
import copy
import numpy as np
import pandas as pd
import json
from datetime import datetime
from collections import defaultdict

# Fungsi konversi waktu ke menit
def time_to_minutes(t):
    try:
        dt = datetime.strptime(t, "%H:%M:%S")
    except ValueError:
        dt = datetime.strptime(t, "%H:%M")
    return dt.hour * 60 + dt.minute

# Generator slot jadwal
def slot_generator():
    wolf = []
    id_counter = 1
    # Asumsi file CSV sudah dibaca sebelumnya
    # Data hari, ruang, dan jam
    hari_df = pd.read_csv('data_skripsi_hari.csv')
    ruang_df = pd.read_csv('data_skripsi_ruang.csv')
    jam_df = pd.read_csv('data_skripsi_jam.csv')
    
    for hari in hari_df['nama_hari']:
        for ruang in ruang_df['nama_ruang']:
            for jam in jam_df.itertuples():
                wolf.append({
                    "id_slot": id_counter,
                    "mata_kuliah": None,
                    "dosen": None,
                    "ruang": ruang,
                    "hari": hari,
                    "jam_mulai": jam.jam_awal,
                    "jam_selesai": jam.jam_akhir,
                    "kelas": None,
                    "sks": None,
                    "metode": None
                })
                id_counter += 1
    return wolf

# Membuat jadwal acak berdasarkan data mata kuliah dan dosen
def create_random_schedule(ordered_courses_df=None):
    schedule = slot_generator()
    # Ambil data dari merged_df (asumsi sudah didefinisikan dan berisi data gabungan)
    # merged_df harus berisi kolom: 'nama_mk_genap', 'nama_dosen', 'kelas', 'sks', 'metode'
    if ordered_courses_df is None:
        # Acak urutan mata kuliah
        merged_df = pd.read_csv('data_skripsi_mk_genap.csv')
        # Gabungkan dengan data dosen jika diperlukan (sesuaikan dengan kebutuhan)
        merged_shuffled = merged_df.sample(frac=1).iterrows()
    else:
        merged_shuffled = ordered_courses_df.iterrows()
    
    # Tracking alokasi (untuk referensi)
    room_allocations = defaultdict(list)
    teacher_allocations = defaultdict(list)
    class_allocations = defaultdict(list)
    
    for _, row in merged_shuffled:
        mata_kuliah = row['nama_mk_genap']
        dosen = row['nama_dosen']
        kelas = row['kelas']
        sks = int(row['sks'])
        metode = row['metode']
        
        possible_positions = list(range(len(schedule) - sks + 1))
        random.shuffle(possible_positions)
        
        candidate_blocks = []
        for i in possible_positions:
            block = schedule[i:i+sks]
            # Pastikan semua slot kosong dan berada di hari yang sama
            if not all(slot['mata_kuliah'] is None for slot in block) or not all(slot['hari'] == block[0]['hari'] for slot in block):
                continue
            # Cek konsistensi ruangan
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
                    "mata_kuliah": mata_kuliah,
                    "dosen": dosen,
                    "kelas": kelas,
                    "sks": sks,
                    "metode": metode
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

# Fungsi pembantu: Deteksi konflik pada kumpulan interval waktu
def detect_time_conflicts(intervals):
    conflicts = []
    intervals.sort(key=lambda x: x[0])
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i-1][1]:
            conflicts.append((intervals[i-1][2], intervals[i][2]))
    return conflicts

# Fungsi konfigurasi preferensi dosen (hanya dua dosen sesuai permintaan)
def get_lecturer_preferences():
    return {
        "Ardiansyah, Dr., S.T., M.Cs.": [
            {"type": "time_before", "value": 720}  # Tidak ada kelas sebelum 12:00 PM
        ],
        "Ali Tarmuji, S.T., M.Cs.": [
            {"type": "restricted_day", "value": "sabtu"}  # Tidak ada kelas pada hari Sabtu
        ]
    }

# Fungsi untuk mengumpulkan konflik pada jadwal
def collect_conflicts(schedule):
    teacher_intervals = defaultdict(list)
    room_intervals = defaultdict(list)
    conflict_slots = set()
    lecturer_preferences = get_lecturer_preferences()
    preference_conflict_slots = set()
    course_teacher_class = defaultdict(list)
    
    for slot in schedule:
        if not slot['mata_kuliah']:
            continue
        start = time_to_minutes(slot['jam_mulai'])
        end = time_to_minutes(slot['jam_selesai'])
        slot_id = slot['id_slot']
        dosen = str(slot['dosen'])
        hari = slot['hari'].lower()
        
        teacher_intervals[(dosen, hari)].append((start, end, slot_id))
        if slot['metode'] != 'Online':
            room_intervals[(slot['ruang'], hari)].append((start, end, slot_id))
        
        key = (slot['mata_kuliah'], slot['dosen'], slot['kelas'])
        course_teacher_class[key].append(slot)
        
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
                if violated:
                    preference_conflict_slots.add(slot_id)
    
    teacher_conflicts = []
    for key, intervals in teacher_intervals.items():
        conflicts = detect_time_conflicts(intervals)
        teacher_conflicts.extend(conflicts)
        for c in conflicts:
            conflict_slots.update(c)
    
    room_conflicts = []
    for key, intervals in room_intervals.items():
        conflicts = detect_time_conflicts(intervals)
        room_conflicts.extend(conflicts)
        for c in conflicts:
            conflict_slots.update(c)
    
    room_consistency_conflicts = []
    sequence_conflicts = []
    for key, slots in course_teacher_class.items():
        expected_slots = slots[0]['sks']
        days = defaultdict(list)
        for s in slots:
            days[s['hari']].append(s)
        for day, day_slots in days.items():
            if len(day_slots) > 1:
                rooms = {s['ruang'] for s in day_slots}
                if len(rooms) > 1:
                    for s in day_slots:
                        conflict_slots.add(s['id_slot'])
                    room_consistency_conflicts.append({
                        'course_key': key,
                        'slot_ids': [s['id_slot'] for s in day_slots],
                        'hari': day
                    })
                day_slots.sort(key=lambda x: time_to_minutes(x['jam_mulai']))
                for i in range(1, len(day_slots)):
                    curr_end = time_to_minutes(day_slots[i-1]['jam_selesai'])
                    next_start = time_to_minutes(day_slots[i]['jam_mulai'])
                    if curr_end != next_start:
                        conflict_slots.add(day_slots[i-1]['id_slot'])
                        conflict_slots.add(day_slots[i]['id_slot'])
                        sequence_conflicts.append({
                            'course_key': key,
                            'prev_slot': day_slots[i-1]['id_slot'],
                            'next_slot': day_slots[i]['id_slot'],
                            'hari': day
                        })
    
    sks_conflicts = []
    for key, slots in course_teacher_class.items():
        expected_slots = slots[0]['sks']
        if len(slots) != expected_slots:
            for s in slots:
                conflict_slots.add(s['id_slot'])
            sks_conflicts.append({
                'course_key': key,
                'expected': expected_slots,
                'actual': len(slots)
            })
    
    return {
        'conflict_slots': conflict_slots,
        'preference_conflict_slots': preference_conflict_slots,
        'teacher_conflicts': teacher_conflicts,
        'room_conflicts': room_conflicts,
        'room_consistency_conflicts': room_consistency_conflicts,
        'sequence_conflicts': sequence_conflicts,
        'sks_conflicts': sks_conflicts,
    }

# Perhitungan fitness berdasarkan penalty
def calculate_fitness(schedule):
    conflicts = collect_conflicts(schedule)
    penalty = 0.0
    penalty += len(conflicts['teacher_conflicts']) * 1.0
    penalty += len(conflicts['room_conflicts']) * 1.0
    penalty += len(conflicts['room_consistency_conflicts']) * 1.0
    penalty += len(conflicts['sequence_conflicts']) * 1.0
    penalty += len(conflicts['sks_conflicts']) * 1.0
    penalty += len(conflicts['preference_conflict_slots']) * 0.5
    return penalty

# Update jadwal secara block (berdasarkan SKS) untuk memastikan course dengan SKS>1 dipindahkan bersama
def update_schedule(current, alpha, beta, delta, a):
    new_schedule = copy.deepcopy(current)
    i = 0
    n = len(new_schedule)
    while i < n:
        # Jika slot kosong, update secara individual
        if new_schedule[i]['mata_kuliah'] is None:
            r = random.random()
            A = 2 * a * r - a
            if abs(A) < 1:
                new_schedule[i]['mata_kuliah'] = alpha[i]['mata_kuliah']
                new_schedule[i]['dosen'] = alpha[i]['dosen']
                new_schedule[i]['kelas'] = alpha[i]['kelas']
                new_schedule[i]['sks'] = alpha[i]['sks']
                new_schedule[i]['metode'] = alpha[i]['metode']
            i += 1
        else:
            # Ambil panjang block dari nilai SKS
            block_length = new_schedule[i]['sks']
            block_indices = list(range(i, min(i + block_length, n)))
            # Tentukan sumber update untuk seluruh block
            r1, r2, r3 = random.random(), random.random(), random.random()
            A1 = 2 * a * r1 - a
            A2 = 2 * a * r2 - a
            A3 = 2 * a * r3 - a
            if abs(A1) < 1:
                source = alpha
            elif abs(A2) < 1:
                source = beta
            elif abs(A3) < 1:
                source = delta
            else:
                source = None
            if source is not None:
                for idx in block_indices:
                    new_schedule[idx]['mata_kuliah'] = source[idx]['mata_kuliah']
                    new_schedule[idx]['dosen'] = source[idx]['dosen']
                    new_schedule[idx]['kelas'] = source[idx]['kelas']
                    new_schedule[idx]['sks'] = source[idx]['sks']
                    new_schedule[idx]['metode'] = source[idx]['metode']
            i += block_length
    return new_schedule

# Optimasi menggunakan Grey Wolf Optimizer (GWO)
def gwo_optimization(max_iter=50, population_size=10):
    population = [create_random_schedule() for _ in range(population_size)]
    fitnesses = [calculate_fitness(schedule) for schedule in population]
    sorted_pop = sorted(zip(population, fitnesses), key=lambda x: x[1])
    alpha, alpha_fit = sorted_pop[0]
    beta, beta_fit = sorted_pop[1]
    delta, delta_fit = sorted_pop[2]
    
    iterasi = 0
    a = 2
    while iterasi < max_iter:
        a = 2 - (2 * iterasi / max_iter)
        new_population = []
        for schedule in population:
            new_schedule = update_schedule(schedule, alpha, beta, delta, a)
            new_population.append(new_schedule)
        population = new_population
        fitnesses = [calculate_fitness(schedule) for schedule in population]
        sorted_pop = sorted(zip(population, fitnesses), key=lambda x: x[1])
        alpha, alpha_fit = sorted_pop[0]
        beta, beta_fit = sorted_pop[1]
        delta, delta_fit = sorted_pop[2]
        iterasi += 1
        print(f"Iterasi {iterasi} - Best Fitness (Penalty): {alpha_fit}")
    return alpha, alpha_fit

# Pemanggilan utama
if __name__ == "__main__":
    # Optimasi jadwal dengan GWO
    alpha_schedule, best_penalty = gwo_optimization(max_iter=50, population_size=10)
    print("Penalty Terbaik:", best_penalty)
    
    # Hitung total slot yang terisi
    total_terisi = sum(1 for slot in alpha_schedule if slot['mata_kuliah'] is not None)
    print(f"Total slot terisi: {total_terisi}")

    # Mengecek apakah jadwal sudah lengkap berdasarkan total SKS
    # Asumsi merged_df berisi kolom 'sks'
    merged_df = pd.read_csv('data_skripsi_mk_genap.csv')
    total_sks = merged_df['sks'].sum()
    if total_terisi == total_sks:
        print("Jadwal Sudah Lengkap")
    else:
        print("Jadwal Belum Lengkap")
    
    # Simpan jadwal terbaik ke file JSON
    with open('output.json', 'w') as f:
        json.dump(alpha_schedule, f, indent=4)
