import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
import queue

# -----------------------------
# CONFIG
# -----------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

processes = {}
log_files = {
    "Backend": os.path.join(LOG_DIR, "backend.log"),
    "Dashboard": os.path.join(LOG_DIR, "dashboard.log"),
    "CAN Simulator": os.path.join(LOG_DIR, "can.log"),
}

log_queue = queue.Queue()

# -----------------------------
# SAFE UI LOGGING
# -----------------------------
def safe_log(message):
    log_queue.put(message)

def process_log_queue():
    while not log_queue.empty():
        try:
            msg = log_queue.get_nowait()
            log_box.insert(tk.END, msg)
            log_box.see(tk.END)
        except queue.Empty:
            break
    root.after(100, process_log_queue)

# -----------------------------
# START SERVICE
# -----------------------------
def start_service(name, command, log_file):
    if name in processes:
        # Check if actually running
        proc, _ = processes[name]
        if proc.poll() is None:
            safe_log(f"⚠ {name} is already running.\n")
            return

    log = open(log_file, "w", encoding="utf-8")

    # Removed CREATE_NEW_PROCESS_GROUP so Windows associates child trees naturally
    process = subprocess.Popen(
        command,
        stdout=log,
        stderr=log
    )

    processes[name] = (process, log)
    safe_log(f"🚀 {name} started (PID: {process.pid})\n")
    root.after(0, update_status)

# -----------------------------
# START ALL
# -----------------------------
def start_all():
    safe_log("\n🚗 Starting ACIP-X1 Services...\n")

    # -------------------------------------------------------------
    # AUTO-DETECT VIRTUAL ENVIRONMENT EXECUTABLE
    # -------------------------------------------------------------
    # Path to your local script's venv relative or absolute directory
    base_dir = r"c:\Users\tarunbalaji.v\Downloads\proto\ACIP-X1"
    venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")

    # Fallback to standard 'python' if venv file doesn't exist locally
    if not os.path.exists(venv_python):
        safe_log("⚠ Local .venv python not found, falling back to system python.\n")
        venv_python = "python"
    else:
        safe_log(f"⚡ Using Virtual Environment: {venv_python}\n")
    # -------------------------------------------------------------

    start_service(
        "Backend",
        [venv_python, "-m", "uvicorn", "backend.main:app", "--port", "8000"],
        log_files["Backend"]
    )
    time.sleep(2)

    start_service(
        "Dashboard",
        [venv_python, "-m", "streamlit", "run", "dashboard/dashboard_app.py", "--server.port", "8501"],
        log_files["Dashboard"]
    )
    time.sleep(2)

    start_service(
        "CAN Simulator",
        [venv_python, "hardware/can/can_simulator.py"],
        log_files["CAN Simulator"]
    )

    safe_log("✅ All services started inside Virtual Environment!\n")
# -----------------------------
# STOP ALL (BULLETPROOF VERSION)
# -----------------------------
def stop_all():
    safe_log("\n🛑 Stopping all services...\n")

    for name, item in list(processes.items()):
        process, log_handle = item
        try:
            safe_log(f"⚡ Terminating tree for {name} (PID: {process.pid})...\n")
            
            # Force kill the process AND its entire child tree (/T) regardless of poll status
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass

            if log_handle and not log_handle.closed:
                log_handle.close()

            safe_log(f"⛔ {name} stopped.\n")
        except Exception as e:
            safe_log(f"⚠ Error stopping {name}: {e}\n")

    # NUCLEAR OPTION FALLBACK: Clear any leftover orphan Python webservers on our ports
    # This ensures that even if windows detached them, the ports are freed up completely.
    for port in ["8000", "8501"]:
        try:
            # Look up PIDs holding the ports
            output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            for line in output.strip().split("\n"):
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    if pid != "0":
                        subprocess.call(["taskkill", "/F", "/PID", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass # Port already free or no process found

    processes.clear()
    root.after(0, update_status)
    safe_log("✅ All services stopped completely!\n")

# -----------------------------
# STATUS UPDATE
# -----------------------------
def update_status():
    backend_status.set(
        "🟢 Running" if "Backend" in processes and processes["Backend"][0].poll() is None else "🔴 Stopped"
    )
    dashboard_status.set(
        "🟢 Running" if "Dashboard" in processes and processes["Dashboard"][0].poll() is None else "🔴 Stopped"
    )
    can_status.set(
        "🟢 Running" if "CAN Simulator" in processes and processes["CAN Simulator"][0].poll() is None else "🔴 Stopped"
    )

# -----------------------------
# LIVE LOG TAILING
# -----------------------------
def tail_logs():
    positions = {name: 0 for name in log_files}

    while True:
        for name, file in log_files.items():
            if os.path.exists(file):
                try:
                    if os.path.getsize(file) < positions[name]:
                        positions[name] = 0

                    with open(file, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(positions[name])
                        lines = f.readlines()
                        positions[name] = f.tell()

                        for line in lines:
                            safe_log(f"[{name}] {line}")
                except Exception:
                    pass
        time.sleep(0.5)

# -----------------------------
# UI SETUP
# -----------------------------
root = tk.Tk()
root.title("🚗 ACIP-X1 Control Panel")
root.geometry("800x600")
root.configure(bg="#0f172a")

title = tk.Label(root, text="ACIP-X1 Desktop Control Panel", font=("Arial", 18, "bold"), fg="white", bg="#0f172a")
title.pack(pady=10)

status_frame = tk.Frame(root, bg="#0f172a")
status_frame.pack(pady=5)

backend_status = tk.StringVar(value="🔴 Stopped")
dashboard_status = tk.StringVar(value="🔴 Stopped")
can_status = tk.StringVar(value="🔴 Stopped")

tk.Label(status_frame, text="Backend:", fg="white", bg="#0f172a").grid(row=0, column=0)
tk.Label(status_frame, textvariable=backend_status, fg="white", bg="#0f172a").grid(row=0, column=1, padx=10)
tk.Label(status_frame, text="Dashboard:", fg="white", bg="#0f172a").grid(row=0, column=2)
tk.Label(status_frame, textvariable=dashboard_status, fg="white", bg="#0f172a").grid(row=0, column=3, padx=10)
tk.Label(status_frame, text="CAN:", fg="white", bg="#0f172a").grid(row=0, column=4)
tk.Label(status_frame, textvariable=can_status, fg="white", bg="#0f172a").grid(row=0, column=5, padx=10)

btn_frame = tk.Frame(root, bg="#0f172a")
btn_frame.pack(pady=10)

tk.Button(
    btn_frame, text="▶ Start All", width=15, bg="#22c55e", fg="white",
    command=lambda: threading.Thread(target=start_all, daemon=True).start()
).grid(row=0, column=0, padx=10)

tk.Button(
    btn_frame, text="⛔ Stop All", width=15, bg="#ef4444", fg="white",
    command=lambda: threading.Thread(target=stop_all, daemon=True).start()
).grid(row=0, column=1, padx=10)

def on_close():
    threading.Thread(target=lambda: (stop_all(), root.quit()), daemon=True).start()

root.protocol("WM_DELETE_WINDOW", on_close)

tk.Button(btn_frame, text="❌ Exit", width=15, bg="#64748b", fg="white", command=on_close).grid(row=0, column=2, padx=10)

log_box = scrolledtext.ScrolledText(root, width=100, height=25, bg="black", fg="lime")
log_box.pack(pady=10)

root.after(100, process_log_queue)
threading.Thread(target=tail_logs, daemon=True).start()

root.mainloop()