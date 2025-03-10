import random
import copy
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict

dosen_df = pd.read_csv('data_skripsi_dosen.csv')
mk_genap_df = pd.read_csv('data_skripsi_mk_genap.csv')
data_dosen_df = pd.read_csv('data_skripsi_data_dosen.csv')
hari_df = pd.read_csv('data_skripsi_hari.csv')
ruang_df = pd.read_csv('data_skripsi_ruang.csv')
jam_df = pd.read_csv('data_skripsi_jam.csv')

# Urutkan jam_df sebelum generate slot
jam_df = jam_df.sort_values('id_jam')

merged_df = pd.merge(
    pd.merge(data_dosen_df, dosen_df, on='id_dosen'),
    mk_genap_df, on='id_mk_genap'
)

# Fungsi Bantu
def time_to_minutes(t):
    try:
        dt = datetime.strptime(t, "%H:%M:%S")
    except ValueError:
        dt = datetime.strptime(t, "%H:%M")
    return dt.hour * 60 + dt.minute

# 1. Preprocessing: Membangun struktur slot waktu yang benar
def build_time_slots_from_data(hari_df, jam_df):
    """
    Membangun struktur slot waktu berdasarkan data hari dan jam yang sebenarnya
    
    Args:
        hari_df: DataFrame dengan informasi hari
        jam_df: DataFrame dengan informasi jam (id_jam, jam_awal, jam_akhir)
    
    Returns:
        List of dictionaries, masing-masing mewakili slot waktu
    """
    slots = []
    for _, hari in hari_df.iterrows():
        for _, jam in jam_df.iterrows():
            # Hitung durasi dalam menit
            durasi = time_to_minutes(jam['jam_akhir']) - time_to_minutes(jam['jam_awal'])
            
            slot = {
                'id_hari': hari['id_hari'],
                'nama_hari': hari['nama_hari'],
                'id_jam': jam['id_jam'],
                'jam_awal': jam['jam_awal'],
                'jam_akhir': jam['jam_akhir'],
                'durasi_menit': durasi
            }
            slots.append(slot)
    return slots

# Fungsi untuk membangun slot SKS (1 SKS = 50 menit)
def build_sks_slots(time_slots, sks_values=[1, 2, 3, 4]):
    """
    Membangun slot-slot yang mencukupi untuk berbagai nilai SKS
    Contoh: mata kuliah 2 SKS membutuhkan slot waktu dengan total 100 menit
    
    Args:
        time_slots: Daftar slot waktu dasar
        sks_values: Daftar nilai SKS yang mungkin
    
    Returns:
        Dictionary of lists, key=sks, value=list of valid slot combinations
    """
    sks_slots = {sks: [] for sks in sks_values}
    
    # Kelompokkan slot berdasarkan hari
    slots_by_day = defaultdict(list)
    for i, slot in enumerate(time_slots):
        slots_by_day[slot['id_hari']].append((i, slot))
    
    # Untuk setiap hari, temukan kombinasi slot yang memenuhi kebutuhan SKS
    for hari, slots in slots_by_day.items():
        # Urutkan slot berdasarkan id_jam
        slots.sort(key=lambda x: x[1]['id_jam'])
        
        # Cari kombinasi slot yang berurutan untuk setiap nilai SKS
        for sks in sks_values:
            required_duration = sks * 50  # 1 SKS = 50 menit
            
            for i in range(len(slots)):
                cumulative_duration = 0
                consecutive_slots = []
                
                # Coba tambahkan slot berurutan sampai mencukupi durasi
                for j in range(i, len(slots)):
                    # Pastikan benar-benar berurutan (id_jam berurutan)
                    if j > i and slots[j][1]['id_jam'] != slots[j-1][1]['id_jam'] + 1:
                        break
                    
                    slot_idx, slot_data = slots[j]
                    consecutive_slots.append(slot_idx)
                    cumulative_duration += slot_data['durasi_menit']
                    
                    # Jika sudah mencukupi durasi yang dibutuhkan
                    if cumulative_duration >= required_duration:
                        sks_slots[sks].append(consecutive_slots)
                        break
    
    return sks_slots

