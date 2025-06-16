import time
start_time = time.time()
from process import update_position, create_random_schedule, calculate_fitness, collect_conflicts
from collections import defaultdict
import pandas as pd
from sqlalchemy.orm import Session
from database import get_db
db: Session = next(get_db())

class GreyWolfOptimizer:
    def __init__(self, population_size, max_iterations):
        self.population_size = population_size
        self.max_iterations = max_iterations

    def optimize(self, fitness_function, create_solution_function, collect_conflicts, db: Session, log_callback=None):
        population = [create_solution_function() for _ in range(self.population_size)]
        fitness_values = [fitness_function(schedule) for schedule in population]

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

            print(f"Iterasi {iteration+1}/{self.max_iterations} - Best Fitness: {best_fitness}")
            
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

            end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("Optimasi Selesai!")
        print(f"Best Fitness: {best_fitness}")
        print(f"Total waktu eksekusi: {elapsed_time:.4f} detik")

        return best_solution, best_fitness, elapsed_time

if __name__ == "__main__":
    population_sizes = [5, 10, 15, 20, 25, 30]
    max_iterations_list = [5, 10, 15, 20, 25, 30]
    num_experiments = 1

    experiment_data = []

    for pop_size in population_sizes:
        for max_iter in max_iterations_list:
            for experiment in range(num_experiments):
                gwo = GreyWolfOptimizer(pop_size, max_iter)
                best_schedule, best_fitness, elapsed_time = gwo.optimize(
                    fitness_function=lambda schedule: calculate_fitness(schedule, db),
                    create_solution_function=create_random_schedule, 
                    collect_conflicts=collect_conflicts, db=db
                )
                print(f"Experiment {experiment+1}/{num_experiments} (Population: {pop_size}, Iterations: {max_iter}) - Best Fitness: {best_fitness}")
                experiment_data.append((pop_size, max_iter, elapsed_time))
    
    grouped_data = defaultdict(list)
    for pop_size, max_iter, fitness in experiment_data:
        grouped_data[(pop_size, max_iter)].append(fitness)
    
    columns = []
    
    population_sizes = sorted(set([pop for pop, _, _ in experiment_data]))
    max_iterations_list = sorted(set([it for _, it, _ in experiment_data]))
    
    for pop_size in population_sizes:
        for max_iter in max_iterations_list:
            # Header kolom
            col_header = [f"Individu {pop_size} Iterasi {max_iter}"]
            
            # Data fitness (konversi ke string dengan koma sebagai desimal)
            fitness_values = [str(f) for f in grouped_data[(pop_size, max_iter)]]
            
            # Gabungkan header dan data
            full_column = col_header + fitness_values
            columns.append(full_column)
    
    # 4. Cari panjang kolom terpanjang
    max_length = max(len(col) for col in columns)
    
    # 5. Samakan panjang semua kolom dengan mengisi string kosong
    for col in columns:
        if len(col) < max_length:
            col += [""] * (max_length - len(col))
    
    # 6. Buat DataFrame dan simpan ke Excel
    df = pd.DataFrame({f"Kombinasi {i+1}": col for i, col in enumerate(columns)})
    
    excel_file = "Proses Time Full Terbaru.xlsx"
    df.to_excel(excel_file, index=False, header=False)
    print(f"File Excel berhasil dibuat: {excel_file}")