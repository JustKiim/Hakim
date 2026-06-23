from ortools.sat.python import cp_model
import collections
import matplotlib.pyplot as plt
import pandas as pd

def solve_and_visualize():
    # 1. Input Data
    try:
        num_jobs = int(input("Jumlah job: "))
        num_machines = int(input("Jumlah mesin: "))
        machine_names = [input(f"Nama Mesin {i+1}: ") for i in range(num_machines)]
    except ValueError:
        print("Input harus angka!")
        return

    jobs_data = []
    for i in range(num_jobs):
        job_name = input(f"\nNama Job ke-{i+1}: ")
        job = []
        for j in range(num_machines):
            time = int(input(f"  Waktu proses di {machine_names[j]}: "))
            job.append((j, time))
        jobs_data.append({'name': job_name, 'tasks': job})

    # 2. Model CP
    model = cp_model.CpModel()
    horizon = sum(task[1] for job in jobs_data for task in job['tasks'])
    all_tasks = {}
    machine_to_intervals = collections.defaultdict(list)
    
    for job_id, job in enumerate(jobs_data):
        for task_id, (machine, duration) in enumerate(job['tasks']):
            start = model.new_int_var(0, horizon, f"s_{job_id}_{task_id}")
            end = model.new_int_var(0, horizon, f"e_{job_id}_{task_id}")
            interval = model.new_interval_var(start, duration, end, f"i_{job_id}_{task_id}")
            all_tasks[job_id, task_id] = {'start': start, 'end': end, 'dur': duration, 'name': job['name']}
            machine_to_intervals[machine].append(interval)

    for machine in range(num_machines):
        model.add_no_overlap(machine_to_intervals[machine])

    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job['tasks']) - 1):
            model.add(all_tasks[job_id, task_id + 1]['start'] >= all_tasks[job_id, task_id]['end'])

    obj_var = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(obj_var, [all_tasks[job_id, len(job['tasks'])-1]['end'] for job_id, job in enumerate(jobs_data)])
    model.minimize(obj_var)
    
    # 3. Solver & Visualisasi
    solver = cp_model.CpSolver()
    if solver.solve(model) == cp_model.OPTIMAL:
        print(f"\n--- Makespan Optimal: {solver.objective_value} ---")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        all_times = set()
        
        for m_idx, m_name in enumerate(machine_names):
            tasks_on_m = []
            for j_id in range(num_jobs):
                for t_id, (m_id, dur) in enumerate(jobs_data[j_id]['tasks']):
                    if m_id == m_idx:
                        s = solver.value(all_tasks[j_id, t_id]['start'])
                        e = solver.value(all_tasks[j_id, t_id]['end'])
                        tasks_on_m.append({'start': s, 'end': e, 'name': jobs_data[j_id]['name']})
                        all_times.update([s, e])
            
            tasks_on_m.sort(key=lambda x: x['start'])
            curr = 0
            for t in tasks_on_m:
                if t['start'] > curr:
                    ax.barh(m_name, t['start'] - curr, left=curr, color='lightgrey', hatch='//', edgecolor='grey')
                ax.barh(m_name, t['end'] - t['start'], left=t['start'], color='skyblue', edgecolor='black')
                ax.text(t['start'] + (t['end']-t['start'])/2, m_idx, t['name'], ha='center', va='center')
                curr = t['end']
        
        ax.set_xticks(sorted(list(all_times)))
        ax.set_title(f"Gantt Chart Optimal (Makespan: {solver.objective_value})")
        plt.tight_layout()
        plt.show()
    else:
        print("Solusi tidak ditemukan.")

if __name__ == "__main__":
    solve_and_visualize()
