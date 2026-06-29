ACIP-X1
│
├── PROJECT_ROADMAP.md
│
├── docs
│ ├── architecture
│ │ └── Vehicle_Program_Definition.xlsx
│ │
│ ├── requirements
│ ├── design
│ ├── diagrams
│ └── presentations
│
├── data
│ ├── raw
│ │ ├── ECU_Master.xlsx
│ │ ├── Signal_Master.xlsx
│ │ ├── Calibration_Master.xlsx
│ │ ├── DTC_Master.xlsx
│ │ ├── Fault_Master.xlsx
│ │ └── TestCase_Master.xlsx
│ │
│ ├── processed
│ ├── synthetic
│ └── exports
│
├── backend
│ ├── api
│ ├── services
│ ├── models
│ ├── repositories
│ ├── utils
│ └── config
│
├── frontend
│
├── agents
│ ├── requirement_agent
│ ├── calibration_agent
│ ├── root_cause_agent
│ ├── impact_analysis_agent
│ ├── vehicle_health_agent
│ ├── predictive_maintenance_agent
│ ├── insurance_agent
│ ├── digital_twin_agent
│ └── orchestrator
│
├── database
│ ├── schemas
│ ├── migrations
│ └── sqlite
│
├── knowledge_graph
│ ├── nodes
│ ├── edges
│ ├── graph_builder
│ └── graph_queries
│
├── hardware
│ ├── stm32
│ ├── can
│ ├── obd
│ └── sensors
│
├── testing
│ ├── unit_tests
│ ├── integration_tests
│ ├── simulation_tests
│ └── datasets
│
├── notebooks
│
└── deployment
## Project Overview

ACIP-X1 (Automotive Cognitive Intelligence Platform) is an OEM-scale automotive intelligence platform that combines:

- Vehicle Engineering Intelligence
- Root Cause Analysis
- Predictive Maintenance
- Vehicle Health Monitoring
- Digital Twin
- Insurance Automation
- Agentic AI
- Knowledge Graph
- Diagnostics & DTC Analysis
- Calibration Intelligence
- Requirement Traceability

## Architecture Layers

### 1. Vehicle Program Layer
- Vehicle Information
- Vehicle Systems
- Vehicle Functions
- Functional Decomposition
- Requirements
- Requirement Templates
- Entity Relationships

### 2. Engineering Data Layer
- ECU Master
- Signal Master
- Calibration Master
- DTC Master
- Fault Master
- Test Case Master

### 3. Knowledge Graph Layer
- Nodes
- Edges
- Graph Builder
- Graph Queries

### 4. Agentic AI Layer
- Requirement Agent
- Calibration Agent
- Root Cause Agent
- Impact Analysis Agent
- Vehicle Health Agent
- Predictive Maintenance Agent
- Insurance Agent
- Digital Twin Agent
- Agent Orchestrator

### 5. Hardware Layer
- STM32
- CAN
- OBD-II
- Sensors

### 6. Platform Layer
- Backend APIs
- Database
- Frontend Dashboard
- Testing Framework
- Deployment Infrastructure

## Current Progress

### Day 1
- [x] Vehicle Program Definition
- [x] Vehicle Systems
- [x] Vehicle Functions
- [x] Function Decomposition
- [x] Requirement Master
- [x] Requirement Templates
- [x] Entity Relationships

### Day 2
- [x] ECU Master
- [x] Signal Master
- [x] Calibration Master
- [x] DTC Master
- [x] Fault Master
- [ ] Test Case Master
- [ ] Knowledge Graph Foundation

## Vision

Build a next-generation Automotive Cognitive Intelligence Platform capable of connecting:

Vehicle → ECU → Signal → Calibration → Requirement → Test Case → DTC → Fault → Root Cause → Vehicle Health → Insurance → Digital Twin → Agentic AI
