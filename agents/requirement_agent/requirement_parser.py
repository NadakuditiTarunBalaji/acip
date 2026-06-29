"""
ACIP-X1 — AI Requirement Parser
Parses requirements from any file format:
PDF, Excel, Word, CSV, TXT

Extracts:
- Requirement ID
- Description
- Category (Safety / Functional / Performance)
- System (Battery / Powertrain / Thermal / Braking etc.)
- Keywords (signal names, limits, thresholds)
"""
import os
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict


# ── Keyword Maps for Auto-Classification ──────────────────

CATEGORY_KEYWORDS = {
    "Safety": [
        "shall not exceed", "shall not drop", "shall not fall",
        "maximum", "minimum", "limit", "threshold", "critical",
        "fault", "failure", "protection", "overvoltage", "undervoltage",
        "overtemperature", "overcurrent", "iso 26262", "asil",
        "safety", "hazard", "risk"
    ],
    "Functional": [
        "shall", "must", "should", "provide", "support", "enable",
        "trigger", "activate", "detect", "monitor", "display",
        "warn", "alert", "notify", "calculate", "estimate"
    ],
    "Performance": [
        "response time", "accuracy", "precision", "efficiency",
        "latency", "throughput", "bandwidth", "resolution",
        "within", "less than", "greater than", "percentage"
    ]
}

SYSTEM_KEYWORDS = {
    "Battery": [
        "battery", "cell", "soc", "soh", "voltage", "current",
        "charge", "discharge", "bms", "balancing", "capacity"
    ],
    "Powertrain": [
        "motor", "torque", "rpm", "speed", "inverter", "power",
        "drivetrain", "transmission", "acceleration", "deceleration"
    ],
    "Thermal": [
        "temperature", "thermal", "cooling", "heating", "heat",
        "coolant", "radiator", "fan", "hvac", "climate"
    ],
    "Braking": [
        "brake", "braking", "regenerative", "regen", "abs",
        "deceleration", "stopping"
    ],
    "Charging": [
        "charging", "charger", "plug", "connector", "dc fast",
        "ac charging", "onboard charger", "obc"
    ],
    "Safety": [
        "safety", "iso 26262", "asil", "fmea", "hazard",
        "fault tolerant", "redundan", "watchdog"
    ]
}


def classify_category(text: str) -> str:
    text_lower = text.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[cat] += 1
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "Functional"


def classify_system(text: str) -> str:
    text_lower = text.lower()
    scores = {sys: 0 for sys in SYSTEM_KEYWORDS}
    for sys, keywords in SYSTEM_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[sys] += 1
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "General"


