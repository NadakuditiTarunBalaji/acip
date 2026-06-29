"""
ACIP-X1 — AI Chat Assistant for Engineers (Day 22 / E9)

Lets an engineer ask natural-language questions and get answers
grounded in the REAL Knowledge Graph and Impact Analysis (E7) already
built — e.g. "Show me all requirements related to battery temperature"
or "What will fail if I change CAL001?". This service does not invent
a new analysis engine; its job is to be the natural-language front
door to the structured queries that already exist (kg_engine.py's
search/lookup methods, ImpactAnalyzer's calibration/signal/requirement
impact methods).

Architecture: uses Gemini's function calling (tools) so the model
decides which real query to run based on the engineer's question,
we execute it for real against the actual KG data, then ask Gemini
to explain the real result conversationally. This is the same
honesty principle as the rest of ACIP-X1's "AI" features — the model
never answers from its own guess about automotive engineering, only
from data we actually looked up and handed back to it.
"""
import json
import logging
from google.genai import types

from backend.services.gemini_client import get_client, GEMINI_MODEL
from knowledge_graph.graph_builder.kg_engine import get_kg
from agents.requirement_agent.impact_analyzer import ImpactAnalyzer

logger = logging.getLogger("acip.engineer_chat")

_analyzer = ImpactAnalyzer()

SYSTEM_INSTRUCTION = (
    "You are an engineering assistant for ACIP-X1, helping automotive "
    "engineers query a real Knowledge Graph of requirements, signals, "
    "DTCs, faults, calibrations, and test cases. You have tools to "
    "search this graph and analyze the downstream impact of changing "
    "a calibration, signal, or requirement. ALWAYS call a tool to get "
    "real data before answering — never answer from your own "
    "knowledge of automotive engineering, since the engineer needs "
    "facts from THIS specific project's graph, not general knowledge. "
    "If a search returns no matches, say so plainly rather than "
    "guessing. Cite specific IDs (e.g. REQ001, CAL001) in your answer "
    "so the engineer can look them up. Keep answers concise and "
    "technical — this is a professional tool, not a casual chat."
)

# ── Tool (function) declarations — map 1:1 to real existing methods ──

_SEARCH_KG_TOOL = types.FunctionDeclaration(
    name="search_kg",
    description=(
        "Search the Knowledge Graph by keyword/topic across requirements, "
        "faults, DTCs, signals, calibrations, test cases, and ECUs. Use "
        "this for questions like 'show me all requirements about X' or "
        "'what faults relate to Y'."
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "The topic/keyword to search for, e.g. 'battery temperature'"},
        },
        "required": ["keyword"],
    },
)

_CALIBRATION_IMPACT_TOOL = types.FunctionDeclaration(
    name="analyze_calibration_impact",
    description=(
        "Analyze what would be affected if a specific calibration's value "
        "were changed — shows affected signals, requirements, DTCs, "
        "faults, and test cases. Use this for 'what will fail if I "
        "change this calibration' style questions. Requires the exact "
        "calibration ID (e.g. CAL001) — use search_kg first if the "
        "engineer named it by description rather than ID."
    ),
    parameters_json_schema={
        "type": "object",
        "properties": {
            "cal_id": {"type": "string", "description": "Calibration ID, e.g. CAL001"},
            "new_value": {"type": "number", "description": "Optional proposed new value"},
        },
        "required": ["cal_id"],
    },
)

_SIGNAL_IMPACT_TOOL = types.FunctionDeclaration(
    name="analyze_signal_impact",
    description="Analyze the full downstream impact of a specific signal (everything connected to it).",
    parameters_json_schema={
        "type": "object",
        "properties": {"sig_id": {"type": "string", "description": "Signal ID, e.g. SIG016"}},
        "required": ["sig_id"],
    },
)

