import json

from agents.root_cause_agent.diagnostic_engine import DiagnosticEngine
from agents.root_cause_agent.root_cause_agent import RootCauseAgent
from agents.impact_analysis_agent.impact_analysis_agent import ImpactAnalysisAgent


class EngineeringIntelligenceFlow:

    def __init__(self):

        self.diagnostic_engine = DiagnosticEngine()
        self.rootcause_agent = RootCauseAgent()
        self.impact_agent = ImpactAnalysisAgent()

    def analyze_signal(self, signal, value):

        diagnostic_result = self.diagnostic_engine.evaluate_signal(
            signal,
            value
        )

        if diagnostic_result["fault"] is None:

            return diagnostic_result

        rootcause_result = self.rootcause_agent.analyze_fault(
            diagnostic_result["fault"]
        )

        impact_result = self.impact_agent.analyze_fault(
    diagnostic_result["fault"]
)

        return {
            **diagnostic_result,
            **rootcause_result,
            **impact_result
        }


if __name__ == "__main__":

    flow = EngineeringIntelligenceFlow()

    tests = [

        ("Battery_Voltage", 435),
        ("Battery_Temperature", 75),
        ("Motor_Speed", 13000)

    ]

    for signal, value in tests:

        result = flow.analyze_signal(
            signal,
            value
        )

        print(json.dumps(result, indent=4))
        print("-" * 50)