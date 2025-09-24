from pydantic import BaseModel
from typing import List

class PolicyAnalysis(BaseModel):
    Mitigation_Targets: List[str] = []
    Adaptation_Strategies: List[str] = []
    Finance_Commitments: List[str] = []
    Legislation_Policies: List[str] = []
    Stakeholders: List[str] = []
    Targets_Timelines: List[str] = []
    Sectors_Covered: List[str] = []
    Monitoring_Reporting: List[str] = []
    International_Cooperation: List[str] = []
    Institutional_Arrangements: List[str] = []
    Social_Community: List[str] = []
    Technology_Innovation: List[str] = []