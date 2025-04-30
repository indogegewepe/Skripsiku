from processCopy import *

if __name__ == "__main__":
    population_sizes = [5, 30]
    max_iterations_list = [5, 30]
    num_experiments = 30

    experiment_data = []

    for pop_size in population_sizes:
        for max_iter in max_iterations_list:
            for experiment in range(num_experiments):
                gwo = GreyWolfOptimizer(pop_size, max_iter)
                best_schedule, best_fitness = gwo.optimize(
                    fitness_function=lambda schedule: calculate_fitness(schedule, db),
                    create_solution_function=create_random_schedule, 
                    collect_conflicts=collect_conflicts, db=db
                )
                print(f"Experiment {experiment+1}/{num_experiments} (Population: {pop_size}, Iterations: {max_iter}) - Best Fitness: {best_fitness}")
                experiment_data.append((pop_size, max_iter, best_fitness))
    
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
    
    excel_file = "revisi new hasil grafik proses copy.xlsx"
    df.to_excel(excel_file, index=False, header=False)
    print(f"File Excel berhasil dibuat: {excel_file}")