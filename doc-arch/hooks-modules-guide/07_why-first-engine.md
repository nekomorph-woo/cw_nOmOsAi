# Why-First 引擎详解

**文档版本**: 2.0
**最后更新**: 2026-03-02
**作者**: Claude Opus 4.6

---

## 1. 概述

### 1.1 设计理念

Why-First 引擎是 nOmOsAi 系统的"深度思考"模块，其核心设计理念是 **"强制 AI 在动手前先思考为什么"**。

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Why-First 设计理念                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  传统 AI 编码模式（"想当然"模式）:                                    │
│  用户需求 → AI 立即开始写代码 → 发现问题 → 增量修补 → 越改越乱        │
│                                                                      │
│  nOmOsAi Why-First 模式（深度思考模式）:                              │
│  用户需求 → Why 问题生成 → 深度思考 → 知识沉淀 → Research → ...      │
│              ↑                              │                        │
│              └──────── 从 project-why.md 加载历史 ────┘              │
│                                                                      │
│  核心价值:                                                           │
│  - 避免幻觉: 强制 AI 思考而非假设                                     │
│  - 知识沉淀: 每次任务的"为什么"都沉淀到 project-why.md               │
│  - 避免重复错误: 历史教训自动加载到上下文                            │
│  - 提升质量: 前置思考减少后期返工                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心功能

| 功能 | 说明 | 实现状态 |
|------|------|----------|
| **AI 增强问题生成** | 使用 AI 生成 5-8 个针对性问题 | ✅ 已实现 |
| **模板降级问题生成** | AI 不可用时降级到固定模板 | ✅ 已实现 |
| **知识库管理** | 维护 project-why.md 知识库 | ✅ 已实现 |
| **AI 辅助知识库维护** | AI 自动决策 add/enhance/merge | ✅ 已实现 |
| **相似检测** | 检测新知识与已有条目的相似度 | ✅ 已实现 |
| **知识增强** | 在现有条目基础上补充信息 | ✅ 已实现 |
| **问题注入** | 将 Why 问题注入到 research.md | ✅ 已实现 |
| **完成度检查** | 检查 Why Questions 回答情况 | ✅ 已实现 |

### 1.3 与 Phase Gates 的关系

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Why-First 在 Phase Gates 中的位置                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐        │
│  │  Why-First    │───►│   Research    │───►│     Plan      │        │
│  │   (内嵌阶段)   │    │   (调研阶段)   │    │   (计划阶段)   │        │
│  └───────────────┘    └───────────────┘    └───────────────┘        │
│         │                                                              │
│         │                                                              │
│         ▼                                                              │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │ Why-First 是 Research 阶段的第一个步骤:                         │   │
│  │ 1. inject_questions_to_research() 注入 Why 问题               │   │
│  │ 2. Agent 在 research.md 回答问题                               │   │
│  │ 3. mark_why_questions_answered() 标记完成                     │   │
│  │ 4. add_knowledge() 沉淀重要决策                                │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构设计

### 2.1 架构定位

Why-First 引擎在 nOmOsAi 系统架构中的位置：

```
┌─────────────────────────────────────────────────────────────────────┐
│                      用户交互层                                      │
│  (Claude Code CLI / Task Viewer HTML 界面)                          │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      SKILL 编排层                                    │
│  (/nomos 主 SKILL + 子 SKILL)                                        │
│  ├── /nomos:start      → 启动完整流程（包含 Why-First）             │
│  └── /nomos:update-why → 更新 project-why.md                        │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    【Why-First 引擎在此层】                          │
│                      知识管理层                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ WhyFirstEngine                                                 │ │
│  │ ├── generate_why_questions()    → 生成 Why 问题（AI 增强）     │ │
│  │ ├── inject_questions_to_research() → 注入问题到 research.md   │ │
│  │ ├── check_why_completion()      → 检查完成情况                 │ │
│  │ ├── mark_why_questions_answered() → 标记已回答                 │ │
│  │ ├── add_knowledge()             → 添加知识条目                 │ │
│  │ ├── search_knowledge()          → 搜索知识库                   │ │
│  │ ├── detect_similar_knowledge()  → 检测相似条目                 │ │
│  │ ├── ai_suggest_knowledge_operation() → AI 辅助决策             │ │
│  │ ├── execute_knowledge_operation() → 执行知识库操作             │ │
│  │ └── enhance_knowledge()         → 增强现有条目                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      状态持久化层                                    │
│  ├── project-why.md          ← 【知识库文件】                       │
│  └── tasks/t{N}-{date}-{name}/                                      │
│       └── research.md         ← Why 问题回答                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 依赖关系

```
┌─────────────────────────────────────────────────────────────────────┐
│                      WhyFirstEngine 依赖                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  外部依赖:                                                           │
│  ├── lib.core.AIClient   → AI 模型调用（用于增强功能）              │
│  └── difflib.SequenceMatcher → 文本相似度计算                       │
│                                                                      │
│  文件依赖:                                                           │
│  ├── project-why.md      → 知识库（可不存在，会降级）               │
│  └── tasks/{task}/research.md → Why 问题存储（必须存在）            │
│                                                                      │
│  降级策略:                                                           │
│  ├── AI 不可用 → 降级到固定模板问题                                 │
│  └── 知识库不存在 → 返回空列表/False                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 知识库结构设计

