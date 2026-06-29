"""
ACIP-X1 — Auto Test Case Generator
Engineering Mode — Feature E10

Given any requirement, automatically generates a complete test case:
- Test steps
- Test data / stimulus
- Expected result
- Pass/Fail criteria
- Preconditions

What takes a test engineer 30 minutes per requirement → done in seconds.
"""
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
import re

BASE_PATH  = Path(__file__).resolve().parent.parent.parent
NODES_PATH = BASE_PATH / "knowledge_graph" / "nodes"
EDGES_PATH = BASE_PATH / "knowledge_graph" / "edges"


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
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except:
                pass
    return None


def _extract_unit(text):
    """Extract unit of measurement from requirement text"""
    units = {
        "V":       ["voltage", "volt", "v)"],
        "A":       ["current", "amp"],
        "°C":      ["temperature", "degrees c", "degrees celsius", "celsius"],
        "RPM":     ["rpm", "speed.*motor", "motor.*speed"],
        "km/h":    ["km/h", "kmh", "vehicle speed"],
        "%":       ["percent", "%", "soc", "soh"],
        "mV":      ["mv", "cell voltage imbalance"],
        "kW":      ["kw", "power"],
        "Nm":      ["nm", "torque"],
        "ms":      ["ms", "millisecond"],
    }
    text_lower = text.lower()
    for unit, keywords in units.items():
        for kw in keywords:
            if re.search(kw, text_lower):
                return unit
    return ""


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