# Modifikasi ScheduleSolution untuk menggunakan slot SKS
class ScheduleSolution:
    """Representasi solusi penjadwalan sebagai "serigala" dalam GWO"""
    
    def __init__(self, courses, time_slots, sks_slots, rooms, random_init=True):
        """
        Inisialisasi solusi penjadwalan
        
        Args:
            courses (DataFrame): Data mata kuliah yang akan dijadwalkan
            time_slots (list): Daftar slot waktu dasar
            sks_slots (dict): Dictionary slot waktu berdasarkan SKS
            rooms (DataFrame): Data ruangan yang tersedia
            random_init (bool): Apakah inisialisasi secara acak
        """
        self.courses = courses
        self.time_slots = time_slots
        self.sks_slots = sks_slots
        self.rooms = rooms
        
        # Schedule sebagai dict: key = id_course, value = (list_of_time_slot_idx, id_room)
        self.schedule = {}
        
        if random_init:
            self.initialize_random()
        
        self.fitness_value = None
    
    def initialize_random(self):
        """Inisialisasi solusi secara acak dengan memperhatikan SKS"""
        for _, course in self.courses.iterrows():
            course_id = course['id_mk_genap']
            sks = course['sks']
            
            # Jika tidak ada slot yang sesuai untuk SKS ini, lewati
            if sks not in self.sks_slots or not self.sks_slots[sks]:
                continue
            
            # Pilih kombinasi slot waktu secara acak berdasarkan SKS
            slot_combination_idx = random.randint(0, len(self.sks_slots[sks]) - 1)
            time_slot_indices = self.sks_slots[sks][slot_combination_idx]
            
            # Pilih ruangan secara acak
            room_idx = random.randint(0, len(self.rooms) - 1)
            room_id = self.rooms.iloc[room_idx]['id_ruang']
            
            # Simpan ke dalam jadwal
            self.schedule[course_id] = (time_slot_indices, room_id)
    
    def calculate_fitness(self):
        """
        Menghitung nilai fitness dengan mempertimbangkan:
        - Konflik dosen (tidak bisa mengajar di slot waktu yang sama)
        - Konflik ruangan (tidak bisa digunakan oleh lebih dari satu kelas pada slot yang sama)
        - Kesesuaian kapasitas ruangan (jika data tersedia)
        - Distribusi beban dosen (opsional)
        """
        if self.fitness_value is not None:
            return self.fitness_value
        
        penalty = 0
        
        # Track slot waktu yang digunakan oleh setiap dosen
        dosen_occupied_slots = defaultdict(set)
        
        # Track slot waktu yang digunakan di setiap ruangan
        room_occupied_slots = defaultdict(set)
        
        for course_id, (time_slot_indices, room_id) in self.schedule.items():
            # Dapatkan informasi course
            course_info = self.courses[self.courses['id_mk_genap'] == course_id].iloc[0]
            dosen_id = course_info['id_dosen']
            
            # Periksa konflik dosen
            for slot_idx in time_slot_indices:
                if slot_idx in dosen_occupied_slots[dosen_id]:
                    penalty += 100  # Penalti berat untuk konflik dosen
                dosen_occupied_slots[dosen_id].add(slot_idx)
                
                # Periksa konflik ruangan
                room_slot_key = (room_id, slot_idx)
                if room_slot_key in room_occupied_slots:
                    penalty += 100  # Penalti berat untuk konflik ruangan
                room_occupied_slots[room_slot_key].add(course_id)
            
            # Penalti kapasitas ruangan (jika data tersedia)
            if 'kapasitas' in self.rooms.columns and 'jumlah_peserta' in course_info:
                room_capacity = self.rooms[self.rooms['id_ruang'] == room_id].iloc[0]['kapasitas']
                if course_info['jumlah_peserta'] > room_capacity:
                    penalty += 10 * (course_info['jumlah_peserta'] - room_capacity)  # Penalti proporsional
        
        # Tambahan: penalti untuk distribusi jadwal yang tidak merata (opsional)
        # Misalnya: jika ada dosen dengan jadwal terlalu padat pada satu hari
        
        self.fitness_value = penalty
        return penalty
    
    def get_position(self):
        """Konversi jadwal ke representasi array untuk GWO"""
        # Kita perlu representasi posisi yang konsisten untuk algoritma GWO
        num_courses = len(self.courses)
        max_slots_per_course = 4  # Asumsi maksimum 4 SKS
        
        # Format: [course1_start_slot, course1_room, course2_start_slot, course2_room, ...]
        position = np.zeros(num_courses * 2)
        
        for i, course_id in enumerate(sorted(self.courses['id_mk_genap'])):
            if course_id in self.schedule:
                time_slot_indices, room_id = self.schedule[course_id]
                # Kita simpan indeks slot awal sebagai representasi
                if time_slot_indices:
                    position[i*2] = time_slot_indices[0]
                    position[i*2 + 1] = room_id
            else:
                position[i*2] = -1
                position[i*2 + 1] = -1
        
        return position
    
    def set_position(self, position):
        """Perbarui jadwal dari representasi array GWO"""
        position = np.round(position).astype(int)
        
        self.schedule = {}
        course_ids = sorted(self.courses['id_mk_genap'])
        
        for i, course_id in enumerate(course_ids):
            if i*2 + 1 < len(position):
                start_slot_idx = position[i*2]
                room_id = position[i*2 + 1]
                
                if start_slot_idx >= 0 and room_id >= 0:
                    # Dapatkan informasi SKS
                    course_info = self.courses[self.courses['id_mk_genap'] == course_id].iloc[0]
                    sks = course_info['sks']
                    
                    # Temukan slot combination yang dimulai dari start_slot_idx
                    valid_combination = None
                    if sks in self.sks_slots:
                        for combination in self.sks_slots[sks]:
                            if combination and combination[0] == start_slot_idx:
                                valid_combination = combination
                                break
                    
                    if valid_combination:
                        self.schedule[course_id] = (valid_combination, room_id)
        
        # Reset fitness karena jadwal berubah
        self.fitness_value = None