**project-why.md 文件结构**:

```markdown
---
project: nOmOsAi
created: 2026-02-26
version: 0.1.0
status: active
---

# Project Why - nOmOsAi 项目知识库

本文档记录项目的核心决策、经验教训和重要知识。

## 核心理念

### 为什么需要 nOmOsAi？

**时间**: 2026-02-26

[核心动机和价值的详细描述...]

## 架构决策

### 为什么选择 Markdown 作为状态存储？

**时间**: 2026-02-25

**原因**: Markdown 人类可读、Git 友好、跨会话持久化

**相关代码**: .claude/hooks/lib/

**最后更新**: 2026-02-26

**状态**: 仍有效

## 经验教训

### 2026-02-25: 必须走 Repository 层

**时间**: 2026-02-25

**错误**: 尝试直接调用 ORM 而非 Repository

**原因**: 未注意到事务管理依赖 Repository 层

**教训**: 所有数据访问必须通过 Repository 层

**补充** (2026-02-26):
增加了缓存层后，Repository 层的重要性更加突出

## 常见问题

### 如何处理跨模块依赖？

**时间**: 2026-02-25

[解决方案描述...]
```

---

## 3. 代码实现详解

### 3.1 文件结构

```
.claude/hooks/lib/
├── why_first_engine.py       # 核心 Why-First 引擎
├── core.py                   # AIClient 所在位置
└── ...

.claude/skills/nomos/prompts/
├── start.md                  # 任务启动流程（包含 Why-First）
└── update-why.md             # project-why.md 维护 prompt
```

### 3.2 WhyFirstEngine 类结构

**文件位置**: `.claude/hooks/lib/why_first_engine.py`

```python
class WhyFirstEngine:
    """Why-First 引擎"""

    # AI 生成问题的 Prompt 模板
    AI_QUESTION_PROMPT = """你是深度思考助手。请为以下任务生成 5-8 个"Why"问题。
    ...
    """

    # AI 知识库操作建议的 Prompt 模板
    AI_KNOWLEDGE_PROMPT = """你是知识库管理助手。请分析新知识并决定最佳操作。
    ...
    """

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化 Why-First 引擎

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or os.getcwd())
        self.project_why_file = self.project_root / 'project-why.md'
        self._ai_client = None  # 懒加载
```

**设计特点**:

- **懒加载 AI 客户端**: 通过 `@property` 懒加载，避免不必要的初始化
- **降级设计**: 所有 AI 功能都有降级方案
- **路径灵活性**: 支持自定义项目根目录

### 3.3 AI 增强问题生成

**代码位置**: `why_first_engine.py:54-132`

#### 3.3.1 主入口方法

```python
def generate_why_questions(self, task_name: str, description: str,
                           use_ai: bool = True) -> Dict[str, any]:
    """
    生成 Why 问题（AI 增强）

    Args:
        task_name: 任务名称
        description: 任务描述
        use_ai: 是否使用 AI 增强

    Returns:
        {
            'questions': List[str],  # 问题列表
            'source': str,           # 'ai_generated' 或 'template'
            'ai_available': bool     # AI 是否可用
        }
    """
    # 尝试 AI 生成
    if use_ai and self.ai_client and self.ai_client.available:
        result = self._generate_ai_questions(task_name, description)
        if result['questions']:
            return result

    # 降级到固定模板
    return {
        'questions': self._generate_template_questions(task_name),
        'source': 'template',
        'ai_available': self.ai_client.available if self.ai_client else False
    }
```

#### 3.3.2 AI 生成逻辑

