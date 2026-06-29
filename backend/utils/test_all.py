"""
ACIP-X1 — Full System Test
Run this to verify every API is working correctly.

Usage:
    python -m backend.utils.test_all
"""
import requests
import json

BASE_URL = "http://localhost:8000"
PASS = "✅"
FAIL = "❌"
WARN = "⚠️"

results = []


def test(name: str, url: str, method: str = "GET", body: dict = None,
         expect_keys: list = None, expect_html: bool = False):
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        elif method == "POST":
            r = requests.post(url, json=body, timeout=5)

        if r.status_code != 200:
            print(f"{FAIL}  {name} — HTTP {r.status_code}")
            results.append(("FAIL", name))
            return

        # HTML pages — just check status 200
        if expect_html:
            print(f"{PASS}  {name}")
            results.append(("PASS", name))
            return

        # JSON pages — parse and check keys
        try:
            data = r.json()
        except Exception:
            print(f"{FAIL}  {name} — Response is not valid JSON")
            results.append(("FAIL", name))
            return

        if expect_keys:
            missing = [k for k in expect_keys if k not in str(data)]
            if missing:
                print(f"{WARN}  {name} — returned 200 but missing keys: {missing}")
                results.append(("WARN", name))
                return

        print(f"{PASS}  {name}")
        results.append(("PASS", name))

    except Exception as e:
        print(f"{FAIL}  {name} — ERROR: {e}")
        results.append(("FAIL", name))


print("\n" + "="*60)
print("  ACIP-X1 Full System Test")
print("="*60)

# ── HOME ──────────────────────────────────────────────────
print("\n📌 HOME")
test("Home endpoint",           f"{BASE_URL}/",       expect_keys=["ACIP-X1"])
test("Swagger UI accessible",   f"{BASE_URL}/docs",   expect_html=True)
test("ReDoc accessible",        f"{BASE_URL}/redoc",  expect_html=True)
test("OpenAPI JSON accessible", f"{BASE_URL}/openapi.json", expect_keys=["openapi"])

# ── CORE DATA APIs ────────────────────────────────────────
print("\n📌 CORE DATA APIs")
test("GET all ECUs",             f"{BASE_URL}/api/ecus/")
test("GET all Signals",          f"{BASE_URL}/api/signals/")
test("GET all Calibrations",     f"{BASE_URL}/api/calibrations/")
test("GET all DTCs",             f"{BASE_URL}/api/dtcs/")
test("GET all Faults",           f"{BASE_URL}/api/faults/")
test("GET all Requirements",     f"{BASE_URL}/api/requirements/")
test("GET all Test Cases",       f"{BASE_URL}/api/testcases/")
test("GET all Vehicle Data",     f"{BASE_URL}/api/vehicle-data/")
test("GET all Insurance Claims", f"{BASE_URL}/api/insurance/")

# ── CAN BUS ───────────────────────────────────────────────
print("\n📌 CAN BUS")
test(
    "POST CAN frame",
    f"{BASE_URL}/api/can/frame",
    method="POST",
    body={
        "vehicle_id": "VEH001",
        "can_id": "0x100",
        "dlc": 8,
        "raw_data": "FF00FF00FF00FF00",
        "decoded_data": {
            "rpm": 2500,
            "speed": 60,
            "engine_temp": 80,
            "battery_voltage": 350,
            "soc": 75,
            "fuel_level": 80
        }
    },
    expect_keys=["received"]
)
test("GET latest CAN frame",  f"{BASE_URL}/api/can/latest/VEH001")
test("GET CAN frame history", f"{BASE_URL}/api/can/frames/VEH001")