# Modifikasi fungsi grey_wolf_optimizer
def grey_wolf_optimizer(courses, time_slots, sks_slots, rooms, num_wolves=10, max_iter=100):
    """
    Implementasi Grey Wolf Optimizer untuk penjadwalan dengan mempertimbangkan SKS
    """
    # Inisialisasi populasi serigala
    wolves = [ScheduleSolution(courses, time_slots, sks_slots, rooms) for _ in range(num_wolves)]
    
    # Evaluasi awal
    for wolf in wolves:
        wolf.calculate_fitness()
    
    # Urutkan serigala berdasarkan fitness
    wolves.sort(key=lambda w: w.calculate_fitness())
    
    # Tetapkan Alpha, Beta, dan Delta
    alpha = copy.deepcopy(wolves[0])
    beta = copy.deepcopy(wolves[1]) if num_wolves > 1 else alpha
    delta = copy.deepcopy(wolves[2]) if num_wolves > 2 else beta
    
    # Iterasi GWO
    for iter_no in range(max_iter):
        # Perbarui parameter a dari 2 ke 0
        a = 2 - iter_no * (2 / max_iter)
        
        # Perbarui posisi setiap serigala
        for i in range(num_wolves):
            # Perbarui posisi berdasarkan Alpha, Beta, dan Delta
            current_pos = wolves[i].get_position()
            alpha_pos = alpha.get_position()
            beta_pos = beta.get_position()
            delta_pos = delta.get_position()
            
            # Implementasi formula GWO untuk memperbarui posisi
            new_pos = np.zeros_like(current_pos)
            
            for j in range(len(current_pos)):
                # Koefisien Alpha
                r1, r2 = np.random.random(2)
                A1 = 2 * a * r1 - a
                C1 = 2 * r2
                D_alpha = abs(C1 * alpha_pos[j] - current_pos[j])
                X1 = alpha_pos[j] - A1 * D_alpha
                
                # Koefisien Beta
                r1, r2 = np.random.random(2)
                A2 = 2 * a * r1 - a
                C2 = 2 * r2
                D_beta = abs(C2 * beta_pos[j] - current_pos[j])
                X2 = beta_pos[j] - A2 * D_beta
                
                # Koefisien Delta
                r1, r2 = np.random.random(2)
                A3 = 2 * a * r1 - a
                C3 = 2 * r2
                D_delta = abs(C3 * delta_pos[j] - current_pos[j])
                X3 = delta_pos[j] - A3 * D_delta
                
                # Posisi baru: rata-rata dari ketiga posisi
                new_pos[j] = (X1 + X2 + X3) / 3
            
            # Perbarui posisi serigala
            wolves[i].set_position(new_pos)
        
        # Evaluasi fitness
        for wolf in wolves:
            wolf.calculate_fitness()
        
        # Urutkan serigala
        wolves.sort(key=lambda w: w.calculate_fitness())
        
        # Perbarui Alpha, Beta, dan Delta
        if wolves[0].calculate_fitness() < alpha.calculate_fitness():
            alpha = copy.deepcopy(wolves[0])
        
        if num_wolves > 1 and wolves[1].calculate_fitness() < beta.calculate_fitness():
            beta = copy.deepcopy(wolves[1])
        
        if num_wolves > 2 and wolves[2].calculate_fitness() < delta.calculate_fitness():
            delta = copy.deepcopy(wolves[2])
        
        # Cetak progress
        print(f"Iterasi {iter_no+1}/{max_iter}, Alpha fitness: {alpha.calculate_fitness()}")
    
    return alpha