def extract_keywords(text: str) -> List[str]:
    """Extract signal names, limits, units from requirement text"""
    keywords = []

    # Extract numbers with units
    patterns = [
        r'\d+\.?\d*\s*(?:V|A|°C|C|RPM|km/h|kmh|%|mV|kW|Nm|ms)',
        r'(?:SIG|DTC|CAL|ECU|REQ|FAULT)\d+',
        r'\b(?:overvoltage|undervoltage|overcurrent|overtemperature)\b',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend(matches)

    return list(set(keywords))


def generate_req_id(index: int, existing_ids: List[str]) -> str:
    """Generate unique requirement ID"""
    req_id = f"REQ{str(index).zfill(3)}"
    counter = index
    while req_id in existing_ids:
        counter += 1
        req_id = f"REQ{str(counter).zfill(3)}"
    return req_id


def is_valid_requirement(text: str) -> bool:
    """Check if a line/cell is actually a requirement"""
    if not text or len(text.strip()) < 10:
        return False
    text_lower = text.lower().strip()
    # Skip headers and metadata
    skip_words = [
        "requirement", "description", "id", "category", "system",
        "no.", "#", "sr.", "s.no", "document", "version", "date",
        "author", "revision", "page", "title", "contents"
    ]
    for word in skip_words:
        if text_lower == word or text_lower.startswith(word + " "):
            return False
    # Must have some action word to be a requirement
    action_words = [
        "shall", "must", "should", "will", "not exceed", "not drop",
        "not fall", "provide", "detect", "monitor", "trigger",
        "activate", "support", "ensure", "verify"
    ]
    return any(word in text_lower for word in action_words)


# ── File Parsers ──────────────────────────────────────────

def parse_txt(file_path: str) -> List[str]:
    """Parse plain text file"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip()]


def parse_csv(file_path: str) -> List[str]:
    """Parse CSV file"""
    df = pd.read_csv(file_path, encoding="utf-8", errors="replace")
    texts = []
    for col in df.columns:
        col_lower = str(col).lower()
        if any(word in col_lower for word in ["req", "description", "statement", "text"]):
            texts.extend(df[col].dropna().astype(str).tolist())
    if not texts:
        # Take all string columns
        for col in df.select_dtypes(include="object").columns:
            texts.extend(df[col].dropna().astype(str).tolist())
    return texts


def parse_excel(file_path: str) -> List[str]:
    """Parse Excel file"""
    xl = pd.ExcelFile(file_path)
    texts = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        for col in df.columns:
            col_lower = str(col).lower()
            if any(word in col_lower for word in ["req", "description", "statement", "text", "requirement"]):
                texts.extend(df[col].dropna().astype(str).tolist())
        if not texts:
            for col in df.select_dtypes(include="object").columns:
                texts.extend(df[col].dropna().astype(str).tolist())
    return texts


def parse_pdf(file_path: str) -> List[str]:
    """Parse PDF file"""
    try:
        import pdfplumber
        texts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = text.split("\n")
                    texts.extend([l.strip() for l in lines if l.strip()])
        return texts
    except ImportError:
        # Fallback if pdfplumber not installed
        return []


def parse_docx(file_path: str) -> List[str]:
    """Parse Word document"""
    try:
        import docx
        doc = docx.Document(file_path)
        return [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    except ImportError:
        return []


# ── Main Parser ───────────────────────────────────────────

class RequirementParser:
    """
    Main AI Requirement Parser
    Accepts any file format and returns structured requirements
    """

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse any file and extract requirements

        Returns:
            {
                "total_found": int,
                "requirements": [...],
                "file_type": str,
                "errors": [...]
            }
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        errors = []

        # Extract raw text lines based on file type
        try:
            if ext == ".txt":
                raw_lines = parse_txt(file_path)
                file_type = "Text"
            elif ext == ".csv":
                raw_lines = parse_csv(file_path)
                file_type = "CSV"
            elif ext in [".xlsx", ".xls"]:
                raw_lines = parse_excel(file_path)
                file_type = "Excel"
            elif ext == ".pdf":
                raw_lines = parse_pdf(file_path)
                file_type = "PDF"
            elif ext in [".docx", ".doc"]:
                raw_lines = parse_docx(file_path)
                file_type = "Word"
            else:
                return {
                    "total_found": 0,
                    "requirements": [],
                    "file_type": "Unknown",
                    "errors": [f"Unsupported file type: {ext}"]
                }
        except Exception as e:
            return {
                "total_found": 0,
                "requirements": [],
                "file_type": ext,
                "errors": [str(e)]
            }

        # Filter valid requirements
        valid_lines = [l for l in raw_lines if is_valid_requirement(l)]

        # Build structured requirements
        requirements = []
        existing_ids = []

        for i, line in enumerate(valid_lines, start=1):
            req_id = generate_req_id(i, existing_ids)
            existing_ids.append(req_id)

            req = {
                "req_id":     req_id,
                "description": line.strip(),
                "category":   classify_category(line),
                "system":     classify_system(line),
                "keywords":   extract_keywords(line),
                "source_file": path.name,
                "confidence": self._calculate_confidence(line)
            }
            requirements.append(req)

        return {
            "total_found":    len(requirements),
            "requirements":   requirements,
            "file_type":      file_type,
            "raw_lines_total": len(raw_lines),
            "filtered_out":   len(raw_lines) - len(valid_lines),
            "errors":         errors
        }

    def parse_text(self, text: str) -> Dict:
        """Parse plain text input directly (no file needed)"""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        valid_lines = [l for l in lines if is_valid_requirement(l)]

        requirements = []
        existing_ids = []

        for i, line in enumerate(valid_lines, start=1):
            req_id = generate_req_id(i, existing_ids)
            existing_ids.append(req_id)

            req = {
                "req_id":      req_id,
                "description": line.strip(),
                "category":    classify_category(line),
                "system":      classify_system(line),
                "keywords":    extract_keywords(line),
                "source_file": "manual_input",
                "confidence":  self._calculate_confidence(line)
            }
            requirements.append(req)

        return {
            "total_found":  len(requirements),
            "requirements": requirements,
            "file_type":    "Text Input",
            "errors":       []
        }

    def _calculate_confidence(self, text: str) -> str:
        """Calculate how confident we are this is a real requirement"""
        text_lower = text.lower()
        score = 0

        if "shall" in text_lower:
            score += 3
        if "must" in text_lower:
            score += 2
        if re.search(r'\d+\.?\d*\s*(?:V|A|°C|C|RPM|%)', text):
            score += 2
        if any(w in text_lower for w in ["not exceed", "not drop", "not fall"]):
            score += 2
        if len(text) > 20:
            score += 1

        if score >= 6:
            return "High"
        elif score >= 3:
            return "Medium"
        else:
            return "Low"