```python
def _generate_ai_questions(self, task_name: str, description: str) -> Dict[str, any]:
    """使用 AI 生成针对性问题"""
    # 收集历史上下文
    historical = self.search_knowledge(task_name)
    recent = self.get_recent_knowledge(limit=3)

    # 构建历史上下文
    historical_context = ""
    if historical or recent:
        context_parts = ["相关历史决策:"]
        for item in (historical[:2] + recent)[:3]:
            context_parts.append(f"- {item['title']}: {item['content'][:100]}...")
        historical_context = "\n".join(context_parts)
    else:
        historical_context = "（暂无相关历史决策）"

    # 构建 Prompt 并调用 AI
    prompt = self.AI_QUESTION_PROMPT.format(...)
    result = self.ai_client.call(prompt, "", max_tokens=1024)

    # 过滤和清理问题
    questions = [q.strip() for q in questions if q and len(q.strip()) > 5]
    questions = questions[:8]  # 限制数量

    return {'questions': questions, 'source': 'ai_generated', 'ai_available': True}
```

**AI 问题生成 Prompt 模板**:

```python
AI_QUESTION_PROMPT = """你是深度思考助手。请为以下任务生成 5-8 个"Why"问题。

任务名称: {task_name}
任务描述: {description}

{historical_context}

要求:
1. 问题应基于任务描述的具体内容，避免泛泛而谈
2. 参考历史决策，生成针对性的对比问题
3. 问题应涵盖: 核心动机、方案选择、潜在风险、依赖关系
4. 返回 JSON 格式: {{"questions": ["问题1", "问题2", ...]}}
5. 问题应该是开放式的，引导深度思考
6. 问题数量控制在 5-8 个"""
```

#### 3.3.3 模板降级方案

```python
def _generate_template_questions(self, task_name: str) -> List[str]:
    """生成固定模板问题（降级方案）"""
    return [
        f"为什么需要 {task_name}？",
        f"为什么现在做 {task_name}？",
        f"为什么选择这种方式实现 {task_name}？",
        f"为什么不用其他方案？",
        f"{task_name} 的核心价值是什么？"
    ]
```

**问题维度分析**:

| 问题 | 维度 | 目的 |
|------|------|------|
| "为什么需要" | 核心动机 | 确认功能必要性 |
| "为什么现在做" | 时机选择 | 评估优先级 |
| "为什么选择这种方式" | 方案选择 | 验证技术决策 |
| "为什么不用其他方案" | 替代分析 | 避免遗漏更好方案 |
| "核心价值是什么" | 价值主张 | 明确成功标准 |

### 3.4 Why Questions 注入与验证

#### 3.4.1 问题注入

**代码位置**: `why_first_engine.py:580-688`

```python
def inject_questions_to_research(self, task_path: str,
                                 questions: any = None,
                                 source: str = "template",
                                 task_name: str = None,
                                 description: str = None,
                                 use_ai: bool = True) -> Dict[str, any]:
    """
    将 Why 问题注入到 research.md

    支持两种调用方式：
    1. 传入 questions 列表：直接注入
    2. 传入 task_name + description：自动生成并注入

    Returns:
        {
            'success': bool,
            'questions': List[str],
            'source': str,
            'ai_available': bool,
            'count': int
        }
    """
```

**注入后的 research.md 格式**:

```markdown
## 4. Why Questions

> **状态**: [pending]
> **生成时间**: 2026-03-02 10:30
> **来源**: ai_generated
> **问题数量**: 5

### 4.1 为什么需要 user-login？

（请在此回答）

### 4.2 为什么现在做 user-login？

（请在此回答）

...
```

#### 3.4.2 完成度检查

**代码位置**: `why_first_engine.py:747-821`

```python
def check_why_completion(self, task_path: str) -> Dict[str, any]:
    """
    检查 Why Questions 完成情况

    Returns:
        {
            'has_why_section': bool,
            'status': 'pending' | 'answered' | 'missing',
            'total_questions': int,
            'answered_questions': int,
            'unanswered': List[str]
        }
    """
```

**检查逻辑**:
- 提取 `## 4. Why Questions` 部分
- 检查状态标记（pending/answered）
- 统计问题总数和已回答数
- 识别未回答的问题（内容少于 10 字符或为占位符）

#### 3.4.3 标记已回答

**代码位置**: `why_first_engine.py:713-745`

```python
def mark_why_questions_answered(self, task_path: str) -> bool:
    """标记 Why Questions 已回答"""
    # 更新状态标记: [pending] → [answered]
    new_content = re.sub(
        r'> \*\*状态\*\*: \[pending\]',
        '> **状态**: [answered]',
        content
    )
```

### 3.5 知识库管理