# ── DASHBOARD ─────────────────────────────────────────────
print("\n📌 DASHBOARD")
test("Dashboard summary",      f"{BASE_URL}/api/dashboard/summary",           expect_keys=["health_score"])
test("Health trend",           f"{BASE_URL}/api/dashboard/health-trend")
test("Active faults",          f"{BASE_URL}/api/dashboard/active-faults")
test("Active DTCs",            f"{BASE_URL}/api/dashboard/active-dtcs")
test("Calibration limits",     f"{BASE_URL}/api/dashboard/calibration-limits")

# ── AI ANALYSIS ───────────────────────────────────────────
print("\n📌 AI ANALYSIS")
test(
    "POST AI diagnose",
    f"{BASE_URL}/api/ai/diagnose",
    method="POST",
    body={
        "vehicle_id": "VEH001",
        "rpm": 2500,
        "speed": 60,
        "coolant_temp": 35,
        "battery_voltage": 380,
        "soc": 75
    },
    expect_keys=["health_score"]
)
test("GET analyze DTC", f"{BASE_URL}/api/ai/analyze-dtc/DTC001")

# ── KNOWLEDGE GRAPH ───────────────────────────────────────
print("\n📌 KNOWLEDGE GRAPH")
test("KG summary",                 f"{BASE_URL}/api/kg/summary",                  expect_keys=["total_nodes"])
test("KG fault FAULT001",          f"{BASE_URL}/api/kg/fault/FAULT001",           expect_keys=["fault_name"])
test("KG fault FAULT004",          f"{BASE_URL}/api/kg/fault/FAULT004",           expect_keys=["fault_name"])
test("KG DTC DTC001",              f"{BASE_URL}/api/kg/dtc/DTC001",               expect_keys=["dtc_name"])
test("KG signal SIG016",           f"{BASE_URL}/api/kg/signal/SIG016",            expect_keys=["signal_name"])
test("KG requirement REQ001",      f"{BASE_URL}/api/kg/requirement/REQ001/trace", expect_keys=["requirement"])
test("KG vehicle VEH001 chain",    f"{BASE_URL}/api/kg/vehicle/VEH001/chain",     expect_keys=["ecus"])
test("KG all faults",              f"{BASE_URL}/api/kg/faults/all")
test("KG requirements gaps",       f"{BASE_URL}/api/kg/requirements/gaps",        expect_keys=["total_requirements"])

# ── INDIVIDUAL RECORDS ────────────────────────────────────
print("\n📌 INDIVIDUAL RECORDS")
test("GET ECU by ID",          f"{BASE_URL}/api/ecus/ECU001")
test("GET Signal by ID",       f"{BASE_URL}/api/signals/SIG001")
test("GET DTC by ID",          f"{BASE_URL}/api/dtcs/DTC001")
test("GET Fault by ID",        f"{BASE_URL}/api/faults/FAULT001")
test("GET Requirement by ID",  f"{BASE_URL}/api/requirements/REQ001")
test("GET Calibration by ID",  f"{BASE_URL}/api/calibrations/CAL001")
test("GET TestCase by ID",     f"{BASE_URL}/api/testcases/TC001")

# ── SUMMARY ───────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for r in results if r[0] == "PASS")
warned = sum(1 for r in results if r[0] == "WARN")
failed = sum(1 for r in results if r[0] == "FAIL")
total  = len(results)

print(f"\n  Total Tests : {total}")
print(f"  {PASS} Passed  : {passed}")
print(f"  {WARN} Warnings: {warned}")
print(f"  {FAIL} Failed  : {failed}")

if failed == 0 and warned == 0:
    print(f"\n  🎉 ALL {total} TESTS PASSED! ACIP-X1 Foundation is SOLID!")
    print(f"  🚀 Ready for Week 2 — Engineering Mode!")
elif failed == 0:
    print(f"\n  ✅ All tests passed with {warned} warning(s).")
else:
    print(f"\n  ⚠️  {failed} test(s) failed. Fix before moving to Week 2.")
    print("\n  Failed tests:")
    for r in results:
        if r[0] == "FAIL":
            print(f"    ❌ {r[1]}")

print("="*60 + "\n")