_REQUIREMENT_IMPACT_TOOL = types.FunctionDeclaration(
    name="analyze_requirement_impact",
    description="Analyze the full downstream impact of changing a specific requirement.",
    parameters_json_schema={
        "type": "object",
        "properties": {"req_id": {"type": "string", "description": "Requirement ID, e.g. REQ001"}},
        "required": ["req_id"],
    },
)

_TOOLS = types.Tool(function_declarations=[
    _SEARCH_KG_TOOL, _CALIBRATION_IMPACT_TOOL, _SIGNAL_IMPACT_TOOL, _REQUIREMENT_IMPACT_TOOL,
])

_FUNCTION_MAP = {
    "search_kg": lambda args: get_kg().search_nodes(args["keyword"]),
    "analyze_calibration_impact": lambda args: _analyzer.analyze_calibration_impact(
        args["cal_id"].upper(), args.get("new_value")
    ),
    "analyze_signal_impact": lambda args: _analyzer.analyze_signal_impact(args["sig_id"].upper()),
    "analyze_requirement_impact": lambda args: _analyzer.analyze_requirement_impact(args["req_id"].upper()),
}

# In-memory conversation per session — engineering queries are
# stateless lookups, not incidents that need DB persistence.
_conversations: dict = {}


def get_conversation(session_id: str = "default") -> list:
    if session_id not in _conversations:
        _conversations[session_id] = []
    return _conversations[session_id]


def reset_conversation(session_id: str = "default"):
    _conversations.pop(session_id, None)


def ask(session_id: str, question: str) -> dict:
    """
    Sends the engineer's question to Gemini with KG/impact tools
    available. If Gemini calls a tool, we execute the REAL query and
    feed the result back so Gemini's final answer is grounded in
    actual data. Never raises — degrades gracefully like every other
    AI feature in ACIP-X1.
    """
    client = get_client()
    if client is None:
        return {
            "answer": "AI assistant unavailable — GEMINI_API_KEY not configured.",
            "tool_calls": [],
            "ai_available": False,
        }

    conversation = get_conversation(session_id)
    contents = list(conversation)
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=question)]))

    tool_calls_made = []

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[_TOOLS],
                temperature=0.2,
                max_output_tokens=500,
            ),
        )

        # Handle one round of function calling — sufficient for the
        # "search or analyze, then explain" pattern this tool covers.
        # Loop in case the model wants to chain a search then an
        # impact analysis (e.g. find the cal ID, then analyze it).
        max_rounds = 3
        for _ in range(max_rounds):
            if not response.function_calls:
                break

            contents.append(response.candidates[0].content)
            function_response_parts = []

            for fc in response.function_calls:
                fn_name = fc.name
                fn_args = dict(fc.args) if fc.args else {}
                tool_calls_made.append({"function": fn_name, "args": fn_args})

                if fn_name not in _FUNCTION_MAP:
                    result = {"error": f"Unknown function {fn_name}"}
                else:
                    try:
                        result = _FUNCTION_MAP[fn_name](fn_args)
                    except Exception as e:
                        logger.error(f"Tool execution failed for {fn_name}: {e}")
                        result = {"error": str(e)}

                function_response_parts.append(
                    types.Part.from_function_response(name=fn_name, response={"result": result})
                )

            contents.append(types.Content(role="user", parts=function_response_parts))

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[_TOOLS],
                    temperature=0.2,
                    max_output_tokens=500,
                ),
            )

        answer = response.text or "I wasn't able to generate a response — please rephrase your question."

        conversation.append(types.Content(role="user", parts=[types.Part.from_text(text=question)]))
        conversation.append(types.Content(role="model", parts=[types.Part.from_text(text=answer)]))
        _conversations[session_id] = conversation

        return {"answer": answer, "tool_calls": tool_calls_made, "ai_available": True}

    except Exception as e:
        logger.error(f"Engineer chat failed: {e}")
        return {
            "answer": "Something went wrong processing that question — please try again.",
            "tool_calls": tool_calls_made,
            "ai_available": False,
        }