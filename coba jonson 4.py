import streamlit as st
from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
import collections

st.title("Job Shop Scheduling Solver")

# 1. Input Data di Streamlit
num_jobs = st.number_input("Jumlah Job", min_value=1, value=2)
num_machines = st.number_input("Jumlah Mesin", min_value=1, value=2)

machine_names = []
for i in range(num_machines):
    machine_names.append(st.text_input(f"Nama Mesin {i+1}", value=f"Mesin {i+1}"))

jobs_data = []
for i in range(num_jobs):
    st.subheader(f"Job {i+1}")
    job_name = st.text_input(f"Nama Job ke-{i+1}", key=f"name_{i}")
    job = []
    for j in range(num_machines):
        time = st.number_input(f"Waktu di {machine_names[j]}", min_value=0, key=f"time_{i}_{j}")
        job.append((j, int(time)))
    jobs_data.append({'name': job_name, 'tasks': job})

# 2. Solver (Logic tetap sama)
if st.button("Hitung Jadwal"):
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

    for m_idx in range(num_machines):
        model.add_no_overlap(machine_to_intervals[m_idx])

    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job['tasks']) - 1):
            model.add(all_tasks[job_id, task_id + 1]['start'] >= all_tasks[job_id, task_id]['end'])

    obj_var = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(obj_var, [all_tasks[job_id, len(job['tasks'])-1]['end'] for job_id, job in enumerate(jobs_data)])
    model.minimize(obj_var)
    
    solver = cp_model.CpSolver()
    if solver.solve(model) == cp_model.OPTIMAL:
        st.success(f"Makespan Optimal: {solver.objective_value}")
        
        # 3. Visualisasi untuk Streamlit
        fig, ax = plt.subplots(figsize=(10, 4))
        for m_idx, m_name in enumerate(machine_names):
            for j_id in range(num_jobs):
                for t_id, (m_id, dur) in enumerate(jobs_data[j_id]['tasks']):
                    if m_id == m_idx:
                        s = solver.value(all_tasks[j_id, t_id]['start'])
                        e = solver.value(all_tasks[j_id, t_id]['end'])
                        ax.barh(m_name, e - s, left=s, edgecolor='black', alpha=0.7)
                        ax.text(s + (e-s)/2, m_idx, jobs_data[j_id]['name'], ha='center', va='center')
        
        st.pyplot(fig)
    else:
        st.error("Solusi tidak ditemukan.")
