# Why-First 引擎增强设计方案

**文档版本**: 1.0
**创建日期**: 2026-03-01
**作者**: Claude Opus 4.6
**状态**: Draft

---

## 1. 背景与问题分析

### 1.1 当前实现现状

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Why-First 当前实现分析                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ✅ 已实现功能:                                                      │
│  ├── generate_why_questions()   - 生成 5 个固定模板问题              │
│  ├── add_knowledge()            - 添加知识到 project-why.md          │
│  ├── search_knowledge()         - 搜索知识库                         │
│  ├── get_recent_knowledge()     - 获取最近知识                       │
│  ├── detect_similar_knowledge() - 检测相似知识                       │
│  ├── enhance_knowledge()        - 增强现有知识                       │
│  ├── suggest_merge()            - 建议合并知识                       │
│  └── validate_why_answers()     - 验证 Why 答案                      │
│                                                                      │
│  ⚠️ 功能孤岛问题:                                                    │
│  ├── search_knowledge() 存在但未在 generate_why_questions() 中使用  │
│  ├── validate_why_answers() 存在但未在 PhaseManager 中使用          │
│  └── AIClient 存在但未集成到 Why-First                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 流程断裂问题

**问题 1: 问题生成与模板不一致**

| 来源 | 问题数量 | 问题内容 |
|------|----------|----------|
| WhyFirstEngine.generate_why_questions() | 5 个 | 为什么需要/为什么现在做/为什么选择这种方式/为什么不用其他/核心价值 |
| research.md 模板 | 3 个 | 为什么需要/为什么选择/为什么不选择 |

**问题 2: 无强制验证机制**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    当前 PhaseManager 门控检查                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  can_proceed_to("plan"):                                            │
│  ├── ✅ 检查 research.completed                                     │
│  ├── ✅ 检查 research.approved_by                                   │
│  ├── ✅ 检查 Review Comments 存在                                   │
│  ├── ✅ 检查 CRITICAL/MAJOR 已处理                                  │
│  └── ❌ 未检查 Why Questions 是否被回答                             │
│                                                                      │
│  结果: Agent 可以跳过 Why Questions 直接完成 Research               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**问题 3: Why-First 与 Research 流程脱节**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    当前流程（断裂）                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  start.md 描述的流程:                                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ 调用 Engine     │───►│ 生成 5 个问题   │───►│ ??? 怎么用？    │  │
│  │ 生成问题        │    │ (固定模板)      │    │                 │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                                        │            │
│                                                        ▼            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ research.md     │◄───│ Agent 手动      │◄───│ 问题去哪了？    │  │
│  │ 有 3 个固定问题 │    │ 填写答案        │    │ 未自动注入      │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                                                      │
│  问题:                                                               │
│  ├── 生成的问题没有自动注入到 research.md                           │
│  ├── Agent 需要手动参考问题来填写                                   │
│  ├── 没有验证机制确保问题被回答                                     │
│  └── 历史知识完全未被利用                                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 AIClient 位置问题

**当前状态**:

```
.claude/hooks/lib/
└── l3_foundation/
    ├── __init__.py           # 导出 AIClient
    ├── ai_client.py          # AI 客户端
    ├── rule_loader.py        # 使用 AIClient
    ├── prompt_builder.py     # 文档引用 AIClient
    └── rule_generator.py     # 使用 AIClient
```

**问题**:
- `l3_foundation` 命名暗示"第三层基础设施"
- 但 AI 能力应该是更基础的"水电煤"级别
- Why-First 引擎需要 AI 能力，但依赖方向不清晰

---

## 2. 设计目标

### 2.1 核心目标

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Why-First 增强目标                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  目标 1: 修复流程断裂                                                │
│  ├── Why 问题自动注入到 research.md                                 │
│  ├── PhaseManager 验证 Why Questions 是否被回答                     │
│  └── 形成闭环：生成 → 注入 → 回答 → 验证                            │
│                                                                      │
│  目标 2: AI 增强问题生成                                             │
│  ├── 集成 AIClient 到 Why-First 引擎                                │
│  ├── AI 生成针对性问题（基于任务描述和历史知识）                     │
│  ├── AI 辅助知识库维护（智能合并/增强建议）                          │
│  └── 降级方案：AI 不可用时使用固定模板                               │
│                                                                      │
│  目标 3: AI 客户端重构                                               │
│  ├── 移动 AIClient 到 core 包                                       │
│  ├── 统一导入路径                                                    │
│  └── 同步修改所有依赖点（L3 业务规则校验等）                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 非目标

