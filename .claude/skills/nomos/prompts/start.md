你正在执行 Nomos 的任务启动流程。

## 执行步骤

### 1. 创建任务文件夹

使用 Python 调用 TaskManager 创建任务：

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.task_manager import TaskManager

tm = TaskManager()
task = tm.create_task("任务名", "feat")  # 或 fix/refactor/test/docs
```

这将：
- 分配短 ID (t1, t2, ...)
- 创建任务文件夹 `tasks/t{N}-YYYY-MM-DD-任务名/`
- 初始化四件套: research.md, plan.md, code_review.md, progress.md
- 更新 current-task.txt 和 short-id-mapping.json

### 1.1 初始化阶段状态

**重要**: 创建任务后，必须初始化阶段状态文件：

```python
from lib.phase_manager import PhaseManager

pm = PhaseManager(str(task.path))  # task.path 是相对路径
pm.initialize(task.task_id)

print(f"✅ 阶段状态已初始化，当前阶段: research")
```

### 2. 创建 Git 分支

使用 GitManager 创建任务分支：

```python
from lib.git_manager import GitManager

git_mgr = GitManager()
branch_name = git_mgr.create_branch(
    task_id=task.task_id,
    task_name="任务名",
    branch_type="feat"  # 或 fix/refactor/test/docs
)

print(f"✅ 已创建并切换到分支: {branch_name}")
```

**分支命名规范**: `<type>/<date>-<task-name>`
- `feat/2026-02-26-user-login`
- `fix/2026-02-26-auth-bug`
- `refactor/2026-02-26-api-cleanup`

### 3. Why-First 阶段（必需）

**目标**: 深度思考任务的本质和价值

**步骤**:
1. 使用 WhyFirstEngine 生成并注入 Why 问题：
```python
from lib.why_first_engine import WhyFirstEngine

why_engine = WhyFirstEngine()

# 生成 Why 问题
questions = why_engine.generate_why_questions("任务名", "任务描述")

# 【重要】自动注入问题到 research.md
why_engine.inject_questions_to_research(
    task_path=str(task.path),  # 任务目录路径
    questions=questions,
    source="template"  # 或 "ai_generated" 如果使用 AI 生成
)

print(f"✅ 已生成 {len(questions)} 个 Why 问题并注入到 research.md")
```

2. 在 research.md 的 "Why Questions" 部分回答这些注入的问题
3. 回答完成后，标记 Why Questions 为已回答：
```python
why_engine.mark_why_questions_answered(str(task.path))
```
4. 将重要的决策和教训添加到 project-why.md：
```python
why_engine.add_knowledge(
    category="架构决策",  # 或 核心理念/经验教训/常见问题
    title="决策标题",
    content="决策内容和理由"
)
```

**Why Questions 示例**:
- 为什么需要这个功能？（核心动机）
- 为什么现在做？（时机选择）
- 为什么选择这种方案？（方案选择）
- 为什么不用其他方案？（替代方案分析）
- 核心价值是什么？（价值主张）

### 4. Research 阶段

**当前阶段**: `research`（此阶段**不允许写入代码文件**）

**目标**: 深入理解需求，调研相关代码

**步骤**:
1. 读取用户需求，记录到 research.md 的"需求理解"部分
2. 扫描相关代码模块，记录到"代码调研"部分
3. 识别 Protected Interfaces（不可修改的接口）
4. 回答 Why Questions（为什么需要、为什么这样做、为什么不那样做）
5. 设置 research.md 的 YAML Frontmatter: `status: draft`

**输出**: 完整的 research.md

### 5. 等待人类审阅 Research

**提示用户**:
```
✅ Research 阶段完成。

请审阅 tasks/{task_id}/research.md：
1. 在文档中右键添加 Review Comments
2. 标记类型: CRITICAL/MAJOR/MINOR/SUGGEST
3. 标记状态: pending

完成审阅后，告诉我继续。
```

**处理批注**:
- 读取 research.md 中的 Review Comments
- 逐条回复，标记为 `addressed`
- 如果有 CRITICAL/MAJOR 未处理，不能进入下一阶段

**完成 Research 阶段**:
```python
from lib.phase_manager import PhaseManager

pm = PhaseManager("tasks/t1-xxx")  # 替换为实际路径
pm.complete_phase("research", approved_by="human")

