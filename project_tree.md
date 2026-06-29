# Project Folder Structure

This document explains the purpose of each folder and important files in the project.

---

# Root Directory

```
Project/
```

Contains the complete Automotive AI Copilot platform including backend services, AI agents, dashboard, hardware simulation, knowledge graph, datasets, and documentation.

---

# Top-Level Folders

## 📁 agents

Contains all AI agents responsible for performing intelligent automotive engineering tasks.

### Subfolders

* **calibration_agent/**

  * Handles calibration validation and parameter analysis.

* **digital_twin_agent/**

  * Simulates vehicle digital twin behavior.

* **impact_analysis_agent/**

  * Predicts the impact of engineering changes.

* **insurance_agent/**

  * Insurance claim intelligence.

* **orchestrator/**

  * Coordinates communication between multiple AI agents.

* **predictive_maintenance_agent/**

  * Predicts upcoming failures using vehicle data.

* **requirement_agent/**

  * Requirement parsing, validation, traceability, testcase generation, and engineering intelligence.

* **root_cause_agent/**

  * Performs diagnostic reasoning to identify root causes.

* **vehicle_health_agent/**

  * Calculates overall vehicle health.

---

## 📁 backend

Main FastAPI backend application.

### api/

REST API endpoints.

Example:

* Vehicle APIs
* Fault APIs
* CAN APIs
* ECU APIs
* Dashboard APIs
* Requirement APIs

### config/

Configuration files.

### models/

SQLAlchemy database models.

### repositories/

Database CRUD layer.

### schemas/

Pydantic request/response models.

### services/

Business logic.

Examples:

* AI Services
* Dashboard Services
* CAN Services
* Vehicle Services
* Breakdown Services
* Insurance Services

### utils/

Utility scripts.

Includes:

* Database initialization
* Data seeding
* Data migration
* Testing scripts
* Validation utilities

### main.py

FastAPI application entry point.

---

## 📁 dashboard

Streamlit dashboard.

Contains:

* Dashboard application
* Exported reports
* Processed datasets
* Raw datasets
* Synthetic datasets

---

## 📁 data

Master engineering datasets.

Contains Excel master files such as:

* Calibration Master
* ECU Master
* DTC Master
* Fault Master
* Signal Master
* TestCase Master

---

## 📁 database

Database resources.

Contains:

* SQLite database
* Database schemas
* Migrations

---

## 📁 deployment

Deployment resources.

May include:

* Docker files
* Kubernetes
* Deployment scripts
* CI/CD configuration

---

## 📁 docs

Project documentation.

Includes:

* Architecture documents
* Design documents
* Diagrams
* Presentations
* Requirements

---

## 📁 frontend

Frontend web application.

Contains HTML pages and future UI assets.

---

## 📁 hardware

Vehicle hardware simulation.

### can/

CAN communication modules.

### obd/

OBD interfaces.

### sensors/

Sensor simulation.

### stm32/

STM32 firmware support.

Contains:

* CAN simulator
* Embedded utilities

---

## 📁 knowledge_graph

Knowledge Graph implementation.

### edges/

Relationship CSV files.

Examples:

* ECU → Signal
* DTC → Fault
* Requirement → Testcase
* Fault → Root Cause

### nodes/

Knowledge Graph node definitions.

Examples:

* Vehicle
* ECU
* Signal
* DTC
* Calibration
* Requirement
* Testcase

### graph_builder/

Graph construction engine.

### graph_queries/

Knowledge Graph query engine.

---

## 📁 notebooks

Jupyter notebooks used for:

* Experiments
* Model evaluation
* Data analysis

---

## 📁 testing

Project testing.

### datasets/

Testing datasets.

### integration_tests/

Integration testing.

### simulation_tests/

Simulation testing.

### unit_tests/

Unit testing.

---

## 📁 uploads

Stores uploaded files from users.

Examples:

* Requirement documents
* CAN logs
* Calibration files
* Reports

---

# Important Root Files

## README.md

Project overview and setup instructions.

---

## requirements.txt

Python dependencies.

Install using:

```bash
pip install -r requirements.txt
```

---

## execution.md

Instructions to initialize the database and start all project services.

---

## folder_struct.md

Documentation describing the project folder structure.

---

## PROJECT_ROADMAP.md

Development roadmap and planned milestones.

---

## project_tree.md

Complete project directory tree.

---

## backendtree.md

Detailed backend folder structure.

---

## endpoints.txt

List of backend REST API endpoints.

---

## .env

Environment variables.

Examples:

* API Keys
* Database URLs
* Configuration settings

---

## seed_new_calibrations.py

Script to insert additional calibration data into the database.

---

## old.db / temp.db

Temporary or backup SQLite databases used during development.

---

# Overall Architecture

```
                 Frontend
                     │
                     ▼
              FastAPI Backend
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   AI Agents     Services     Database
        │            │            │
        └────────────┼────────────┘
                     ▼
            Knowledge Graph
                     │
                     ▼
             Hardware Simulator
                     │
                     ▼
           Streamlit Dashboard
```

This structure follows a modular architecture where AI agents, backend services, hardware simulation, the knowledge graph, and the dashboard are separated into independent components, making the project easier to maintain, extend, and test.
