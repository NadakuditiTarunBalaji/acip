# 🚗 ACIP-X1 API (Automotive Cognitive Intelligence Platform)

**Version:** 1.0.0  
**Base URL:** http://localhost:8000  
**OpenAPI:** http://localhost:8000/openapi.json  
**Docs:** http://localhost:8000/docs  

---

## 📌 Summary

ACIP-X1 is a next-generation **Automotive Cognitive Intelligence Platform** designed to manage:

- Vehicle ECUs, signals, calibrations, and diagnostics
- Live CAN bus telemetry and predictive insights
- Faults, DTCs, and AI-driven diagnostics
- Emergency crash detection and breakdown assistance
- Engineering lifecycle tools (traceability, safety, test generation)
- Knowledge graph for automotive intelligence
- AI assistant for engineers and in-vehicle personality systems
- Resale value optimization and insurance tracking

It acts as a **central nervous system for connected vehicles**, combining real-time data ingestion, AI reasoning, and engineering-grade traceability.

---

# 🧠 Core Modules

---

## 📋 Requirements Management

- GET    http://localhost:8000/api/requirements/
- POST   http://localhost:8000/api/requirements/
- GET    http://localhost:8000/api/requirements/{req_id}
- PUT    http://localhost:8000/api/requirements/{req_id}
- DELETE http://localhost:8000/api/requirements/{req_id}

---

## ⚙️ ECUs (Electronic Control Units)

- GET    http://localhost:8000/api/ecus/
- POST   http://localhost:8000/api/ecus/
- GET    http://localhost:8000/api/ecus/{ecu_id}
- PUT    http://localhost:8000/api/ecus/{ecu_id}
- DELETE http://localhost:8000/api/ecus/{ecu_id}

---

## 📡 Signals

- GET    http://localhost:8000/api/signals/
- POST   http://localhost:8000/api/signals/
- GET    http://localhost:8000/api/signals/{signal_id}
- PUT    http://localhost:8000/api/signals/{signal_id}
- DELETE http://localhost:8000/api/signals/{signal_id}

---

## 🔧 Calibrations

- GET    http://localhost:8000/api/calibrations/
- POST   http://localhost:8000/api/calibrations/
- GET    http://localhost:8000/api/calibrations/{cal_id}
- PUT    http://localhost:8000/api/calibrations/{cal_id}
- DELETE http://localhost:8000/api/calibrations/{cal_id}

---

## 🚨 Fault Management

- GET    http://localhost:8000/api/faults/
- POST   http://localhost:8000/api/faults/
- GET    http://localhost:8000/api/faults/{fault_id}
- PUT    http://localhost:8000/api/faults/{fault_id}
- DELETE http://localhost:8000/api/faults/{fault_id}

---

## 🧾 DTC (Diagnostic Trouble Codes)

- GET    http://localhost:8000/api/dtcs/
- POST   http://localhost:8000/api/dtcs/
- GET    http://localhost:8000/api/dtcs/{dtc_id}
- PUT    http://localhost:8000/api/dtcs/{dtc_id}
- DELETE http://localhost:8000/api/dtcs/{dtc_id}

---

## 🚘 Vehicle Data

- GET    http://localhost:8000/api/vehicle-data/
- POST   http://localhost:8000/api/vehicle-data/
- PUT    http://localhost:8000/api/vehicle-data/{vehicle_id}
- DELETE http://localhost:8000/api/vehicle-data/{vehicle_id}

---

## 📊 Vehicle Telemetry (Live CAN Data)

- POST   http://localhost:8000/api/telemetry/
- GET    http://localhost:8000/api/telemetry/latest/{vehicle_id}
- GET    http://localhost:8000/api/telemetry/history/{vehicle_id}
- POST   http://localhost:8000/api/telemetry/destination
- GET    http://localhost:8000/api/telemetry/destination/{vehicle_id}
- DELETE http://localhost:8000/api/telemetry/destination/{vehicle_id}
- PATCH  http://localhost:8000/api/telemetry/destination/{vehicle_id}/arrived

