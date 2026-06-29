# Execution Guide

This document explains how to initialize the database and start all required services for the project.

## Prerequisites

* Python 3.10+ installed
* Virtual environment activated
* Required dependencies installed (`pip install -r requirements.txt`)

---

## Step 1: Initialize the Database

Run the following command once before starting the application:

```bash
python -m backend.utils.init_db
```

---

## Step 2: Start the Backend API

Launch the FastAPI backend:

```bash
python -m uvicorn backend.main:app --reload
```

The backend will start in development mode with auto-reload enabled.

---

## Step 3: Start the Streamlit Dashboard

Open a new terminal and run:

```bash
python -m streamlit run dashboard/dashboard_app.py
```

This launches the dashboard interface.

---

## Step 4: Start the CAN Simulator

Open another terminal and run:

```bash
python hardware/can/can_simulator.py
```

This starts the CAN bus simulator for testing and development.

---

## Running All Components

Use separate terminals for each service.

| Terminal   | Command                                                  |
| ---------- | -------------------------------------------------------- |
| Terminal 1 | `python -m backend.utils.init_db` *(Run once if needed)* |
| Terminal 1 | `python -m uvicorn backend.main:app --reload`            |
| Terminal 2 | `python -m streamlit run dashboard/dashboard_app.py`     |
| Terminal 3 | `python hardware/can/can_simulator.py`                   |

## Notes

* Initialize the database only once unless you need to recreate it.
* Keep the backend server running before launching the dashboard.
* Ensure all terminals remain active while using the application.
* If any service stops, restart it using the corresponding command.