class TestCaseGenerator:
    """
    Generates complete, ready-to-execute test cases from requirements.
    """

    def __init__(self):
        self.req_nodes = _load("requirement_nodes.csv", NODES_PATH)
        self.sig_nodes = _load("signal_nodes.csv",      NODES_PATH)
        self.dtc_nodes = _load("dtc_nodes.csv",         NODES_PATH)
        self.req_sig_edges = _load("requirement_signal_edges.csv", EDGES_PATH)
        self.sig_dtc_edges = _load("signal_dtc_edges.csv",         EDGES_PATH)
        print(f"TestCaseGenerator loaded — {len(self.req_nodes)} requirements")

    def _targets(self, source, edge_df):
        if edge_df.empty:
            return []
        return edge_df[edge_df["source"] == source]["target"].tolist()

    def _node(self, node_id, df):
        if df.empty:
            return None
        row = df[df["node_id"] == node_id]
        return row.iloc[0] if not row.empty else None

    def generate_from_text(self, requirement_text: str, req_id: str = "REQ_NEW") -> Dict:
        """
        Generate a complete test case from raw requirement text.
        Works even for requirements not yet in the Knowledge Graph.
        """
        limit     = _extract_limit(requirement_text)
        direction = _extract_direction(requirement_text)
        unit      = _extract_unit(requirement_text)
        is_timing = _is_timing(requirement_text)

        # Try to find matching signal/DTC from KG
        signal_name = None
        dtc_name    = None
        sig_id      = None

        req_row = self.req_nodes[self.req_nodes["node_id"] == req_id]
        if not req_row.empty:
            sig_ids = self._targets(req_id, self.req_sig_edges)
            if sig_ids:
                sig_id   = sig_ids[0]
                sig_node = self._node(sig_id, self.sig_nodes)
                if sig_node is not None:
                    signal_name = sig_node["name"]
                dtc_ids = self._targets(sig_id, self.sig_dtc_edges)
                if dtc_ids:
                    dtc_node = self._node(dtc_ids[0], self.dtc_nodes)
                    if dtc_node is not None:
                        dtc_name = dtc_node["name"]

        # ── Build Test Case ────────────────────────────────

        title = self._generate_title(requirement_text, limit, direction, unit, is_timing)
        preconditions = self._generate_preconditions(signal_name, requirement_text)
        steps = self._generate_steps(requirement_text, limit, direction, unit, signal_name, is_timing)
        expected = self._generate_expected_result(limit, direction, unit, dtc_name, is_timing)
        pass_criteria = self._generate_pass_criteria(limit, direction, unit, dtc_name, is_timing)
        fail_criteria = self._generate_fail_criteria(limit, direction, unit, dtc_name, is_timing)
        test_data = self._generate_test_data(limit, direction, unit, is_timing)

        return {
            "req_id":         req_id,
            "requirement":    requirement_text,
            "test_case_id":   f"TC_AUTO_{req_id}",
            "title":          title,
            "preconditions":  preconditions,
            "test_data":      test_data,
            "steps":          steps,
            "expected_result": expected,
            "pass_criteria":  pass_criteria,
            "fail_criteria":  fail_criteria,
            "signal":         signal_name or "Not mapped",
            "dtc":            dtc_name or "Not mapped",
            "extracted_limit": limit,
            "extracted_unit":  unit,
            "test_type":      "Timing Test" if is_timing else "Boundary Value Test",
            "automation_ready": limit is not None
        }

    def _generate_title(self, text, limit, direction, unit, is_timing):
        if is_timing:
            return f"Verify response time requirement: {text[:60]}"
        if limit is None:
            return f"Verify: {text[:60]}"
        if direction == "max":
            return f"Verify system behavior when value exceeds {limit}{unit}"
        elif direction == "min":
            return f"Verify system behavior when value drops below {limit}{unit}"
        elif "trigger" in direction:
            return f"Verify alert triggers at threshold {limit}{unit}"
        return f"Verify: {text[:60]}"

    def _generate_preconditions(self, signal_name, text):
        pre = [
            "Vehicle ignition is ON",
            "ACIP-X1 system is initialized and connected via CAN bus",
            "All ECUs are powered and communicating",
        ]
        if signal_name:
            pre.append(f"Signal '{signal_name}' is being monitored and reporting valid data")
        return pre

    def _generate_steps(self, text, limit, direction, unit, signal_name, is_timing):
        sig_display = signal_name or "the target signal"

        if is_timing:
            return [
                f"Step 1: Inject the fault/event condition described in the requirement",
                f"Step 2: Start timer at the moment of fault injection",
                f"Step 3: Monitor for DTC trigger / system response",
                f"Step 4: Stop timer when response is detected",
                f"Step 5: Record elapsed time and compare against requirement limit of {limit}{unit}"
            ]

        if limit is None:
            return [
                f"Step 1: Set up test environment for: {text}",
                f"Step 2: Execute the functional scenario described in the requirement",
                f"Step 3: Observe system behavior",
                f"Step 4: Record results for manual review"
            ]

        if direction == "max":
            boundary = round(limit + (limit * 0.001 if limit != 0 else 1), 3)
            return [
                f"Step 1: Set {sig_display} to nominal value (within normal operating range)",
                f"Step 2: Gradually increase {sig_display} towards the limit of {limit}{unit}",
                f"Step 3: Apply {sig_display} = {limit}{unit} (boundary value) — verify system remains stable",
                f"Step 4: Apply {sig_display} = {boundary}{unit} (limit + 1) — verify violation is detected",
                f"Step 5: Monitor system response and DTC status"
            ]
        elif direction == "min":
            boundary = round(limit - (limit * 0.001 if limit != 0 else 1), 3)
            return [
                f"Step 1: Set {sig_display} to nominal value (within normal operating range)",
                f"Step 2: Gradually decrease {sig_display} towards the limit of {limit}{unit}",
                f"Step 3: Apply {sig_display} = {limit}{unit} (boundary value) — verify system remains stable",
                f"Step 4: Apply {sig_display} = {boundary}{unit} (limit - 1) — verify violation is detected",
                f"Step 5: Monitor system response and DTC status"
            ]
        elif "trigger" in direction:
            return [
                f"Step 1: Set {sig_display} to a value above the trigger threshold ({limit}{unit})",
                f"Step 2: Verify no alert is active",
                f"Step 3: Gradually decrease {sig_display} towards {limit}{unit}",
                f"Step 4: Cross the threshold — set {sig_display} below {limit}{unit}",
                f"Step 5: Verify alert/warning is triggered immediately"
            ]

        return [f"Step 1: Execute test for: {text}"]

    def _generate_expected_result(self, limit, direction, unit, dtc_name, is_timing):
        if is_timing:
            return f"System response/DTC trigger occurs within {limit}{unit} of fault injection"
        if limit is None:
            return "System behaves as described in the functional requirement"
        if direction == "max":
            dtc_text = f" and {dtc_name} is logged" if dtc_name else ""
            return f"At {limit}{unit} system remains within spec. Above {limit}{unit}, violation is detected{dtc_text}"
        elif direction == "min":
            dtc_text = f" and {dtc_name} is logged" if dtc_name else ""
            return f"At {limit}{unit} system remains within spec. Below {limit}{unit}, violation is detected{dtc_text}"
        elif "trigger" in direction:
            return f"Warning/alert is displayed immediately when value crosses {limit}{unit}"
        return "System produces correct output as per requirement"

    def _generate_pass_criteria(self, limit, direction, unit, dtc_name, is_timing):
        if is_timing:
            return [
                f"Response time ≤ {limit}{unit}",
                "No missed detections",
                "Timer measurement repeatable across 3 runs"
            ]
        if limit is None:
            return ["System behavior matches functional description", "No unexpected errors logged"]

        criteria = [f"System remains stable at boundary value {limit}{unit}"]
        if dtc_name:
            criteria.append(f"{dtc_name} is triggered when limit is exceeded")
        criteria.append("No false positives within normal operating range")
        return criteria

    def _generate_fail_criteria(self, limit, direction, unit, dtc_name, is_timing):
        if is_timing:
            return [f"Response time > {limit}{unit}", "Detection missed or delayed"]
        if limit is None:
            return ["System produces unexpected output", "Error or crash occurs"]

        criteria = []
        if dtc_name:
            criteria.append(f"{dtc_name} does NOT trigger when limit is exceeded")
            criteria.append(f"{dtc_name} triggers prematurely before limit is reached")
        criteria.append("System becomes unstable or unresponsive")
        return criteria

    def _generate_test_data(self, limit, direction, unit, is_timing):
        if limit is None:
            return {"note": "No numeric test data — functional test"}

        if is_timing:
            return {
                "fault_injection_time": "T0",
                "max_response_time":    f"{limit}{unit}",
                "measurement_points":   ["T0", "T0+50ms", "T0+100ms"]
            }

        if direction == "max":
            return {
                "nominal_value":  f"{round(limit * 0.7, 2)}{unit}",
                "boundary_value": f"{limit}{unit}",
                "over_limit":     f"{round(limit * 1.01, 3)}{unit}"
            }
        elif direction == "min":
            return {
                "nominal_value":  f"{round(limit * 1.3, 2) if limit != 0 else 10}{unit}",
                "boundary_value": f"{limit}{unit}",
                "under_limit":    f"{round(limit - abs(limit * 0.01) - 0.01, 3) if limit != 0 else -1}{unit}"
            }
        elif "trigger" in direction:
            return {
                "above_threshold": f"{round(limit * 1.5, 2)}{unit}",
                "threshold":       f"{limit}{unit}",
                "below_threshold": f"{round(limit * 0.9, 2)}{unit}"
            }
        return {"limit": f"{limit}{unit}"}

    def generate_for_requirement(self, req_id: str) -> Dict:
        """Generate test case for an existing requirement in the KG"""
        req_node = self._node(req_id.upper(), self.req_nodes)
        if req_node is None:
            return {"error": f"Requirement {req_id} not found"}
        return self.generate_from_text(req_node["name"], req_id.upper())

    def generate_for_all(self) -> Dict:
        """Generate test cases for ALL requirements"""
        results = []
        for _, req in self.req_nodes.iterrows():
            tc = self.generate_from_text(req["name"], req["node_id"])
            results.append(tc)

        automation_ready = sum(1 for r in results if r["automation_ready"])

        return {
            "total":             len(results),
            "automation_ready":  automation_ready,
            "manual_review_needed": len(results) - automation_ready,
            "test_cases":        results
        }