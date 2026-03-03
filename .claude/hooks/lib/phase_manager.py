"""
Phase Manager - 阶段状态管理器
实现 Research → Plan → Execute → Review 的刚性门控
"""

import os
import json
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from enum import Enum


class Phase(Enum):
    """阶段枚举"""
    RESEARCH = "research"
    PLAN = "plan"
    EXECUTE = "execute"
    REVIEW = "review"
    DONE = "done"


@dataclass
class PhaseState:
    """单个阶段的状态"""
    completed: bool = False
    approved_by: Optional[str] = None  # "human" or "agent"
    approved_at: Optional[str] = None
    gates_total: int = 0
    gates_completed: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'PhaseState':
        return cls(
            completed=data.get('completed', False),
            approved_by=data.get('approved_by'),
            approved_at=data.get('approved_at'),
            gates_total=data.get('gates_total', 0),
            gates_completed=data.get('gates_completed', 0)
        )


@dataclass
class TaskPhaseState:
    """任务的完整阶段状态"""
    task_id: str
    current_phase: str  # Phase enum value
    research: PhaseState
    plan: PhaseState
    execute: PhaseState
    review: PhaseState
    created: str
    updated: str

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "current_phase": self.current_phase,
            "research": self.research.to_dict(),
            "plan": self.plan.to_dict(),
            "execute": self.execute.to_dict(),
            "review": self.review.to_dict(),
            "created": self.created,
            "updated": self.updated
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TaskPhaseState':
        return cls(
            task_id=data.get('task_id', ''),
            current_phase=data.get('current_phase', Phase.RESEARCH.value),
            research=PhaseState.from_dict(data.get('research', {})),
            plan=PhaseState.from_dict(data.get('plan', {})),
            execute=PhaseState.from_dict(data.get('execute', {})),
            review=PhaseState.from_dict(data.get('review', {})),
            created=data.get('created', ''),
            updated=data.get('updated', '')
        )