- 不移动 why_first_engine.py 文件位置
- 不修改 PhaseManager 的核心门控逻辑（仅增加 Why 验证）
- 不引入外部 NLP 依赖

---

## 3. 架构调整方案

### 3.1 AI 客户端位置调整

```
┌─────────────────────────────────────────────────────────────────────┐
│                    新的目录结构                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  .claude/hooks/lib/                                                 │
│  ├── core/                        # 【新增】核心基础设施层           │
│  │   ├── __init__.py                                                │
│  │   └── ai_client.py             # ← 从 l3_foundation 移入         │
│  │                                                                 │
│  ├── l3_foundation/               # L3 业务规则校验模块              │
│  │   ├── __init__.py              # 移除 AIClient 导出              │
│  │   ├── rule_loader.py           # 导入路径需修改                  │
│  │   ├── prompt_builder.py        # 导入路径需修改                  │
│  │   └── rule_generator.py        # 导入路径需修改                  │
│  │                                                                 │
│  ├── why_first_engine.py          # 位置不变，导入路径修改          │
│  └── ...                                                            │
│                                                                      │
│  导入路径变化:                                                       │
│  ├── 旧: from lib.l3_foundation import AIClient                     │
│  └── 新: from lib.core import AIClient                              │
│                                                                      │
│  ⚠️ 重要: 必须同步修改所有依赖点                                    │
│  ├── l3_foundation/rule_loader.py   - L3 动态规则加载器              │
│  ├── l3_foundation/rule_generator.py - L3 规则生成器                │
│  └── 其他使用 AIClient 的模块                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 需要修改的文件清单

| 文件 | 修改内容 |
|------|----------|
| `lib/core/__init__.py` | 新建，导出 AIClient |
| `lib/core/ai_client.py` | 从 l3_foundation 移入 |
| `lib/l3_foundation/__init__.py` | 移除 AIClient 导出（不再导出） |
| `lib/l3_foundation/rule_loader.py` | 修改导入路径为 `from lib.core import AIClient` |
| `lib/l3_foundation/rule_generator.py` | 修改导入路径为 `from lib.core import AIClient` |
| `lib/why_first_engine.py` | 添加 `from lib.core import AIClient` |

> ⚠️ **注意**: L3 业务规则校验系统正在使用 AIClient，迁移时必须同步修改所有依赖点。

---

## 4. Why-First 引擎增强设计

### 4.1 增强后的问题生成流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    增强版 Why 问题生成流程                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  generate_why_questions(task_name, description, task_path)          │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 1: 检查 AI 可用性                                          ││
│  │                                                                 ││
│  │ ai_client = AIClient()                                          ││
│  │ if not ai_client.available:                                     ││
│  │     → 降级到固定模板 5 个问题                                    ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼ (AI 可用)                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 2: 收集上下文                                              ││
│  │                                                                 ││
│  │ # 从 project-why.md 搜索相关知识                                ││
│  │ historical = self.search_knowledge(task_name)                   ││
│  │                                                                 ││
│  │ # 获取最近的知识条目                                            ││
│  │ recent = self.get_recent_knowledge(limit=3)                     ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 3: AI 生成针对性问题                                       ││
│  │                                                                 ││
│  │ prompt = """                                                    ││
│  │ 你是一个深度思考助手。请为以下任务生成 5-8 个"Why"问题。         ││
│  │                                                                 ││
│  │ 任务名称: {task_name}                                           ││
│  │ 任务描述: {description}                                         ││
│  │                                                                 ││
│  │ 相关历史决策:                                                   ││
│  │ {format_knowledge(historical)}                                  ││
│  │                                                                 ││
│  │ 要求:                                                           ││
│  │ 1. 问题应基于任务描述的具体内容                                  ││
│  │ 2. 参考历史决策，生成针对性的对比问题                            ││
│  │ 3. 问题应涵盖: 核心动机、方案选择、潜在风险、依赖关系            ││
│  │ 4. 返回 JSON 格式: {"questions": ["问题1", "问题2", ...]}        ││
│  │ """                                                             ││
│  │                                                                 ││
│  │ result = ai_client.call(prompt, "", max_tokens=1024)            ││
│  │ questions = parse_questions(result)                             ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼ (AI 失败或返回无效)                                        │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 4: 降级到固定模板                                          ││
│  │                                                                 ││
│  │ return [                                                        ││
│  │     f"为什么需要 {task_name}？",                                 ││
│  │     f"为什么现在做 {task_name}？",                               ││
│  │     f"为什么选择这种方式实现 {task_name}？",                     ││
│  │     f"为什么不用其他方案？",                                     ││
│  │     f"{task_name} 的核心价值是什么？"                           ││
│  │ ]                                                               ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Why 问题注入机制

**新增方法: `inject_questions_to_research()`**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Why 问题注入流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  inject_questions_to_research(task_path, questions)                 │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 1. 读取 research.md 模板                                        ││
│  │    research_path = task_path / "research.md"                    ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 2. 定位 "## 4. Why Questions" 部分                              ││
│  │    找到该部分，替换其中的问题列表                                ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 3. 生成新的 Why Questions 内容                                  ││
│  │                                                                 ││
│  │    ## 4. Why Questions                                          ││
│  │                                                                 ││
│  │    > **状态**: [pending/answered]                               ││
│  │    > **生成时间**: 2026-03-01                                   ││
│  │    > **来源**: AI生成/固定模板                                  ││
│  │                                                                 ││
│  │    ### 4.1 为什么需要 {task_name}？                             ││
│  │                                                                 ││
│  │    （Agent 在此回答）                                           ││
│  │                                                                 ││
│  │    ### 4.2 为什么现在做 {task_name}？                           ││
│  │                                                                 ││
│  │    （Agent 在此回答）                                           ││
│  │    ...                                                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 4. 写回 research.md                                             ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**新的 research.md Why Questions 部分模板**:

```markdown
## 4. Why Questions

