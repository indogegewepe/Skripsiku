from process import *
from collections import defaultdict
import pandas as pd
import asyncio

if __name__ == "__main__":
    population_sizes = [5, 10, 15, 20, 25, 30]
    total_iterations = 30
    step = 5
    checkpoints = list(range(step, total_iterations + 1, step))  # [5, 10, 15, 20, 25, 30]
    num_experiments = 30

    experiment_data = defaultdict(list)  # key: (pop_size, iter), value: list of fitness

    for pop_size in population_sizes:
        for experiment in range(num_experiments):
            gwo = GreyWolfOptimizer(pop_size, total_iterations)
            best_schedule, best_fitness, tracked_fitnesses = asyncio.run(gwo.optimize(
                fitness_function=lambda schedule: calculate_fitness(schedule, db),
                create_solution_function=create_random_schedule,
                collect_conflicts=collect_conflicts,
                db=db,
                log_callback=None
            ))

            for i, fitness in zip(checkpoints, tracked_fitnesses):
                experiment_data[(pop_size, i)].append(fitness)

            print(f"Populasi {pop_size}, Eksperimen {experiment+1}/{num_experiments} selesai")

    # Susun kolom Excel
    columns = []
    for pop_size in population_sizes:
        for iter_checkpoint in checkpoints:
            header = [f"Populasi {pop_size} - Iterasi {iter_checkpoint}"]
            fitness_list = [str(f) for f in experiment_data[(pop_size, iter_checkpoint)]]
            full_col = header + fitness_list
            columns.append(full_col)

    # Samakan panjang kolom
    max_length = max(len(col) for col in columns)
    for col in columns:
        if len(col) < max_length:
            col += [""] * (max_length - len(col))

    df = pd.DataFrame({f"Kombinasi {i+1}": col for i, col in enumerate(columns)})
    df.to_excel("Fitness per Iterasi.xlsx", index=False, header=False)
    print("File Excel berhasil dibuat: Fitness per Iterasi.xlsx")