class PhaseManager:
    """阶段状态管理器"""

    PHASE_STATE_FILE = "phase_state.json"

    # 阶段顺序
    PHASE_ORDER = [
        Phase.RESEARCH.value,
        Phase.PLAN.value,
        Phase.EXECUTE.value,
        Phase.REVIEW.value,
        Phase.DONE.value
    ]

    def __init__(self, task_path: str, project_root: Optional[str] = None):
        """
        初始化 PhaseManager

        Args:
            task_path: 任务路径（相对或绝对）
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or os.getcwd())

        # 处理相对路径
        if not os.path.isabs(task_path):
            self.task_path = self.project_root / task_path
        else:
            self.task_path = Path(task_path)

        self.state_file = self.task_path / self.PHASE_STATE_FILE

    def initialize(self, task_id: str) -> TaskPhaseState:
        """
        初始化阶段状态文件

        Args:
            task_id: 任务 ID (如 t1)

        Returns:
            初始化后的 TaskPhaseState
        """
        now = datetime.now().isoformat()

        state = TaskPhaseState(
            task_id=task_id,
            current_phase=Phase.RESEARCH.value,
            research=PhaseState(),
            plan=PhaseState(),
            execute=PhaseState(),
            review=PhaseState(),
            created=now,
            updated=now
        )

        self._save_state(state)
        return state

    def load_state(self) -> Optional[TaskPhaseState]:
        """
        加载阶段状态

        Returns:
            TaskPhaseState 或 None（如果不存在）
        """
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TaskPhaseState.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_state(self, state: TaskPhaseState) -> None:
        """保存阶段状态"""
        state.updated = datetime.now().isoformat()
        self.task_path.mkdir(parents=True, exist_ok=True)

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

    def get_current_phase(self) -> Optional[str]:
        """获取当前阶段"""
        state = self.load_state()
        return state.current_phase if state else None

    def can_proceed_to(self, target_phase: str) -> tuple[bool, str]:
        """
        检查是否可以进入目标阶段

        Args:
            target_phase: 目标阶段

        Returns:
            (是否允许, 原因说明)
        """
        state = self.load_state()
        if not state:
            return False, "阶段状态文件不存在，请先初始化任务"

        current = state.current_phase
        target_idx = self.PHASE_ORDER.index(target_phase) if target_phase in self.PHASE_ORDER else -1
        current_idx = self.PHASE_ORDER.index(current) if current in self.PHASE_ORDER else -1

        # 目标阶段无效
        if target_idx == -1:
            return False, f"无效的阶段: {target_phase}"

        # 已经在目标阶段或更后面的阶段
        if current_idx >= target_idx:
            return True, f"当前已在 {current} 阶段"

        # 检查前置阶段是否完成
        # 要进入 Plan，需要 Research 完成
        if target_phase == Phase.PLAN.value:
            if not state.research.completed:
                return False, "Research 阶段未完成"
            if not state.research.approved_by:
                return False, "Research 阶段未获人类审阅批准"

            # 增强检查：验证 Why Questions 是否已回答
            why_result = self._check_why_questions()
            if not why_result[0]:
                return False, why_result[1]

            # 增强检查：验证 research.md 中的 Review Comments
            rc_result = self._check_review_comments("research.md")
            if not rc_result[0]:
                return False, rc_result[1]

        # 要进入 Execute，需要 Plan 完成
        if target_phase == Phase.EXECUTE.value:
            if not state.plan.completed:
                return False, "Plan 阶段未完成"
            if not state.plan.approved_by:
                return False, "Plan 阶段未获人类审阅批准"

            # 增强检查：验证 plan.md 中的 Review Comments
            rc_result = self._check_review_comments("plan.md")
            if not rc_result[0]:
                return False, rc_result[1]

        # 要进入 Review，需要 Execute 完成
        if target_phase == Phase.REVIEW.value:
            if not state.execute.completed:
                return False, "Execute 阶段未完成"

            # 增强检查：验证代码标注
            code_result = self._check_code_annotations()
            if not code_result[0]:
                return False, code_result[1]

        return True, "可以进入"

    def can_write_code(self) -> tuple[bool, str]:
        """
        检查当前是否允许写入代码文件

        Returns:
            (是否允许, 原因说明)
        """
        state = self.load_state()
        if not state:
            return False, "阶段状态文件不存在"

        current = state.current_phase

        # Research 和 Plan 阶段不允许写代码
        if current == Phase.RESEARCH.value:
            return False, "当前在 Research 阶段，不允许写入代码文件。请先完成 Research 并获得人类审阅批准"

        if current == Phase.PLAN.value:
            return False, "当前在 Plan 阶段，不允许写入代码文件。请先完成 Plan 并获得人类审阅批准"

        # Execute 和 Review 阶段允许写代码
        if current in [Phase.EXECUTE.value, Phase.REVIEW.value]:
            return True, f"当前在 {current} 阶段，允许写入代码"

        if current == Phase.DONE.value:
            return True, "任务已完成，允许写入代码"

        return False, f"未知阶段: {current}"

    def complete_phase(self, phase: str, approved_by: Optional[str] = None) -> bool:
        """
        标记阶段完成并推进到下一阶段

        Args:
            phase: 要完成的阶段
            approved_by: 批准者 ("human" or "agent")

        Returns:
            是否成功
        """
        state = self.load_state()
        if not state:
            return False

        now = datetime.now().isoformat()

        # 更新对应阶段的状态
        phase_state = getattr(state, phase, None)
        if phase_state:
            phase_state.completed = True
            phase_state.approved_by = approved_by
            phase_state.approved_at = now

        # 推进到下一阶段
        current_idx = self.PHASE_ORDER.index(state.current_phase)
        phase_idx = self.PHASE_ORDER.index(phase)

        if phase_idx >= current_idx:
            next_idx = min(phase_idx + 1, len(self.PHASE_ORDER) - 1)
            state.current_phase = self.PHASE_ORDER[next_idx]

        self._save_state(state)
        return True

    def update_gates(self, phase: str, total: int, completed: int) -> bool:
        """
        更新阶段的 Gates 进度

        Args:
            phase: 阶段名称
            total: 总 Gates 数
            completed: 已完成 Gates 数

        Returns:
            是否成功
        """
        state = self.load_state()
        if not state:
            return False

        phase_state = getattr(state, phase, None)
        if phase_state:
            phase_state.gates_total = total
            phase_state.gates_completed = completed

            # 如果所有 Gates 完成，自动标记阶段完成
            if total > 0 and completed >= total:
                phase_state.completed = True

            self._save_state(state)
            return True

        return False

    def get_progress(self) -> Dict:
        """
        获取整体进度

        Returns:
            进度信息字典
        """
        state = self.load_state()
        if not state:
            return {"error": "状态文件不存在"}

        return {
            "task_id": state.task_id,
            "current_phase": state.current_phase,
            "progress": {
                "research": {
                    "completed": state.research.completed,
                    "approved": bool(state.research.approved_by)
                },
                "plan": {
                    "completed": state.plan.completed,
                    "approved": bool(state.plan.approved_by),
                    "gates": f"{state.plan.gates_completed}/{state.plan.gates_total}"
                },
                "execute": {
                    "completed": state.execute.completed,
                    "gates": f"{state.execute.gates_completed}/{state.execute.gates_total}"
                },
                "review": {
                    "completed": state.review.completed
                }
            }
        }

    # ========== Why Questions 检查 ==========

    def _check_why_questions(self) -> Tuple[bool, str]:
        """
        检查 research.md 中的 Why Questions 是否已回答

        Returns:
            (是否通过, 原因说明)
        """
        research_path = self.task_path / "research.md"

        if not research_path.exists():
            return False, "research.md 不存在"

        try:
            # 导入 WhyFirstEngine
            import sys
            hooks_path = self.project_root / '.claude' / 'hooks'
            if str(hooks_path) not in sys.path:
                sys.path.insert(0, str(hooks_path))

            from lib.why_first_engine import WhyFirstEngine

            # 检查 Why Questions 完成情况
            why_engine = WhyFirstEngine(str(self.project_root))
            result = why_engine.check_why_completion(str(self.task_path))

            # 没有 Why Questions 部分
            if not result['has_why_section']:
                return False, "research.md 中缺少 Why Questions 部分"

            # 状态为 pending
            if result['status'] == 'pending':
                unanswered = result.get('unanswered', [])
                if unanswered:
                    return False, f"Why Questions 尚未完成深度思考，未回答: {unanswered[:3]}..."
                else:
                    return False, "Why Questions 尚未完成深度思考，请标记为已回答"

            # 有未回答的问题
            if result['unanswered']:
                return False, f"Why Questions 有 {len(result['unanswered'])} 个问题未回答: {result['unanswered'][:3]}..."

            return True, "Why Questions 检查通过"

        except ImportError:
            # WhyFirstEngine 不可用，跳过检查
            return True, "WhyFirstEngine 不可用，跳过 Why Questions 检查"
        except Exception as e:
            return False, f"检查 Why Questions 时出错: {str(e)}"

    # ========== Review Comments 检查 ==========

    def _check_review_comments(self, filename: str) -> Tuple[bool, str]:
        """
        检查 Markdown 文件中的 Review Comments 状态

        Args:
            filename: 文件名 (research.md 或 plan.md)

        Returns:
            (是否通过, 原因说明)
        """
        file_path = self.task_path / filename

        if not file_path.exists():
            return False, f"{filename} 不存在"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析 Review Comments
            rc_result = self._parse_review_comments(content)

            # 检查是否有 Review Comments（至少需要 1 条表示人类已审阅）
            if rc_result['total'] == 0:
                return False, f"{filename} 中没有任何 Review Comments，请人类先审阅并添加批注"

            # 检查 CRITICAL 和 MAJOR 是否都已处理
            unaddressed_critical = rc_result['critical_pending']
            unaddressed_major = rc_result['major_pending']

            if unaddressed_critical > 0:
                return False, f"{filename} 中有 {unaddressed_critical} 个 CRITICAL Review Comment 未处理"

            if unaddressed_major > 0:
                return False, f"{filename} 中有 {unaddressed_major} 个 MAJOR Review Comment 未处理"

            return True, f"{filename} 审阅通过"

        except Exception as e:
            return False, f"检查 {filename} 时出错: {str(e)}"

    def _parse_review_comments(self, content: str) -> Dict:
        """
        解析 Markdown 内容中的 Review Comments

        支持两种格式：

        格式 1（引用块格式，推荐）:
        ### RC-1: 标题
        > 严重程度: [CRITICAL/MAJOR/MINOR/SUGGEST]
        > 状态: [pending/addressed/pending_ai_question]

        格式 2（列表格式，向后兼容）:
        ### RC-1: 标题
        - **类型**: CRITICAL/MAJOR/MINOR/SUGGEST
        - **状态**: pending/addressed/pending_ai_question

        Returns:
            {
                'total': 总数,
                'critical_pending': CRITICAL 未处理数,
                'major_pending': MAJOR 未处理数,
                'comments': [...]
            }
        """
        result = {
            'total': 0,
            'critical_pending': 0,
            'major_pending': 0,
            'comments': []
        }

        # 匹配 RC 块：### RC-N: ... 到下一个 ### RC- 或 --- 或 ## 或文档结束
        rc_pattern = r'### (RC-\d+[^\\n]*):.*?(?=### RC-|\n---\n|\n## |\Z)'

        for match in re.finditer(rc_pattern, content, re.DOTALL):
            block_text = match.group(0)
            rc_id = match.group(1).strip()
            result['total'] += 1

            # 提取严重程度 - 支持多种格式
            severity = 'MINOR'  # 默认值

            # 格式 1: > 严重程度: [CRITICAL]
            severity_match = re.search(r'严重程度[:\s]*\[?(CRITICAL|MAJOR|MINOR|SUGGEST)\]?', block_text, re.IGNORECASE)
            if severity_match:
                severity = severity_match.group(1).upper()
            else:
                # 格式 2: - **类型**: CRITICAL 或 类型: CRITICAL
                severity_match = re.search(r'(?:类型|type)[:\s]*\*?\*?(CRITICAL|MAJOR|MINOR|SUGGEST)', block_text, re.IGNORECASE)
                if severity_match:
                    severity = severity_match.group(1).upper()

            # 提取状态 - 支持多种格式
            status = 'pending'  # 默认值

            # 格式 1: > 状态: [pending]
            status_match = re.search(r'状态[:\s]*\[?(pending|addressed|pending_ai_question)\]?', block_text, re.IGNORECASE)
            if status_match:
                status = status_match.group(1).lower()
            else:
                # 格式 2: - **状态**: pending
                status_match = re.search(r'(?:状态|status)[:\s]*\*?\*?(pending|addressed|pending_ai_question)', block_text, re.IGNORECASE)
                if status_match:
                    status = status_match.group(1).lower()

            # 检查是否是 pending 状态
            is_pending = status in ['pending', 'pending_ai_question']

            if is_pending:
                if severity == 'CRITICAL':
                    result['critical_pending'] += 1
                elif severity == 'MAJOR':
                    result['major_pending'] += 1

            result['comments'].append({
                'id': rc_id,
                'severity': severity,
                'status': status,
                'pending': is_pending
            })

        return result

    def _check_code_annotations(self) -> Tuple[bool, str]:
        """
        检查代码标注中是否有未处理的 CRITICAL/MAJOR

        Returns:
            (是否通过, 原因说明)
        """
        annotations_file = self.task_path / '.annotations' / 'code.json'

        if not annotations_file.exists():
            # 没有代码标注，允许通过
            return True, "没有代码标注"

        try:
            with open(annotations_file, 'r', encoding='utf-8') as f:
                all_annotations = json.load(f)

            critical_pending = 0
            major_pending = 0

            for file_path, file_annotations in all_annotations.items():
                for line_num, annotation in file_annotations.items():
                    severity = annotation.get('type', annotation.get('severity', 'MINOR'))
                    status = annotation.get('status', 'pending')

                    if status.lower() in ['pending', 'pending_ai_question']:
                        if severity == 'CRITICAL':
                            critical_pending += 1
                        elif severity == 'MAJOR':
                            major_pending += 1

            if critical_pending > 0:
                return False, f"代码标注中有 {critical_pending} 个 CRITICAL 未处理"

            if major_pending > 0:
                return False, f"代码标注中有 {major_pending} 个 MAJOR 未处理"

            return True, "代码标注检查通过"

        except Exception as e:
            return False, f"检查代码标注时出错: {str(e)}"

    def get_review_status(self) -> Dict:
        """
        获取审阅状态摘要

        Returns:
            审阅状态信息
        """
        result = {
            'research': {'has_rc': False, 'critical_pending': 0, 'major_pending': 0},
            'plan': {'has_rc': False, 'critical_pending': 0, 'major_pending': 0},
            'code': {'has_annotations': False, 'critical_pending': 0, 'major_pending': 0}
        }

        # 检查 research.md
        research_path = self.task_path / 'research.md'
        if research_path.exists():
            with open(research_path, 'r', encoding='utf-8') as f:
                rc = self._parse_review_comments(f.read())
            result['research'] = {
                'has_rc': rc['total'] > 0,
                'critical_pending': rc['critical_pending'],
                'major_pending': rc['major_pending'],
                'total': rc['total']
            }

        # 检查 plan.md
        plan_path = self.task_path / 'plan.md'
        if plan_path.exists():
            with open(plan_path, 'r', encoding='utf-8') as f:
                rc = self._parse_review_comments(f.read())
            result['plan'] = {
                'has_rc': rc['total'] > 0,
                'critical_pending': rc['critical_pending'],
                'major_pending': rc['major_pending'],
                'total': rc['total']
            }

        # 检查代码标注
        annotations_file = self.task_path / '.annotations' / 'code.json'
        if annotations_file.exists():
            try:
                with open(annotations_file, 'r', encoding='utf-8') as f:
                    all_annotations = json.load(f)

                critical_pending = 0
                major_pending = 0
                total = 0

                for file_path, file_annotations in all_annotations.items():
                    for line_num, annotation in file_annotations.items():
                        total += 1
                        severity = annotation.get('type', annotation.get('severity', 'MINOR'))
                        status = annotation.get('status', 'pending')

                        if status.lower() in ['pending', 'pending_ai_question']:
                            if severity == 'CRITICAL':
                                critical_pending += 1
                            elif severity == 'MAJOR':
                                major_pending += 1

                result['code'] = {
                    'has_annotations': total > 0,
                    'critical_pending': critical_pending,
                    'major_pending': major_pending,
                    'total': total
                }
            except:
                pass

        return result


def check_phase_for_file(task_path: str, file_path: str, project_root: str = None) -> tuple[bool, str]:
    """
    便捷函数：检查是否允许写入指定文件

    Args:
        task_path: 任务路径
        file_path: 要写入的文件路径
        project_root: 项目根目录

    Returns:
        (是否允许, 原因说明)
    """
    # 代码文件扩展名
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.vue', '.svelte'
    }

    # 非代码文件直接允许
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in CODE_EXTENSIONS:
        return True, "非代码文件，不受阶段限制"

    # 检查阶段状态
    manager = PhaseManager(task_path, project_root)
    state = manager.load_state()

    if not state:
        # 没有状态文件，可能是旧任务，允许写入（向后兼容）
        return True, "未找到阶段状态文件（向后兼容模式）"

    return manager.can_write_code()
