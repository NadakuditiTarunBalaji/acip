import json
from agents.impact_analysis_agent.impact_analysis_agent import ImpactAnalysisAgent
from agents.requirement_agent.requirement_parser import RequirementParser
from agents.root_cause_agent.root_cause_agent import RootCauseAgent


class RequirementRootCauseFlow:

    def __init__(self):
        self.requirement_agent = RequirementParser()
        self.rootcause_agent = RootCauseAgent()
        self.impact_agent = ImpactAnalysisAgent()

    def analyze(self, requirement):

        requirement_result = self.requirement_agent.parse(requirement)

        rootcause_result = self.rootcause_agent.analyze_fault(
            requirement_result["fault"]
        )

        impact_result = self.impact_agent.analyze_fault(
            requirement_result["fault"]
        )

        return {
            **requirement_result,
            **rootcause_result,
            **impact_result
        }


if __name__ == "__main__":

    flow = RequirementRootCauseFlow()

    requirements = [
        "Battery pack voltage shall not exceed 420V during normal operation.",
        "Motor speed shall not exceed 12000 RPM.",
        "Battery temperature shall not exceed 60C."
    ]

    for req in requirements:

        result = flow.analyze(req)

        print(json.dumps(result, indent=4))
        print("-" * 50)