#### 3.5.1 添加知识条目

**代码位置**: `why_first_engine.py:144-209`

```python
def add_knowledge(self, category: str, title: str, content: str) -> bool:
    """
    添加知识到 project-why.md

    Args:
        category: 分类（核心理念/架构决策/经验教训/常见问题）
        title: 标题
        content: 内容
    """
```

**支持的分类**:

| 分类 | 用途 | 示例 |
|------|------|------|
| **核心理念** | 项目的核心价值观和设计理念 | "为什么需要 nOmOsAi" |
| **架构决策** | 重要的技术架构决策及其理由 | "为什么选择 Hooks 而非 Prompt" |
| **经验教训** | 失败案例和学到的教训 | "必须走 Repository 层" |
| **常见问题** | 常见问题及解决方案 | "如何处理跨模块依赖" |

#### 3.5.2 搜索知识

**代码位置**: `why_first_engine.py:211-241`

```python
def search_knowledge(self, keyword: str) -> List[Dict[str, str]]:
    """搜索知识库（大小写不敏感）"""
    sections = re.split(r'\n### ', content)
    # 基于 ### 标题分节，返回匹配的条目
```

#### 3.5.3 获取最近知识

**代码位置**: `why_first_engine.py:243-280`

```python
def get_recent_knowledge(self, limit: int = 5) -> List[Dict[str, str]]:
    """获取最近的知识条目（按时间排序）"""
    # 提取 **时间**: YYYY-MM-DD 格式的时间戳
    # 按时间倒序排列
```

### 3.6 AI 辅助知识库维护

#### 3.6.1 AI 操作建议

**代码位置**: `why_first_engine.py:434-503`

```python
def ai_suggest_knowledge_operation(self, new_knowledge: str,
                                    threshold: float = 0.6) -> Dict[str, any]:
    """
    AI 辅助决策知识库操作

    Returns:
        {
            'operation': 'add' | 'enhance' | 'merge',
            'target': None | {'title': str, 'similarity': float},
            'reason': str,
            'suggested_content': str,
            'ai_available': bool
        }
    """
```

**AI 知识库操作 Prompt 模板**:

```python
AI_KNOWLEDGE_PROMPT = """你是知识库管理助手。请分析新知识并决定最佳操作。

新知识:
{new_knowledge}

相似的历史知识:
{similar_knowledge}

请返回 JSON 格式:
{{
    "operation": "add" | "enhance" | "merge",
    "target_title": "目标条目标题（enhance/merge 时填写）" 或 null,
    "reason": "决策理由（一句话说明为什么选择这个操作）",
    "suggested_content": "建议的内容（如需合并则提供合并后内容，如需增强则提供补充内容）"
}}

操作说明:
- add: 创建新条目（内容完全不相关或相似度很低）
- enhance: 增强现有条目（相似度较高，应补充而非创建）
- merge: 合并条目（多个条目讨论同一主题）"""
```

#### 3.6.2 降级决策逻辑

**代码位置**: `why_first_engine.py:505-543`

```python
def _fallback_knowledge_operation(self, new_knowledge: str,
                                   similar: List[Dict]) -> Dict[str, any]:
    """降级：基于相似度的知识库操作决策"""
    if not similar:
        return {'operation': 'add', ...}

    similarity = similar[0]['similarity']

    if similarity > 0.8:
        return {'operation': 'enhance', ...}  # 增强现有条目
    elif similarity > 0.6:
        return {'operation': 'merge', ...}   # 建议合并
    else:
        return {'operation': 'add', ...}     # 创建新条目
```

#### 3.6.3 执行知识库操作

**代码位置**: `why_first_engine.py:545-576`

```python
def execute_knowledge_operation(self, operation: str, category: str,
                                title: str, content: str,
                                target: Dict = None) -> bool:
    """执行知识库操作"""
    if operation == 'add':
        return self.add_knowledge(category, title, content)
    elif operation == 'enhance':
        return self.enhance_knowledge(target['title'], content)
    elif operation == 'merge':
        merged_content = f"**合并内容**:\n\n{content}"
        return self.enhance_knowledge(target['title'], merged_content)
```

### 3.7 知识相似度检测

#### 3.7.1 相似度计算

**代码位置**: `why_first_engine.py:344-355`

```python
def _calculate_similarity(self, text1: str, text2: str) -> float:
    """计算文本相似度（0-1）"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
```

**算法说明**:
- 使用 Python 标准库 `difflib.SequenceMatcher`
- 基于 longest common subsequence 算法
- 大小写不敏感