# Modifikasi fungsi display_schedule untuk menampilkan jadwal dengan slot berurutan
def display_schedule(solution, courses, time_slots, rooms):
    """Tampilkan jadwal dalam format yang lebih informatif"""
    schedule_data = []
    
    for course_id, (time_slot_indices, room_id) in solution.schedule.items():
        # Dapatkan informasi mata kuliah
        course_info = courses[courses['id_mk_genap'] == course_id].iloc[0]
        
        # Dapatkan informasi ruangan
        room_info = rooms[rooms['id_ruang'] == room_id].iloc[0]
        
        # Informasi slot waktu
        if time_slot_indices:
            # Ambil informasi slot pertama dan terakhir
            first_slot = time_slots[time_slot_indices[0]]
            last_slot = time_slots[time_slot_indices[-1]]
            
            schedule_data.append({
                'Mata Kuliah': course_info['nama_mk_genap'],
                'SKS': course_info['sks'],
                'Dosen': course_info['nama_dosen'],
                'Hari': first_slot['nama_hari'],
                'Jam Mulai': first_slot['jam_awal'],
                'Jam Selesai': last_slot['jam_akhir'],
                'Ruang': room_info['nama_ruang'],
                'Slot IDs': ','.join(map(str, time_slot_indices))
            })
    
    # Buat DataFrame dan urutkan
    schedule_df = pd.DataFrame(schedule_data)
    if not schedule_df.empty:
        schedule_df = schedule_df.sort_values(['Hari', 'Jam Mulai', 'Ruang'])
    
    return schedule_df

# Fungsi utama yang menggunakan struktur jam dari data
def run_scheduling_with_real_data():
    """Menjalankan penjadwalan dengan data jam yang sebenarnya"""
    # 1. Preprocessing
    print("1. Preprocessing...")
    time_slots = build_time_slots_from_data(hari_df, jam_df)
    sks_slots = build_sks_slots(time_slots)
    
    print(f"Total slot waktu dasar: {len(time_slots)}")
    for sks, slots in sks_slots.items():
        print(f"Kombinasi slot untuk {sks} SKS: {len(slots)}")
    
    # 2. Menjalankan GWO
    print("\n2. Menjalankan Grey Wolf Optimizer...")
    best_solution = grey_wolf_optimizer(
        merged_df, time_slots, sks_slots, ruang_df, 
        num_wolves=20, max_iter=50
    )
    
    # 3. Menampilkan hasil
    print("\n3. Menampilkan hasil penjadwalan...")
    schedule = display_schedule(best_solution, merged_df, time_slots, ruang_df)
    print("\nJadwal Optimal:")
    print(schedule)
    
    # Evaluasi hasil
    fitness = best_solution.calculate_fitness()
    print(f"\nNilai Fitness: {fitness}")
    if fitness == 0:
        print("Jadwal optimal tanpa konflik!")
    else:
        print("Jadwal memiliki beberapa konflik atau kendala yang tidak terpenuhi.")
    
    # Simpan hasil
    schedule.to_csv('jadwal_hasil_optimasi.csv', index=False)
    print("Jadwal berhasil disimpan ke 'jadwal_hasil_optimasi.csv'")
    
    return best_solution, schedule

# Jalankan program
if __name__ == "__main__":
    best_solution, schedule = run_scheduling_with_real_data()