---

## 🧾 Insurance

- GET    http://localhost:8000/api/insurance/
- POST   http://localhost:8000/api/insurance/
- PUT    http://localhost:8000/api/insurance/{claim_id}
- DELETE http://localhost:8000/api/insurance/{claim_id}

---

## 🧪 Test Management

- GET    http://localhost:8000/api/testcases/
- POST   http://localhost:8000/api/testcases/
- GET    http://localhost:8000/api/testcases/{tc_id}
- PUT    http://localhost:8000/api/testcases/{tc_id}
- DELETE http://localhost:8000/api/testcases/{tc_id}

---

## 📡 CAN Bus

- POST   http://localhost:8000/api/can/frame
- GET    http://localhost:8000/api/can/frames/{vehicle_id}
- GET    http://localhost:8000/api/can/latest/{vehicle_id}

---

## 📊 Dashboard & Insights

- GET http://localhost:8000/api/dashboard/summary
- GET http://localhost:8000/api/dashboard/diagnostics
- GET http://localhost:8000/api/dashboard/invisible-mechanic
- GET http://localhost:8000/api/dashboard/predictive-alerts
- GET http://localhost:8000/api/dashboard/health-trend
- GET http://localhost:8000/api/dashboard/active-faults
- GET http://localhost:8000/api/dashboard/active-dtcs
- GET http://localhost:8000/api/dashboard/calibration-limits

---

## 🤖 AI Diagnostics

- POST http://localhost:8000/api/ai/diagnose
- GET  http://localhost:8000/api/ai/analyze-dtc/{dtc_id}

---

## 🚑 Emergency System (Crash Detection)

- GET    http://localhost:8000/api/emergency/contacts/{vehicle_id}
- POST   http://localhost:8000/api/emergency/contacts
- DELETE http://localhost:8000/api/emergency/contacts/{contact_id}
- GET    http://localhost:8000/api/emergency/nearby-devices
- GET    http://localhost:8000/api/emergency/accidents/{vehicle_id}
- PATCH  http://localhost:8000/api/emergency/accidents/{accident_id}/resolve
- POST   http://localhost:8000/api/emergency/demo-trigger/{vehicle_id}

---

## 🛠 Breakdown Assistance AI

- GET    http://localhost:8000/api/breakdown/history/{vehicle_id}
- PATCH  http://localhost:8000/api/breakdown/resolve/{breakdown_id}
- POST   http://localhost:8000/api/breakdown/check/{vehicle_id}
- GET    http://localhost:8000/api/breakdown/chat/{breakdown_id}
- POST   http://localhost:8000/api/breakdown/chat/{breakdown_id}

---

## 🗣 AI Personality & Voice Assistant

- GET    http://localhost:8000/api/personality/greeting/{vehicle_id}
- GET    http://localhost:8000/api/personality/chat/{vehicle_id}
- POST   http://localhost:8000/api/personality/chat/{vehicle_id}
- DELETE http://localhost:8000/api/personality/chat/{vehicle_id}
- GET    http://localhost:8000/api/personality/voice/{vehicle_id}
- POST   http://localhost:8000/api/personality/voice/{vehicle_id}
- DELETE http://localhost:8000/api/personality/voice/{vehicle_id}

---

## 💰 Resale Value System

- GET  http://localhost:8000/api/resale/estimate/{vehicle_id}
- POST http://localhost:8000/api/resale/base-price/{vehicle_id}
- GET  http://localhost:8000/api/resale/certificate/{vehicle_id}

---

## 👨‍💻 Engineer AI Chat

- POST   http://localhost:8000/api/engineer-chat/ask/{session_id}
- DELETE http://localhost:8000/api/engineer-chat/reset/{session_id}

---

## 🧠 Knowledge Graph