#### 3.7.2 相似条目检测

**代码位置**: `why_first_engine.py:304-342`

```python
def detect_similar_knowledge(self, new_content: str, threshold: float = 0.7) -> List[Dict[str, any]]:
    """检测相似的知识条目"""
    # 遍历所有 ### 条目
    # 计算相似度
    # 返回超过阈值的条目（按相似度排序）
```

**相似度阈值建议**:

| 相似度范围 | 建议操作 |
|-----------|---------|
| > 0.8 | 增强现有条目（添加补充信息） |
| 0.6-0.8 | 考虑合并条目 |
| < 0.6 | 创建新条目 |

### 3.8 知识增强

**代码位置**: `why_first_engine.py:374-408`

```python
def enhance_knowledge(self, title: str, additional_info: str) -> bool:
    """增强现有知识条目"""
    # 在条目末尾添加:
    # **补充** (YYYY-MM-DD):
    # {additional_info}
```

**增强格式示例**:

```markdown
### 为什么选择 Markdown 作为状态存储？

**时间**: 2026-02-25

**原因**: Markdown 人类可读、Git 友好、跨会话持久化

**补充** (2026-02-26):
经过一周使用，发现 Markdown 的另一个优势：
支持在 IDE 中直接预览和编辑，无需额外工具
```

---

## 4. 设计 vs 实现对比

### 4.1 完成度分析

```
┌─────────────────────────────────────────────────────────────────────┐
│                     设计 vs 实现对比                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  核心功能                                                            │
│  ├── Why 问题生成（AI 增强）  ✅ 已实现（含降级方案）                │
│  ├── Why 问题注入到 research  ✅ 已实现                              │
│  ├── 完成度检查               ✅ 已实现                              │
│  ├── 知识库添加               ✅ 已实现                              │
│  ├── 知识库搜索               ✅ 已实现                              │
│  ├── 相似度检测               ✅ 已实现                              │
│  ├── 知识增强                 ✅ 已实现                              │
│  ├── 知识合并建议             ✅ 已实现                              │
│  ├── AI 辅助知识库维护        ✅ 已实现（含降级方案）                │
│  └── 执行知识库操作           ✅ 已实现                              │
│                                                                      │
│  降级策略                                                            │
│  ├── AI 不可用时               ✅ 降级到模板问题                     │
│  ├── 知识库不存在时            ✅ 返回空列表/False                   │
│  └── AI 调用失败时             ✅ 基于相似度决策                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 实现亮点

| 特性 | 说明 |
|------|------|
| **AI 增强** | 问题生成和知识库维护都支持 AI 增强 |
| **优雅降级** | AI 不可用时自动降级到模板/规则决策 |
| **历史上下文** | AI 生成问题时会加载相关历史决策 |
| **完整流程** | 从问题生成到完成检查的完整闭环 |
| **状态追踪** | pending/answered 状态标记 |

### 4.3 待优化方向

| 方向 | 说明 |
|------|------|
| **代码扫描集成** | 基于受影响文件生成针对性问题 |
| **知识图谱** | 构建知识条目之间的关联关系 |
| **自动合并** | 当前合并是简化实现，可优化 |

---

## 5. 使用流程图

### 5.1 Why-First 完整流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Why-First 完整流程                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户执行 /nomos:start <任务名>                                      │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 1: 生成并注入 Why 问题                                     ││
│  │                                                                 ││
│  │ why_engine = WhyFirstEngine()                                  ││
│  │ result = why_engine.inject_questions_to_research(              ││
│  │     task_path=str(task.path),                                  ││
│  │     task_name="任务名",                                        ││
│  │     description="任务描述",                                    ││
│  │     use_ai=True  # AI 不可用时自动降级                         ││
│  │ )                                                              ││
│  │                                                                 ││
│  │ print(f"来源: {result['source']} (AI: {result['ai_available']})")│
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 2: 在 research.md 中回答 Why 问题                          ││
│  │                                                                 ││
│  │ ## 4. Why Questions                                             ││
│  │ > **状态**: [pending]                                           ││
│  │                                                                 ││
│  │ ### 4.1 为什么需要 {任务名}？                                   ││
│  │ [Agent 回答...]                                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 3: 标记 Why Questions 已回答                               ││
│  │                                                                 ││
│  │ why_engine.mark_why_questions_answered(str(task.path))          ││
│  │ # research.md 中: [pending] → [answered]                        ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 4: AI 辅助沉淀知识到 project-why.md                        ││
│  │                                                                 ││
│  │ # AI 自动决策最佳操作                                           ││
│  │ suggestion = why_engine.ai_suggest_knowledge_operation(         ││
│  │     new_knowledge=lesson_content                                ││
│  │ )                                                              ││
│  │                                                                 ││
│  │ # 执行建议的操作                                                ││
│  │ why_engine.execute_knowledge_operation(                         ││
│  │     operation=suggestion['operation'],                          ││
│  │     category="架构决策",                                        ││
│  │     title="决策标题",                                           ││
│  │     content=suggestion['suggested_content'],                    ││
│  │     target=suggestion['target']                                 ││
│  │ )                                                              ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 5: 进入 Research 阶段                                      ││
│  │                                                                 ││
│  │ 继续调研相关代码、识别 Protected Interfaces 等                   ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 AI 辅助知识库更新流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AI 辅助知识库更新流程                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Agent 准备更新 project-why.md                                       │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 1: AI 辅助决策                                             ││
│  │                                                                 ││
│  │ suggestion = why_engine.ai_suggest_knowledge_operation(         ││
│  │     new_knowledge=new_content                                   ││
│  │ )                                                              ││
│  │                                                                 ││
│  │ # AI 可用时: 分析内容并建议 add/enhance/merge                   ││
│  │ # AI 不可用时: 基于相似度自动决策                               ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 2: 执行建议的操作                                          ││
│  │                                                                 ││
│  │ success = why_engine.execute_knowledge_operation(               ││
│  │     operation=suggestion['operation'],                          ││
│  │     category="架构决策",                                        ││
│  │     title="新知识标题",                                         ││
│  │     content=suggestion['suggested_content'],                    ││
│  │     target=suggestion['target']                                 ││
│  │ )                                                              ││
│  │                                                                 ││
│  │ ┌─────────────────────────────────────────────────────────────┐ ││
│  │ │ operation = 'add'                                           │ ││
│  │ │ → 创建新条目                                                │ ││
│  │ └─────────────────────────────────────────────────────────────┘ ││
│  │ ┌─────────────────────────────────────────────────────────────┐ ││
│  │ │ operation = 'enhance'                                       │ ││
│  │ │ → 在现有条目末尾添加补充信息                                │ ││
│  │ └─────────────────────────────────────────────────────────────┘ ││
│  │ ┌─────────────────────────────────────────────────────────────┐ ││
│  │ │ operation = 'merge'                                         │ ││
│  │ │ → 合并内容到现有条目                                        │ ││
│  │ └─────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. 使用示例

### 6.1 一键注入 Why 问题（推荐）

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.why_first_engine import WhyFirstEngine

why_engine = WhyFirstEngine()

# 一键生成并注入（自动使用 AI，失败时降级到模板）
result = why_engine.inject_questions_to_research(
    task_path="tasks/t1-2026-03-02-user-login",
    task_name="user-login",
    description="实现用户登录认证功能，支持 JWT Token",
    use_ai=True  # AI 不可用时自动降级
)

print(f"✅ 已生成 {result['count']} 个 Why 问题")
print(f"   来源: {result['source']} (AI {'可用' if result['ai_available'] else '不可用'})")
```