print("✅ Research 阶段已完成，进入 Plan 阶段")
```

### 6. Plan 阶段

**当前阶段**: `plan`（此阶段**不允许写入代码文件**）

**目标**: 设计实施方案

**步骤**:
1. 基于 research.md 生成 plan.md
2. 定义核心目标和成功标准
3. 设计架构和模块划分
4. 定义 Phase Gates（分阶段的可验证检查点）
   ```markdown
   ### Phase 1: 基础设施
   - [ ] Gate 1.1: 创建目录结构
   - [ ] Gate 1.2: 初始化配置文件

   ### Phase 2: 核心功能
   - [ ] Gate 2.1: 实现核心逻辑
   - [ ] Gate 2.2: 添加单元测试
   ```
5. 列出详细实施步骤
6. 识别风险和缓解措施
7. 设置 plan.md 的 YAML Frontmatter: `status: draft`

**输出**: 完整的 plan.md

### 7. 等待人类审阅 Plan

**提示用户**:
```
✅ Plan 阶段完成。

请审阅 tasks/{task_id}/plan.md：
1. 检查 Phase Gates 是否合理
2. 添加 Review Comments
3. 确认方案可行

完成审阅后，告诉我继续。
```

**完成 Plan 阶段**:
```python
from lib.phase_manager import PhaseManager

pm = PhaseManager("tasks/t1-xxx")  # 替换为实际路径
pm.complete_phase("plan", approved_by="human")

print("✅ Plan 阶段已完成，进入 Execute 阶段，现在可以写入代码文件")
```

### 8. Execute 阶段

**当前阶段**: `execute`（此阶段**允许写入代码文件**）

**目标**: 按 Phase Gates 逐步实现

**步骤**:
1. 按 plan.md 中的 Phase Gates 顺序执行
2. 每完成一个 Gate，在 plan.md 中勾选 checkbox: `- [x] Gate 1.1: ...`
3. PreToolUse Hook 会自动运行 Linter 检查代码
   - 如果 Linter 失败 → 修复后重试
   - 如果 Linter 通过 → 允许写入
4. 更新 progress.md 记录进度和问题
5. 设置 plan.md 的 YAML Frontmatter: `status: executing`
6. 更新阶段 Gates 进度：
   ```python
   # 统计 plan.md 中已完成和未完成的 Gates
   pm.update_gates("execute", total=8, completed=3)
   ```

**约束**:
- 不能跳过 Gate
- 所有代码必须通过 Linter
- Stop Hook 会检查 Gates 完成情况

**完成 Execute 阶段**:
```python
pm.complete_phase("execute", approved_by="agent")
print("✅ Execute 阶段已完成，进入 Review 阶段")
```

### 9. Review 阶段

**当前阶段**: `review`（此阶段**允许写入代码文件**）

**目标**: 验证实现质量

**步骤**:
1. 运行测试
2. 生成 code_review.md
3. 记录变更和审查发现
4. 设置 plan.md 的 YAML Frontmatter: `status: done`

**完成 Review 阶段**:
```python
pm.complete_phase("review", approved_by="agent")
print("✅ 任务完成！")
```

## 约束（刚性门控）

- **不能跳过 Research 直接写 Plan** → Phase Manager 强制检查
- **不能跳过 Plan 直接写代码** → PreToolUse Hook 拦截
- **所有 CRITICAL/MAJOR Review Comments 必须 addressed**
- **所有 Phase Gates 必须完成**
- **所有代码必须通过 Linter**

## 示例

```bash
# 用户输入
/nomos:start user-login

# Agent 执行
1. 创建 tasks/t1-2026-02-26-user-login/
2. 初始化四件套 + phase_state.json
3. 创建 Git 分支 feat/2026-02-26-user-login
4. 开始 Why-First 阶段...
```

## 阶段状态文件说明

每个任务文件夹下会生成 `phase_state.json`：

```json
{
  "task_id": "t1",
  "current_phase": "execute",
  "research": {
    "completed": true,
    "approved_by": "human",
    "approved_at": "2026-02-27T10:00:00"
  },
  "plan": {
    "completed": true,
    "approved_by": "human",
    "approved_at": "2026-02-27T11:00:00",
    "gates_total": 5,
    "gates_completed": 5
  },
  "execute": {
    "completed": false,
    "gates_total": 8,
    "gates_completed": 3
  },
  "review": {
    "completed": false
  }
}
```