> **状态**: [pending]
> **生成时间**: {TIMESTAMP}
> **来源**: {ai_generated|template}
> **问题数量**: {N}

### 4.1 {QUESTION_1}

（Agent 在此回答）

### 4.2 {QUESTION_2}

（Agent 在此回答）

...
```

### 4.3 Why 验证机制

**PhaseManager 增强检查**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PhaseManager Why 验证增强                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  can_proceed_to("plan") 新增检查:                                   │
│                                                                      │
│  def _check_why_questions_answered(self) -> Tuple[bool, str]:       │
│      """                                                             │
│      检查 research.md 中的 Why Questions 是否已回答                 │
│      """                                                             │
│      research_path = self.task_path / "research.md"                 │
│                                                                      │
│      # 1. 检查 Why Questions 部分是否存在                           │
│      if not has_why_questions_section(content):                     │
│          return False, "research.md 中缺少 Why Questions 部分"      │
│                                                                      │
│      # 2. 检查状态标记                                              │
│      status = extract_why_status(content)                           │
│      if status == "pending":                                        │
│          return False, "Why Questions 尚未回答，请完成深度思考"     │
│                                                                      │
│      # 3. 检查每个问题是否有实质内容                                │
│      questions = parse_why_questions(content)                       │
│      unanswered = []                                                │
│      for q in questions:                                            │
│          if not has_substantive_answer(q):                          │
│              unanswered.append(q.title)                             │
│                                                                      │
│      if unanswered:                                                 │
│          return False, f"以下 Why 问题未回答: {unanswered}"         │
│                                                                      │
│      return True, "Why Questions 检查通过"                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**WhyFirstEngine 新增方法**:

```python
def mark_why_questions_answered(self, task_path: str) -> bool:
    """
    标记 Why Questions 已回答

    在 Agent 完成所有 Why 问题回答后调用
    """
    research_path = Path(task_path) / "research.md"

    with open(research_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 更新状态标记
    content = re.sub(
        r'> \*\*状态\*\*: \[pending\]',
        '> **状态**: [answered]',
        content
    )

    with open(research_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

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
    research_path = Path(task_path) / "research.md"

    if not research_path.exists():
        return {'has_why_section': False, 'status': 'missing'}

    with open(research_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 Why Questions 部分
    why_match = re.search(
        r'## 4\. Why Questions(.*?)(?=## 5\.|\Z)',
        content, re.DOTALL
    )

    if not why_match:
        return {'has_why_section': False, 'status': 'missing'}

    why_section = why_match.group(1)

    # 检查状态
    status_match = re.search(r'> \*\*状态\*\*: \[(\w+)\]', why_section)
    status = status_match.group(1) if status_match else 'pending'

    # 统计问题
    questions = re.findall(r'### 4\.\d+ (.+)', why_section)
    total = len(questions)

    # 检查每个问题是否有回答
    answered = 0
    unanswered = []

    for i, q in enumerate(questions, 1):
        # 提取问题后的内容
        q_pattern = rf'### 4\.{i} .+?\n\n(.*?)(?=### 4\.\d+|## |\Z)'
        q_match = re.search(q_pattern, why_section, re.DOTALL)

        if q_match:
            answer = q_match.group(1).strip()
            # 检查是否有实质内容（超过 20 字符且不是占位符）
            if len(answer) > 20 and '（' not in answer[:10]:
                answered += 1
            else:
                unanswered.append(q)
        else:
            unanswered.append(q)

    return {
        'has_why_section': True,
        'status': status,
        'total_questions': total,
        'answered_questions': answered,
        'unanswered': unanswered
    }
```

### 4.4 AI 辅助知识库维护

**新增方法: `ai_suggest_knowledge_operation()`**

```python
def ai_suggest_knowledge_operation(self, new_knowledge: str) -> Dict[str, any]:
    """
    AI 辅助决策知识库操作

    Args:
        new_knowledge: 新知识内容

    Returns:
        {
            'operation': 'add' | 'enhance' | 'merge',
            'target': None | {'title': str, 'similarity': float},
            'reason': str,
            'suggested_content': str
        }
    """
    ai_client = AIClient()

    if not ai_client.available:
        # 降级：使用相似度检测
        similar = self.detect_similar_knowledge(new_knowledge, 0.7)
        if similar and similar[0]['similarity'] > 0.8:
            return {
                'operation': 'enhance',
                'target': similar[0],
                'reason': f"相似度 {similar[0]['similarity']:.2%}，建议增强",
                'suggested_content': new_knowledge
            }
        return {
            'operation': 'add',
            'target': None,
            'reason': "未发现相似条目",
            'suggested_content': new_knowledge
        }

    # 获取相关历史知识
    similar = self.detect_similar_knowledge(new_knowledge, 0.5)

    prompt = f"""
你是知识库管理助手。请分析新知识并决定最佳操作。

新知识:
{new_knowledge}

相似的历史知识:
{json.dumps(similar[:3], ensure_ascii=False, indent=2)}

请返回 JSON 格式:
{{
    "operation": "add" | "enhance" | "merge",
    "target_title": "目标条目标题" 或 null,
    "reason": "决策理由",
    "suggested_content": "建议的内容（如需合并则提供合并后内容）"
}}
"""

    result = ai_client.call(prompt, "", max_tokens=1024)

    if result and 'operation' in result:
        return result

    # AI 返回无效，降级
    return {
        'operation': 'add',
        'target': None,
        'reason': "AI 分析失败，默认添加新条目",
        'suggested_content': new_knowledge
    }
```

---

## 5. 完整流程设计

### 5.1 增强后的 start.md 流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    增强后的任务启动流程                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  /nomos:start <任务名>                                              │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 1: 创建任务文件夹 + 初始化阶段状态                         ││
│  │ (不变)                                                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 2: 创建 Git 分支                                           ││
│  │ (不变)                                                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 3: Why-First 阶段（增强）                                   ││
│  │                                                                 ││
│  │ # 生成 Why 问题（AI 增强）                                      ││
│  │ questions = why_engine.generate_why_questions(                  ││
│  │     task_name,                                                  ││
│  │     description,                                                ││
│  │     task_path=task.path                                         ││
│  │ )                                                               ││
│  │                                                                 ││
│  │ # 【新增】自动注入问题到 research.md                            ││
│  │ why_engine.inject_questions_to_research(task.path, questions)   ││
│  │                                                                 ││
│  │ print(f"✅ 已生成 {len(questions)} 个 Why 问题并注入到 research.md")│
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 4: Research 阶段                                           ││
│  │                                                                 ││
│  │ # Agent 填写 research.md                                        ││
│  │ # - 需求理解                                                     ││
│  │ # - 代码调研                                                     ││
│  │ # - Protected Interfaces                                        ││
│  │ # - Why Questions（回答注入的问题）                             ││
│  │                                                                 ││
│  │ # 【新增】完成 Why 回答后标记                                   ││
│  │ why_engine.mark_why_questions_answered(task.path)               ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 5: 等待人类审阅                                            ││
│  │ (不变)                                                          ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 6: PhaseManager 验证（增强）                               ││
│  │                                                                 ││
│  │ # 原有检查                                                       ││
│  │ - Review Comments 存在                                          ││
│  │ - CRITICAL/MAJOR 已处理                                         ││
│  │                                                                 ││
│  │ # 【新增】Why Questions 检查                                    ││
│  │ why_status = why_engine.check_why_completion(task.path)         ││
│  │ if why_status['status'] != 'answered':                          ││
│  │     return False, "Why Questions 尚未完成深度思考"              ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ▼                                                            │
│  继续后续阶段...                                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 知识沉淀流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    知识沉淀流程（增强）                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  任务完成，Agent 准备沉淀知识                                       │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Step 1: AI 辅助决策操作类型                                     ││
│  │                                                                 ││
│  │ suggestion = why_engine.ai_suggest_knowledge_operation(         ││
│  │     new_knowledge                                               ││
│  │ )                                                               ││
│  │                                                                 ││
│  │ print(f"💡 AI 建议: {suggestion['operation']}")                 ││
│  │ print(f"   理由: {suggestion['reason']}")                       ││
│  └─────────────────────────────────────────────────────────────────┘│
│         │                                                            │
│         ├── operation == "add"                                       │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 直接添加新条目                                                  ││
│  │ why_engine.add_knowledge(category, title, content)              ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│         ├── operation == "enhance"                                   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 增强现有条目                                                    ││
│  │ why_engine.enhance_knowledge(                                   ││
│  │     title=suggestion['target']['title'],                        ││
│  │     additional_info=suggestion['suggested_content']             ││
│  │ )                                                               ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│         └── operation == "merge"                                     │
│                                                                      │
│             ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 合并条目                                                        ││
│  │ # AI 已提供合并后内容，执行合并                                 ││
│  │ # 1. 删除旧条目                                                 ││
│  │ # 2. 添加合并后的新条目                                         ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. API 变更清单

### 6.1 WhyFirstEngine 新增方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `generate_why_questions()` | task_name, description, task_path | List[str] | **增强**: AI 生成 + 历史知识 + 降级 |
| `inject_questions_to_research()` | task_path, questions | bool | **新增**: 注入问题到 research.md |
| `mark_why_questions_answered()` | task_path | bool | **新增**: 标记问题已回答 |
| `check_why_completion()` | task_path | Dict | **新增**: 检查完成情况 |
| `ai_suggest_knowledge_operation()` | new_knowledge | Dict | **新增**: AI 辅助知识库操作 |

### 6.2 PhaseManager 变更

| 方法 | 变更 |
|------|------|
| `can_proceed_to("plan")` | **增强**: 新增 Why Questions 完成检查 |
| `_check_why_questions_answered()` | **新增**: 检查 Why 答案状态 |

### 6.3 导入路径变更

| 模块 | 旧路径 | 新路径 |
|------|--------|--------|
| AIClient | `from lib.l3_foundation import AIClient` | `from lib.core import AIClient` |

> ⚠️ **必须同步修改**: L3 业务规则校验系统（rule_loader.py, rule_generator.py）正在使用 AIClient，迁移时必须更新所有导入路径。

---

## 7. 文件修改清单

### 7.1 新建文件

| 文件 | 说明 |
|------|------|
| `lib/core/__init__.py` | 核心模块入口，导出 AIClient |
| `lib/core/ai_client.py` | 从 l3_foundation 移入 |

### 7.2 修改文件

| 文件 | 修改内容 |
|------|----------|
| `lib/l3_foundation/__init__.py` | 移除 AIClient 导出 |
| `lib/l3_foundation/rule_loader.py` | 修改 AIClient 导入路径（L3 业务规则校验） |
| `lib/l3_foundation/rule_generator.py` | 修改 AIClient 导入路径（L3 业务规则校验） |
| `lib/why_first_engine.py` | 集成 AIClient，新增方法 |
| `lib/phase_manager.py` | 新增 Why Questions 检查 |
| `lib/task_manager.py` | 创建任务时调用 Why 问题注入 |
| `.claude/skills/nomos/prompts/start.md` | 更新流程描述 |
| `.claude/skills/nomos/templates/research.md` | 更新 Why Questions 模板格式 |

### 7.3 Rule Example 文件（同步修改）

| 文件 | 修改内容 |
|------|----------|
| `lib/rule_examples/i18n_check.py.example` | 更新 AIClient 导入路径 |
| `lib/rule_examples/logger_standard.py.example` | 更新 AIClient 导入路径 |
| `lib/rule_examples/README.md` | 更新文档中的导入示例 |

> ⚠️ **关键依赖**: `lib/l3_foundation/rule_loader.py` 和 `rule_generator.py` 是 L3 业务规则校验的核心模块，必须确保迁移后正常工作。Rule Example 文件是用户自定义规则的参考模板，也需要同步更新。

### 7.4 删除文件

| 文件 | 说明 |
|------|------|
| `lib/l3_foundation/ai_client.py` | 移动到 core 后删除原文件 |

---

## 8. 实施计划

### 8.1 阶段划分

```
┌─────────────────────────────────────────────────────────────────────┐
│                    实施阶段                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Phase 1: AI 客户端迁移 (基础)                                      │
│  ├── 创建 lib/core/ 目录                                            │
│  ├── 移动 ai_client.py                                              │
│  ├── 更新所有导入路径                                               │
│  │   ├── l3_foundation/rule_loader.py                               │
│  │   ├── l3_foundation/rule_generator.py                            │
│  │   ├── rule_examples/i18n_check.py.example                        │
│  │   ├── rule_examples/logger_standard.py.example                   │
│  │   └── rule_examples/README.md                                    │
│  ├── 验证 L3 业务规则校验正常工作                                   │
│  └── 预计工时: 15m                                                  │
│                                                                      │
│  Phase 2: Why 问题注入机制                                          │
│  ├── 修改 research.md 模板格式                                      │
│  ├── 实现 inject_questions_to_research()                            │
│  ├── 修改 start.md 流程                                             │
│  └── 预计工时: 30m                                                  │
│                                                                      │
│  Phase 3: AI 增强问题生成                                           │
│  ├── 增强 generate_why_questions()                                  │
│  ├── 实现 AI 生成逻辑                                               │
│  ├── 实现降级方案                                                   │
│  └── 预计工时: 45m                                                  │
│                                                                      │
│  Phase 4: Why 验证机制                                              │
│  ├── 实现 check_why_completion()                                    │
│  ├── 实现 mark_why_questions_answered()                             │
│  ├── 增强 PhaseManager 门控                                         │
│  └── 预计工时: 30m                                                  │
│                                                                      │
│  Phase 5: AI 辅助知识库维护                                         │
│  ├── 实现 ai_suggest_knowledge_operation()                          │
│  ├── 更新 update-why.md prompt                                      │
│  └── 预计工时: 30m                                                  │
│                                                                      │
│  总计: ~2.5h                                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 验收标准

| 阶段 | 验收标准 |
|------|----------|
| Phase 1 | 所有导入 AIClient 的模块正常工作 |
| Phase 2 | /nomos:start 后 research.md 自动包含 Why Questions |
| Phase 3 | AI 可用时生成针对性问题，不可用时降级到固定模板 |
| Phase 4 | 未回答 Why Questions 时无法进入 Plan 阶段 |
| Phase 5 | AI 能智能决策知识库操作类型 |

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI 服务不可用 | 问题生成降级 | 固定模板作为降级方案 |
| AI 返回无效 JSON | 问题解析失败 | try-catch + 降级到固定模板 |
| AIClient 迁移遗漏依赖点 | L3 校验功能中断 | 迁移前完整扫描所有依赖，迁移后运行 L3 校验测试 |
| Why 验证过于严格 | 阻塞正常流程 | 允许用户手动标记已回答 |

---

## 10. 附录

### A. 新的 research.md 模板（Why Questions 部分）

```markdown
## 4. Why Questions

> **状态**: [pending]
> **生成时间**: {TIMESTAMP}
> **来源**: {ai_generated|template}
> **问题数量**: {N}

### 4.1 {QUESTION_1}

（请在此回答，回答完成后将状态改为 [answered]）

### 4.2 {QUESTION_2}

（请在此回答）

...
```

### B. AI 生成问题的 Prompt 模板

```
你是深度思考助手。请为以下任务生成 5-8 个"Why"问题。

任务名称: {task_name}
任务描述: {description}

相关历史决策:
{historical_knowledge}

要求:
1. 问题应基于任务描述的具体内容，避免泛泛而谈
2. 参考历史决策，生成针对性的对比问题
3. 问题应涵盖: 核心动机、方案选择、潜在风险、依赖关系
4. 返回 JSON 格式: {"questions": ["问题1", "问题2", ...]}
5. 问题应该是开放式的，引导深度思考
```

---

*本文档由 Claude Opus 4.6 生成*
*生成时间: 2026-03-01*