**输出**:
```
✅ 已生成 6 个 Why 问题
   来源: ai_generated (AI 可用)
```

### 6.2 仅生成 Why 问题

```python
# 仅生成问题（不注入）
result = why_engine.generate_why_questions(
    "user-login",
    "实现用户登录认证功能",
    use_ai=True
)

print(f"来源: {result['source']}")
for i, q in enumerate(result['questions'], 1):
    print(f"  {i}. {q}")
```

### 6.3 检查 Why 完成情况

```python
# 检查完成情况
status = why_engine.check_why_completion("tasks/t1-2026-03-02-user-login")

print(f"状态: {status['status']}")
print(f"进度: {status['answered_questions']}/{status['total_questions']}")

if status['unanswered']:
    print("未回答的问题:")
    for q in status['unanswered']:
        print(f"  - {q}")
```

### 6.4 AI 辅助添加知识

```python
# AI 自动决策最佳操作
new_knowledge = """
用户认证使用 JWT Token 而非 Session。
原因: 需要支持分布式部署和无状态认证。
JWT 更适合移动端 API 调用场景。
"""

suggestion = why_engine.ai_suggest_knowledge_operation(new_knowledge)

print(f"🤖 AI 建议: {suggestion['operation']}")
print(f"   理由: {suggestion['reason']}")

if suggestion['target']:
    print(f"   目标: {suggestion['target']['title']}")
    print(f"   相似度: {suggestion['target']['similarity']:.2%}")

# 执行建议的操作
success = why_engine.execute_knowledge_operation(
    operation=suggestion['operation'],
    category="架构决策",
    title="为什么选择 JWT 认证",
    content=suggestion['suggested_content'],
    target=suggestion['target']
)
```

