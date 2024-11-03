import subprocess

# List of scripts to run
scripts = ["Hospital.py", "Smartphone.py", "SmartBracelet.py"]

# Launch each script in a separate process
processes = []
for script in scripts:
    print(f"Starting {script}...")
    process = subprocess.Popen(["python", script])
    processes.append(process)

# Wait for all processes to complete
try:
    for process in processes:
        process.wait()
except KeyboardInterrupt:
    print("Terminating all processes...")
    for process in processes:
        process.terminate()

print("All processes terminated.")
