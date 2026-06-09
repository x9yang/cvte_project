from typing import Optional
from sqlalchemy.orm import Session

from .state import AgentState
from .nodes import extract_features, filter_candidates, analyze_workload, make_decision


class AssignmentAgent:
    """合同分派Agent"""

    def __init__(self, db: Session):
        self.db = db

    def run(self, input_data: dict) -> dict:
        """
        执行分派决策

        Args:
            input_data: 包含 pages, word_count, contract_type, text_content, extra_info

        Returns:
            分派结果字典
        """
        # 初始化状态
        state = AgentState(**input_data)

        # 节点1: 特征提取
        state = extract_features(state, self.db)

        # 节点2: 人员筛选
        state = filter_candidates(state, self.db)

        # 节点3: 负载分析
        state = analyze_workload(state)

        # 节点4: 综合决策
        state = make_decision(state)

        return {
            "recommended_staff": state.recommended_staff,
            "staff_id": state.staff_id,
            "reason": state.reason,
            "confidence": state.confidence,
            "contract_type": state.identified_type,
            "workload_summary": state.workload_analysis,
        }