### 6.5 手动添加知识

```python
# 直接添加新条目
success = why_engine.add_knowledge(
    category="架构决策",
    title="为什么选择 JWT 而非 Session",
    content="""
**原因**: 需要支持分布式部署和无状态认证

**备选方案**:
- Session: 需要共享存储，增加复杂度
- JWT: 无状态，易于扩展

**决策**: 选择 JWT

**相关代码**: src/auth/jwt_service.py
"""
)
```

### 6.6 增强现有知识

```python
# 增强现有条目
success = why_engine.enhance_knowledge(
    title="为什么选择 JWT 而非 Session",
    additional_info="""
补充：考虑到移动端 API 调用场景，JWT 更适合无状态架构。
此外，JWT 支持自定义 Claims，可以在 Token 中携带用户角色信息。
"""
)
```

---

## 7. 与其他模块的协作

### 7.1 与 Phase Gates 的协作

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Why-First 与 Phase Gates 协作                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  /nomos:start                                                        │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Research 阶段                                                   ││
│  │                                                                 ││
│  │ ┌─────────────────────────────────────────────────────────────┐ ││
│  │ │ Why-First 子阶段                                             │ ││
│  │ │ - inject_questions_to_research()                            │ ││
│  │ │ - 回答 Why 问题                                              │ ││
│  │ │ - mark_why_questions_answered()                             │ ││
│  │ │ - ai_suggest_knowledge_operation()                          │ ││
│  │ └─────────────────────────────────────────────────────────────┘ ││
│  │                         │                                       ││
│  │                         ▼                                       ││
│  │ ┌─────────────────────────────────────────────────────────────┐ ││
│  │ │ 代码调研子阶段                                               │ ││
│  │ │ - 扫描相关代码                                               │ ││
│  │ │ - 识别 Protected Interfaces                                  │ ││
│  │ └─────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  PhaseManager.complete_phase("research", approved_by="human")       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 与 Revert Manager 的协作

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Why-First 与 Revert Manager 协作                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Revert 触发                                                        │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Revert Manager 执行                                             ││
│  │ - git revert HEAD --no-edit                                     ││
│  │ - 记录到 code_review.md                                         ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Why-First 记录教训（AI 辅助）                                   ││
│  │                                                                 ││
│  │ suggestion = why_engine.ai_suggest_knowledge_operation(         ││
│  │     f"失败教训: {revert_reason}"                                ││
│  │ )                                                              ││
│  │ why_engine.execute_knowledge_operation(                         ││
│  │     operation=suggestion['operation'],                          ││
│  │     category="经验教训",                                        ││
│  │     ...                                                        ││
│  │ )                                                              ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 回到 Plan 阶段                                                  ││
│  │ - generate_why_questions() 会加载历史教训                       ││
│  │ - 重新设计方案                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 与 AIClient 的协作

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Why-First 与 AIClient 协作                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  WhyFirstEngine                                                     │
│         │                                                            │
│         │ @property ai_client (懒加载)                              │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ lib.core.AIClient                                               ││
│  │                                                                 ││
│  │ 属性:                                                           ││
│  │ - available: bool  → AI 是否可用                                ││
│  │                                                                 ││
│  │ 方法:                                                           ││
│  │ - call(prompt, context, max_tokens) → Dict                     ││
│  │                                                                 ││
│  │ 降级处理:                                                       ││
│  │ - AI 不可用时 available = False                                ││
│  │ - 调用失败时抛出异常                                            ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  WhyFirstEngine 的降级策略:                                         │
│  ├── generate_why_questions: AI 失败 → 模板问题                     │
│  ├── ai_suggest_knowledge_operation: AI 失败 → 相似度决策           │
│  └── 所有方法都有非 AI 的备选方案                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. 总结

### 8.1 核心价值

Why-First 引擎是 nOmOsAi 系统的"深度思考"模块，通过以下方式提升 AI 编码质量：

1. **强制深度思考**: 通过 Why 问题迫使 AI 在动手前思考
2. **AI 增强生成**: 利用 AI 生成针对性问题，而非固定模板
3. **历史上下文**: 自动加载相关历史决策作为上下文
4. **知识沉淀**: 每次任务的决策和教训都沉淀到 project-why.md
5. **智能维护**: AI 辅助决策是添加、增强还是合并知识
6. **优雅降级**: AI 不可用时自动降级到模板/规则决策

