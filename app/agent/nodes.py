import json
import os
import httpx
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from .state import AgentState
from ..models.models import Staff, ContractType


def call_llm(prompt: str) -> str:
    """调用LLM API"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    if not api_key:
        # 无API Key时使用模拟响应
        return '{"staff_name": "张三", "reason": "模拟响应：技能匹配且负载适中", "confidence": 0.8}'

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个法务合同分派决策专家。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }

    try:
        # 使用无代理传输
        transport = httpx.HTTPTransport(proxy=None)
        with httpx.Client(timeout=60.0, transport=transport) as client:
            response = client.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"LLM调用失败: {e}")
        return '{"staff_name": "张三", "reason": "LLM调用失败，使用默认选择", "confidence": 0.5}'


def extract_features(state: AgentState, db: Session) -> AgentState:
    """节点1: 特征提取 - 识别合同类型"""
    # 如果已有合同类型，直接使用
    if state.contract_type:
        state.identified_type = state.contract_type
        print(f"[特征提取] 使用用户指定的合同类型: {state.contract_type}")
        return state

    # 从文本内容推断类型
    print(f"[特征提取] text_content 长度: {len(state.text_content) if state.text_content else 0}")
    if state.text_content:
        # 获取所有合同类型供参考
        types = db.query(ContractType).all()
        type_names = [t.name for t in types]

        prompt = f"""根据以下合同内容，判断合同类型。

可选的合同类型: {', '.join(type_names)}

合同内容:
{state.text_content}

额外信息: {state.extra_info or '无'}

请只返回合同类型名称，不要其他内容。如果无法判断，返回"其他"。"""

        print(f"[特征提取] 发送给LLM的完整text_content:\n{state.text_content}")
        print(f"[特征提取] 调用 LLM 分析合同类型...")
        try:
            result = call_llm(prompt)
            print(f"[特征提取] LLM 返回: {result}")
            # 清理结果，确保是有效的类型名称
            cleaned = result.strip().strip('"').strip("'")
            print(f"[特征提取] 清理后: {cleaned}")
            # 验证是否是有效的类型名称
            if cleaned in type_names:
                state.identified_type = cleaned
                print(f"[特征提取] 精确匹配: {cleaned}")
            else:
                # 尝试模糊匹配
                matched = False
                for type_name in type_names:
                    if type_name in cleaned or cleaned in type_name:
                        state.identified_type = type_name
                        matched = True
                        print(f"[特征提取] 模糊匹配: {type_name}")
                        break
                if not matched:
                    state.identified_type = "其他"
        except Exception as e:
            print(f"合同类型识别失败: {e}")
            state.identified_type = "其他"
    else:
        state.identified_type = "其他"

    return state


def filter_candidates(state: AgentState, db: Session) -> AgentState:
    """节点2: 人员筛选 - 按技能标签匹配"""
    contract_type = state.identified_type or "其他"

    # 查询具有匹配技能标签的人员
    all_staff = db.query(Staff).all()

    candidates = []
    for staff in all_staff:
        skill_tags = staff.skill_tags or []
        # 精确匹配或包含匹配
        is_match = any(
            tag in contract_type or contract_type in tag
            for tag in skill_tags
        )
        if is_match or "通用" in skill_tags:
            candidates.append({
                "id": staff.id,
                "name": staff.name,
                "skill_tags": skill_tags,
                "current_todo_count": staff.current_todo_count,
                "weekly_assigned": staff.weekly_assigned,
                "monthly_assigned": staff.monthly_assigned,
            })

    # 如果没有匹配的候选人，返回所有人
    if not candidates:
        candidates = [
            {
                "id": staff.id,
                "name": staff.name,
                "skill_tags": staff.skill_tags or [],
                "current_todo_count": staff.current_todo_count,
                "weekly_assigned": staff.weekly_assigned,
                "monthly_assigned": staff.monthly_assigned,
            }
            for staff in all_staff
        ]

    state.candidates = candidates
    return state


def analyze_workload(state: AgentState) -> AgentState:
    """节点3: 负载分析"""
    if not state.candidates:
        state.workload_analysis = "无可用候选人"
        return state

    workload_info = []
    for c in state.candidates:
        total_load = (
            c["current_todo_count"] * 3
            + c["weekly_assigned"] * 2
            + c["monthly_assigned"]
        )
        workload_info.append(
            f"{c['name']}: 当前待办{c['current_todo_count']}件, "
            f"本周{c['weekly_assigned']}件, 本月{c['monthly_assigned']}件, "
            f"综合负载分数: {total_load}"
        )

    state.workload_analysis = "\n".join(workload_info)
    return state


def make_decision(state: AgentState) -> AgentState:
    """节点4: 综合决策"""
    candidates_desc = "\n".join([
        f"- {c['name']}: 技能={c['skill_tags']}, "
        f"待办={c['current_todo_count']}, 本周={c['weekly_assigned']}, 本月={c['monthly_assigned']}"
        for c in state.candidates
    ])

    prompt = f"""根据以下信息，选择最合适的法务人员。

## 合同信息
- 合同类型: {state.identified_type}
- 页数: {state.pages or '未知'}
- 字数: {state.word_count or '未知'}
- 额外信息: {state.extra_info or '无'}

## 候选法务人员
{candidates_desc}

## 负载分析
{state.workload_analysis}

## 决策规则
1. 优先考虑技能匹配度（合同类型与人员擅长类型匹配）
2. 在技能匹配相近时，优先选择负载较低的人员
3. 考虑工作量平衡，避免某人过载

请以JSON格式返回决策结果:
{{
    "staff_name": "推荐的人员姓名",
    "reason": "详细的分派理由",
    "confidence": 0.0到1.0之间的置信度
}}"""

    try:
        result = call_llm(prompt)
        parsed = json.loads(result)
        state.recommended_staff = parsed["staff_name"]
        state.reason = parsed["reason"]
        state.confidence = parsed["confidence"]

        # 查找对应的staff_id
        for c in state.candidates:
            if c["name"] == state.recommended_staff:
                state.staff_id = c["id"]
                break
    except Exception as e:
        print(f"决策失败: {e}")
        # 降级处理: 选择负载最低的
        if state.candidates:
            best = min(state.candidates, key=lambda x: x["current_todo_count"])
            state.recommended_staff = best["name"]
            state.staff_id = best["id"]
            state.reason = "基于负载均衡自动选择"
            state.confidence = 0.5

    return state
