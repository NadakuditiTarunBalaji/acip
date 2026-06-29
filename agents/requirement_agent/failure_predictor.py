"""
ACIP-X1 — Pre-Test Failure Predictor
Engineering Mode — Feature E3
All warnings shown honestly. Nothing hidden.
"""
from pathlib import Path
from typing import List, Dict
import pandas as pd
import re

BASE_PATH  = Path(__file__).resolve().parent.parent.parent
NODES_PATH = BASE_PATH / "knowledge_graph" / "nodes"
EDGES_PATH = BASE_PATH / "knowledge_graph" / "edges"
DB_PATH    = BASE_PATH / "database" / "sqlite" / "acip.db"


def _load(filename, folder):
    path = folder / filename
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception as e:
            print(f"Warning: {filename}: {e}")
    return pd.DataFrame()


def _extract_limit(text):
    if not text:
        return None
    # Handle "minus X" — preserve negative sign
    minus = re.search(r'minus\s+(\d+\.?\d*)', text, re.IGNORECASE)
    if minus:
        try:
            return -float(minus.group(1))
        except:
            pass
    patterns = [
        r'(\d+\.?\d*)\s*(?:V|A|C|RPM|km/h|kmh|%|mV|kW|Nm|ms)',
        r'exceed\s+(\d+\.?\d*)',
        r'below\s+(\d+\.?\d*)',
        r'above\s+(\d+\.?\d*)',
        r'minimum\s+(?:of\s+)?(\d+\.?\d*)',
        r'maximum\s+(?:of\s+)?(\d+\.?\d*)',
        r'within\s+(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:percent|degrees)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    return None


def _extract_direction(text):
    t = text.lower()
    if any(w in t for w in ["not exceed", "maximum", "max", "less than"]):
        return "max"
    if any(w in t for w in ["not drop", "not fall", "minimum", "min", "greater than"]):
        return "min"
    if "below" in t and "trigger" in t:
        return "trigger_below"
    if "above" in t and "trigger" in t:
        return "trigger_above"
    if "below" in t:
        return "max"
    if "above" in t:
        return "min"
    if "within" in t:
        return "timing"
    return "unknown"


def _is_timing(text):
    t = text.lower()
    return any(w in t for w in [
        "ms", "millisecond", "within", "respond", "response",
        "latency", "delay", "trigger within", "detect within",
        "activate within", "update within", "seconds"
    ])


def _cal_direction(cal_name):
    n = cal_name.lower()
    if any(w in n for w in ["max", "over", "maximum", "upper"]):
        return "max"
    if any(w in n for w in ["min", "under", "minimum", "lower", "recovery"]):
        return "min"
    return "unknown"


class FailurePredictor:

    def __init__(self):
        self.req_nodes  = _load("requirement_nodes.csv",  NODES_PATH)
        self.sig_nodes  = _load("signal_nodes.csv",       NODES_PATH)
        self.cal_nodes  = _load("calibration_nodes.csv",  NODES_PATH)
        self.dtc_nodes  = _load("dtc_nodes.csv",          NODES_PATH)
        self.tc_nodes   = _load("testcase_nodes.csv",     NODES_PATH)
        self.req_sig_edges = _load("requirement_signal_edges.csv",   EDGES_PATH)
        self.req_tc_edges  = _load("requirement_testcase_edges.csv", EDGES_PATH)
        self.sig_cal_edges = _load("signal_calibration_edges.csv",   EDGES_PATH)
        self.sig_dtc_edges = _load("signal_dtc_edges.csv",           EDGES_PATH)
        self.db_calibrations = self._load_db_calibrations()
        print(f"FailurePredictor loaded — {len(self.req_nodes)} requirements, "
              f"{len(self.db_calibrations)} DB calibrations")

    def _load_db_calibrations(self):
        try:
            import sqlite3
            conn = sqlite3.connect(str(DB_PATH))
            rows = conn.execute(
                "SELECT cal_id, parameter, value, unit FROM calibrations"
            ).fetchall()
            conn.close()
            return {r[0]: {"parameter": r[1], "value": r[2], "unit": r[3]} for r in rows}
        except Exception as e:
            print(f"Warning: DB calibrations not loaded: {e}")
            return {}

    def _targets(self, source, edge_df):
        if edge_df.empty:
            return []
        return edge_df[edge_df["source"] == source]["target"].tolist()

    def _node(self, node_id, df):
        if df.empty:
            return None
        row = df[df["node_id"] == node_id]
        return row.iloc[0] if not row.empty else None

    def predict_requirement_failure(self, req_id):
        req_node = self._node(req_id, self.req_nodes)
        if req_node is None:
            return {"req_id": req_id, "status": "Not Found"}

        req_text      = req_node["name"]
        req_limit     = _extract_limit(req_text)
        req_direction = _extract_direction(req_text)
        is_timing     = _is_timing(req_text)

        prediction = {
            "req_id":          req_id,
            "requirement":     req_text,
            "req_limit":       req_limit,
            "req_direction":   req_direction,
            "test_cases":      [],
            "failures":        [],
            "warnings":        [],
            "verdict":         "PASS",
            "confidence":      "High",
            "failure_reasons": []
        }

        # Test cases
        for tc_id in self._targets(req_id, self.req_tc_edges):
            tc = self._node(tc_id, self.tc_nodes)
            if tc is not None:
                prediction["test_cases"].append({
                    "tc_id": tc_id,
                    "name":  tc["name"],
                    "expected_result": tc.get("expected_result", "N/A")
                })

        # No numeric limit
        if req_limit is None:
            prediction["confidence"] = "Low"
            prediction["warnings"].append({
                "type":   "No Numeric Limit",
                "detail": f"Cannot extract numeric limit from requirement",
                "impact": "Quantitative validation not possible",
                "fix":    "Rewrite with explicit numeric limit"
            })
            prediction["verdict"] = "WARNING"

        # Signals
        for sig_id in self._targets(req_id, self.req_sig_edges):
            sig = self._node(sig_id, self.sig_nodes)
            if sig is None:
                continue

            sig_min = float(sig["min_value"]) if pd.notna(sig.get("min_value")) else None
            sig_max = float(sig["max_value"]) if pd.notna(sig.get("max_value")) else None

            # Signal range check — skip for timing requirements
            if req_limit is not None and sig_min is not None and sig_max is not None and not is_timing:
                if req_direction == "max" and req_limit > sig_max:
                    prediction["failures"].append({
                        "type":   "Requirement Exceeds Signal Range",
                        "detail": f"REQ limit {req_limit} > Signal {sig_id} max {sig_max}",
                        "impact": "Test will FAIL — signal cannot reach required limit",
                        "fix":    f"Update signal {sig_id} max_value or revise requirement"
                    })
                    prediction["verdict"] = "FAIL"
                    prediction["failure_reasons"].append(
                        f"Signal {sig_id} max={sig_max} < requirement limit={req_limit}"
                    )

            # Calibration check
            for cal_id in self._targets(sig_id, self.sig_cal_edges):
                db_cal = self.db_calibrations.get(cal_id)
                if not db_cal or req_limit is None or is_timing:
                    continue

                cal_value   = db_cal["value"]
                cal_dir     = _cal_direction(db_cal["parameter"])

                # Only compare matching directions
                # Max requirement → max calibration only
                # Min requirement → min calibration only
                if req_direction == "max" and cal_dir == "max":
                    if abs(cal_value - req_limit) > 0.01:
                        prediction["warnings"].append({
                            "type":   "Calibration Mismatch",
                            "detail": f"{cal_id}={cal_value} vs REQ limit={req_limit}",
                            "impact": "DTC trigger differs from requirement boundary",
                            "fix":    f"Update {cal_id} to {req_limit}"
                        })
                        if prediction["verdict"] == "PASS":
                            prediction["verdict"] = "WARNING"

                elif req_direction == "min" and cal_dir == "min":
                    # For min requirements — compare only when same sign
                    # e.g. -20°C undertemp cal matches -20°C undertemp req
                    if abs(cal_value - req_limit) > 0.01:
                        prediction["warnings"].append({
                            "type":   "Calibration Mismatch",
                            "detail": f"{cal_id}={cal_value} vs REQ min={req_limit}",
                            "impact": "DTC trigger differs from requirement boundary",
                            "fix":    f"Update {cal_id} to {req_limit}"
                        })
                        if prediction["verdict"] == "PASS":
                            prediction["verdict"] = "WARNING"

                # Opposite direction combinations are intentional — skip silently
                # e.g. undervoltage cal (280V) linked to same signal as overvoltage req (420V)

            # DTC check
            if not self._targets(sig_id, self.sig_dtc_edges):
                prediction["failures"].append({
                    "type":   "No DTC Defined",
                    "detail": f"Signal {sig_id} has no DTC trigger",
                    "impact": "Violation undetectable — test will FAIL",
                    "fix":    f"Add DTC for {sig_id}"
                })
                prediction["verdict"] = "FAIL"
                prediction["failure_reasons"].append(f"No DTC for {sig_id}")

        return prediction

    def predict_all(self):
        predictions = []
        fail_count  = 0
        warn_count  = 0
        pass_count  = 0
        critical    = []

        for _, req in self.req_nodes.iterrows():
            pred = self.predict_requirement_failure(req["node_id"])
            predictions.append(pred)
            if pred["verdict"] == "FAIL":
                fail_count += 1
                critical.append({
                    "req_id":      pred["req_id"],
                    "requirement": pred["requirement"],
                    "reasons":     pred["failure_reasons"],
                    "test_cases":  [tc["tc_id"] for tc in pred["test_cases"]]
                })
            elif pred["verdict"] == "WARNING":
                warn_count += 1
            else:
                pass_count += 1

        total     = len(predictions)
        pass_rate = round((pass_count + warn_count) / total * 100, 1) if total > 0 else 0

        if fail_count == 0 and warn_count == 0:
            verdict = "ALL PASS ✅"
            risk    = "Low"
            action  = "Ready for testing"
        elif fail_count == 0:
            verdict = f"PASS WITH {warn_count} WARNING(S) ⚠️"
            risk    = "Low"
            action  = f"Fix {warn_count} warning(s) then run tests"
        else:
            verdict = f"{fail_count} FAILURE(S) PREDICTED ❌"
            risk    = "High" if fail_count > 5 else "Medium"
            action  = f"Fix {fail_count} failure(s) before testing"

        return {
            "total_requirements": total,
            "predicted_pass":     pass_count,
            "predicted_fail":     fail_count,
            "predicted_warning":  warn_count,
            "pass_rate":          pass_rate,
            "critical_failures":  critical,
            "predictions":        predictions,
            "summary": {
                "verdict": verdict,
                "risk":    risk,
                "action":  action
            }
        }

    def predict_by_system(self, system):
        if self.req_nodes.empty:
            return {"error": "No requirements loaded"}
        reqs = self.req_nodes[
            self.req_nodes["name"].str.lower().str.contains(system.lower(), na=False)
        ]
        predictions = [self.predict_requirement_failure(r["node_id"]) for _, r in reqs.iterrows()]
        return {
            "system":      system,
            "total":       len(predictions),
            "fail":        sum(1 for p in predictions if p["verdict"] == "FAIL"),
            "warning":     sum(1 for p in predictions if p["verdict"] == "WARNING"),
            "pass":        sum(1 for p in predictions if p["verdict"] == "PASS"),
            "predictions": predictions
        }