### 8.2 当前实现完成度

| 功能 | 完成度 | 说明 |
|------|--------|------|
| AI 增强问题生成 | 100% | 含历史上下文、降级方案 |
| 模板问题生成 | 100% | 5 个固定问题 |
| 问题注入 | 100% | 完整的 Markdown 格式 |
| 完成度检查 | 100% | pending/answered 状态 |
| 知识库管理 | 100% | 增删改查完整 |
| AI 辅助维护 | 100% | add/enhance/merge 决策 |
| 相似度检测 | 100% | SequenceMatcher |
| 知识增强 | 100% | 追加补充信息 |

### 8.3 后续优化方向

1. **代码扫描集成**: 基于受影响文件生成针对性问题
2. **知识图谱**: 构建知识条目之间的关联关系
3. **团队协作**: 支持多人共享和冲突合并
4. **自动合并优化**: 当前合并是简化实现，可优化为智能合并

---

## 附录

### A. 文件路径索引

| 文件 | 路径 | 说明 |
|------|------|------|
| WhyFirstEngine | `.claude/hooks/lib/why_first_engine.py` | 核心 Why-First 引擎 |
| AIClient | `.claude/hooks/lib/core.py` | AI 客户端 |
| 启动流程 | `.claude/skills/nomos/prompts/start.md` | 任务启动流程 |
| 知识维护 | `.claude/skills/nomos/prompts/update-why.md` | project-why.md 维护 |
| 知识库 | `project-why.md` | 项目知识库文件 |

### B. 关键代码行号索引

| 功能 | 文件 | 行号 |
|------|------|------|
| WhyFirstEngine 类定义 | `why_first_engine.py` | 17-45 |
| AI 问题生成 Prompt | `why_first_engine.py` | 21-34 |
| generate_why_questions | `why_first_engine.py` | 54-82 |
| _generate_ai_questions | `why_first_engine.py` | 84-132 |
| _generate_template_questions | `why_first_engine.py` | 134-142 |
| add_knowledge | `why_first_engine.py` | 144-209 |
| search_knowledge | `why_first_engine.py` | 211-241 |
| get_recent_knowledge | `why_first_engine.py` | 243-280 |
| validate_why_answers | `why_first_engine.py` | 282-302 |
| detect_similar_knowledge | `why_first_engine.py` | 304-342 |
| _calculate_similarity | `why_first_engine.py` | 344-355 |
| enhance_knowledge | `why_first_engine.py` | 374-408 |
| AI 知识库 Prompt | `why_first_engine.py` | 413-432 |
| ai_suggest_knowledge_operation | `why_first_engine.py` | 434-503 |
| _fallback_knowledge_operation | `why_first_engine.py` | 505-543 |
| execute_knowledge_operation | `why_first_engine.py` | 545-576 |
| inject_questions_to_research | `why_first_engine.py` | 580-688 |
| mark_why_questions_answered | `why_first_engine.py` | 713-745 |
| check_why_completion | `why_first_engine.py` | 747-821 |

### C. API 速查

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `generate_why_questions(task_name, description, use_ai)` | 任务名, 描述, 是否用AI | Dict | 生成 Why 问题 |
| `inject_questions_to_research(task_path, ...)` | 任务路径, 问题等 | Dict | 注入问题到 research.md |
| `check_why_completion(task_path)` | 任务路径 | Dict | 检查完成情况 |
| `mark_why_questions_answered(task_path)` | 任务路径 | bool | 标记已回答 |
| `add_knowledge(category, title, content)` | 分类, 标题, 内容 | bool | 添加知识条目 |
| `search_knowledge(keyword)` | 关键词 | List[Dict] | 搜索知识库 |
| `get_recent_knowledge(limit)` | 数量限制 | List[Dict] | 获取最近条目 |
| `detect_similar_knowledge(content, threshold)` | 内容, 阈值 | List[Dict] | 检测相似条目 |
| `ai_suggest_knowledge_operation(new_knowledge, threshold)` | 新知识, 阈值 | Dict | AI 辅助决策 |
| `execute_knowledge_operation(operation, ...)` | 操作类型等 | bool | 执行知识库操作 |
| `enhance_knowledge(title, additional_info)` | 标题, 补充信息 | bool | 增强现有条目 |

---

*本文档由 Claude Opus 4.6 生成*
*生成时间: 2026-03-02*
*来源: nOmOsAi Why-First 引擎代码分析*