- GET http://localhost:8000/api/kg/summary
- GET http://localhost:8000/api/kg/search
- GET http://localhost:8000/api/kg/fault/{fault_id}
- GET http://localhost:8000/api/kg/dtc/{dtc_id}
- GET http://localhost:8000/api/kg/signal/{signal_id}
- GET http://localhost:8000/api/kg/requirement/{req_id}/trace
- GET http://localhost:8000/api/kg/vehicle/{vehicle_id}/chain
- GET http://localhost:8000/api/kg/requirements/gaps
- GET http://localhost:8000/api/kg/faults/all

---

## 🏗 Engineering Intelligence Suite

### 📥 Requirements Parsing
- POST http://localhost:8000/api/engineering/requirements/parse/file
- POST http://localhost:8000/api/engineering/requirements/parse/text
- GET  http://localhost:8000/api/engineering/requirements/parse/demo
- GET  http://localhost:8000/api/engineering/requirements/stats

### 🔗 Traceability
- GET http://localhost:8000/api/engineering/traceability/matrix
- GET http://localhost:8000/api/engineering/traceability/matrix/flat
- GET http://localhost:8000/api/engineering/traceability/requirement/{req_id}
- GET http://localhost:8000/api/engineering/traceability/summary
- GET http://localhost:8000/api/engineering/traceability/gaps
- GET http://localhost:8000/api/engineering/traceability/export/csv

### ⚠️ Analysis Engine
- GET http://localhost:8000/api/engineering/analysis/full-report
- GET http://localhost:8000/api/engineering/analysis/gaps
- GET http://localhost:8000/api/engineering/analysis/conflicts
- GET http://localhost:8000/api/engineering/analysis/orphans
- GET http://localhost:8000/api/engineering/analysis/summary

### 🔮 Prediction Engine
- GET http://localhost:8000/api/engineering/predict/all
- GET http://localhost:8000/api/engineering/predict/summary
- GET http://localhost:8000/api/engineering/predict/requirement/{req_id}
- GET http://localhost:8000/api/engineering/predict/system/{system}
- GET http://localhost:8000/api/engineering/predict/failures-only
- GET http://localhost:8000/api/engineering/predict/warnings-only

### 🧍 Human Mistake Detection
- GET http://localhost:8000/api/engineering/mistakes/all
- GET http://localhost:8000/api/engineering/mistakes/summary
- GET http://localhost:8000/api/engineering/mistakes/team/{team_name}
- GET http://localhost:8000/api/engineering/mistakes/critical-only
- GET http://localhost:8000/api/engineering/mistakes/by-severity/{severity}

### 🧪 Safety & Test Generation
- POST http://localhost:8000/api/engineering/generate-testcase
- GET  http://localhost:8000/api/engineering/generate-testcase/{req_id}
- GET  http://localhost:8000/api/engineering/safety/check-all
- GET  http://localhost:8000/api/engineering/safety/check/{req_id}
- GET  http://localhost:8000/api/engineering/safety/asil-breakdown
- GET  http://localhost:8000/api/engineering/safety/critical-gaps
- GET  http://localhost:8000/api/engineering/safety/summary

### 📈 Impact & KG Visualization
- POST http://localhost:8000/api/engineering/impact/calibration
- GET  http://localhost:8000/api/engineering/impact/signal/{sig_id}
- GET  http://localhost:8000/api/engineering/impact/requirement/{req_id}
- GET  http://localhost:8000/api/engineering/impact/calibrations
- GET  http://localhost:8000/api/engineering/kg-viz/full
- GET  http://localhost:8000/api/engineering/kg-viz/domain/{domain}
- GET  http://localhost:8000/api/engineering/kg-viz/stats

---

## 🧾 License / Notes

ACIP-X1 is a modular automotive intelligence backend combining:
- Real-time vehicle telemetry
- AI-driven diagnostics
- Engineering lifecycle automation
- Knowledge graph reasoning
- Safety & compliance analysis (ISO 26262-ready design patterns)