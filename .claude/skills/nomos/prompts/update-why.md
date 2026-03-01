更新和维护 project-why.md 知识库。

## 执行步骤

### 1. AI 辅助决策（推荐）

使用 AI 自动分析新知识并建议最佳操作：

```python
import sys
sys.path.insert(0, '.claude/hooks')
from lib.why_first_engine import WhyFirstEngine

why_engine = WhyFirstEngine()

# 用户提供的新知识
new_knowledge = """
用户输入的新知识内容
"""

# 【推荐】AI 辅助决策
suggestion = why_engine.ai_suggest_knowledge_operation(new_knowledge)

print(f"🤖 AI 建议: {suggestion['operation']}")
print(f"   理由: {suggestion['reason']}")
print(f"   AI 可用: {suggestion['ai_available']}")

if suggestion['target']:
    print(f"   目标条目: {suggestion['target']['title']}")
    print(f"   相似度: {suggestion['target']['similarity']:.2%}")
```

### 2. 执行建议的操作

```python
# 直接执行 AI 建议的操作
success = why_engine.execute_knowledge_operation(
    operation=suggestion['operation'],
    category="架构决策",  # 或 核心理念/经验教训/常见问题
    title="新知识标题",
    content=suggestion['suggested_content'],
    target=suggestion['target']
)

if success:
    print(f"✅ 已执行操作: {suggestion['operation']}")
else:
    print("❌ 操作失败")
```

### 3. 手动模式（可选）

如果需要手动控制，可以使用传统方法：

```python
# 检测相似条目
similar_items = why_engine.detect_similar_knowledge(new_knowledge, threshold=0.7)

if similar_items:
    print(f"🔍 发现 {len(similar_items)} 个相似条目:\n")
    for item in similar_items:
        print(f"  - {item['title']} (相似度: {item['similarity']:.2%})")

# 手动选择操作
# - 添加新条目: why_engine.add_knowledge(category, title, content)
# - 增强现有条目: why_engine.enhance_knowledge(title, additional_info)
# - 合并建议: why_engine.suggest_merge(item1, item2)
```

### 4. 显示更新后的知识库

```python
recent = why_engine.get_recent_knowledge(limit=5)

print("\n📚 最近的知识条目:\n")
for item in recent:
    print(f"  - {item['title']} ({item['timestamp']})")
    print(f"    {item['content'][:80]}...")
    print()
```

## 操作类型说明

| 操作 | 说明 | 触发条件 |
|------|------|----------|
| `add` | 创建新条目 | 无相似条目或相似度 < 0.6 |
| `enhance` | 增强现有条目 | 相似度 > 0.8，添加补充信息 |
| `merge` | 合并条目 | 相似度 0.6-0.8，讨论同一主题 |

## AI 辅助 vs 手动模式

| 模式 | 优点 | 适用场景 |
|------|------|----------|
| **AI 辅助** | 智能分析、自动决策、省时 | 大多数情况 |
| **手动模式** | 精确控制、理解每一步 | 需要人工审核时 |

## 使用场景

- 完成任务后总结经验教训
- 发现重要架构决策
- 记录失败原因和避免方法
- 更新项目核心理念

## 注意事项

- AI 不可用时会自动降级到基于相似度的决策
- 增强操作会在条目末尾添加补充信息
- 合并操作会保留原有内容并添加新内容
- 定期检查知识库，保持组织性
