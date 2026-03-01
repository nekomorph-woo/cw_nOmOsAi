"""
Why-First 引擎
生成和管理 Why 问题，维护 project-why.md 知识库
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from difflib import SequenceMatcher


class WhyFirstEngine:
    """Why-First 引擎"""

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化 Why-First 引擎

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or os.getcwd())
        self.project_why_file = self.project_root / 'project-why.md'

    def generate_why_questions(self, task_name: str, description: str) -> List[str]:
        """
        生成 Why 问题

        Args:
            task_name: 任务名称
            description: 任务描述

        Returns:
            Why 问题列表
        """
        questions = [
            f"为什么需要 {task_name}？",
            f"为什么现在做 {task_name}？",
            f"为什么选择这种方式实现 {task_name}？",
            f"为什么不用其他方案？",
            f"{task_name} 的核心价值是什么？"
        ]

        return questions

    def add_knowledge(self, category: str, title: str, content: str) -> bool:
        """
        添加知识到 project-why.md

        Args:
            category: 分类（核心理念/架构决策/经验教训/常见问题）
            title: 标题
            content: 内容

        Returns:
            是否成功
        """
        if not self.project_why_file.exists():
            return False

        # 读取现有内容
        with open(self.project_why_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 查找分类位置
        category_map = {
            '核心理念': '## 核心理念',
            '架构决策': '## 架构决策',
            '经验教训': '## 经验教训',
            '常见问题': '## 常见问题'
        }

        category_header = category_map.get(category)
        if not category_header:
            return False

        # 找到分类位置
        insert_index = -1
        for i, line in enumerate(lines):
            if line.strip() == category_header:
                # 找到下一个 ## 或文件末尾
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith('## '):
                        insert_index = j
                        break
                if insert_index == -1:
                    insert_index = len(lines)
                break

        if insert_index == -1:
            return False

        # 插入新内容
        timestamp = datetime.now().strftime('%Y-%m-%d')
        new_content = [
            '\n',
            f'### {title}\n',
            '\n',
            f'**时间**: {timestamp}\n',
            '\n',
            f'{content}\n',
            '\n'
        ]

        lines[insert_index:insert_index] = new_content

        # 写回文件
        with open(self.project_why_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return True

    def search_knowledge(self, keyword: str) -> List[Dict[str, str]]:
        """
        搜索知识库

        Args:
            keyword: 关键词

        Returns:
            匹配的知识条目列表
        """
        if not self.project_why_file.exists():
            return []

        with open(self.project_why_file, 'r', encoding='utf-8') as f:
            content = f.read()

        results = []
        sections = re.split(r'\n### ', content)

        for section in sections[1:]:  # 跳过第一个（YAML frontmatter 和标题）
            if keyword.lower() in section.lower():
                lines = section.split('\n', 1)
                title = lines[0].strip()
                body = lines[1] if len(lines) > 1 else ''

                results.append({
                    'title': title,
                    'content': body.strip()
                })

        return results

    def get_recent_knowledge(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        获取最近的知识条目

        Args:
            limit: 返回数量

        Returns:
            知识条目列表
        """
        if not self.project_why_file.exists():
            return []

        with open(self.project_why_file, 'r', encoding='utf-8') as f:
            content = f.read()

        results = []
        sections = re.split(r'\n### ', content)

        for section in sections[1:]:  # 跳过第一个
            lines = section.split('\n', 1)
            title = lines[0].strip()
            body = lines[1] if len(lines) > 1 else ''

            # 提取时间
            time_match = re.search(r'\*\*时间\*\*:\s*(\d{4}-\d{2}-\d{2})', body)
            timestamp = time_match.group(1) if time_match else '1970-01-01'

            results.append({
                'title': title,
                'content': body.strip(),
                'timestamp': timestamp
            })

        # 按时间排序
        results.sort(key=lambda x: x['timestamp'], reverse=True)

        return results[:limit]

    def validate_why_answers(self, research_content: str) -> Dict[str, bool]:
        """
        验证 research.md 中是否回答了 Why 问题

        Args:
            research_content: research.md 内容

        Returns:
            验证结果字典
        """
        required_sections = [
            '为什么需要',
            '为什么选择',
            '为什么不'
        ]

        results = {}
        for section in required_sections:
            results[section] = section in research_content

        return results

    def detect_similar_knowledge(self, new_content: str, threshold: float = 0.7) -> List[Dict[str, any]]:
        """
        检测相似的知识条目

        Args:
            new_content: 新内容
            threshold: 相似度阈值 (0-1)

        Returns:
            相似条目列表
        """
        if not self.project_why_file.exists():
            return []

        with open(self.project_why_file, 'r', encoding='utf-8') as f:
            content = f.read()

        similar_items = []
        sections = re.split(r'\n### ', content)

        for section in sections[1:]:
            lines = section.split('\n', 1)
            title = lines[0].strip()
            body = lines[1] if len(lines) > 1 else ''

            # 计算相似度
            similarity = self._calculate_similarity(new_content, body)

            if similarity >= threshold:
                similar_items.append({
                    'title': title,
                    'content': body.strip(),
                    'similarity': similarity
                })

        # 按相似度排序
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)

        return similar_items

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度 (0-1)
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def suggest_merge(self, item1: Dict, item2: Dict) -> Dict[str, str]:
        """
        建议合并两个知识条目

        Args:
            item1: 条目1
            item2: 条目2

        Returns:
            合并建议
        """
        return {
            'merged_title': f"{item1['title']} & {item2['title']}",
            'merged_content': f"{item1['content']}\n\n---\n\n{item2['content']}",
            'reason': f"相似度: {item1.get('similarity', 0):.2%}"
        }

    def enhance_knowledge(self, title: str, additional_info: str) -> bool:
        """
        增强现有知识条目

        Args:
            title: 条目标题
            additional_info: 额外信息

        Returns:
            是否成功
        """
        if not self.project_why_file.exists():
            return False

        with open(self.project_why_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找条目
        pattern = rf'### {re.escape(title)}\n\n(.*?)(?=\n### |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return False

        # 在条目末尾添加信息
        old_content = match.group(0)
        new_content = old_content.rstrip() + f"\n\n**补充** ({datetime.now().strftime('%Y-%m-%d')}):\n{additional_info}\n"

        # 替换
        updated_content = content.replace(old_content, new_content)

        with open(self.project_why_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        return True

    # ========== Why Questions 注入与验证 ==========

    def inject_questions_to_research(self, task_path: str, questions: List[str],
                                     source: str = "template") -> bool:
        """
        将 Why 问题注入到 research.md

        Args:
            task_path: 任务目录路径
            questions: Why 问题列表
            source: 问题来源 ("template" 或 "ai_generated")

        Returns:
            是否成功
        """
        research_path = Path(task_path) / "research.md"

        if not research_path.exists():
            return False

        with open(research_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 生成 Why Questions 内容
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        why_section = self._generate_why_section(questions, timestamp, source)

        # 查找并替换 Why Questions 部分
        # 匹配 "## 4. Why Questions" 到 "## 5." 之间的内容
        pattern = r'(## 4\. Why Questions.*?)(## 5\.)'

        if re.search(pattern, content, re.DOTALL):
            # 替换现有内容
            new_content = re.sub(
                pattern,
                f'{why_section}\n\n\\2',
                content,
                flags=re.DOTALL
            )
        else:
            # 如果没有找到，尝试在文件末尾插入
            new_content = content.rstrip() + '\n\n' + why_section + '\n'

        with open(research_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    def _generate_why_section(self, questions: List[str], timestamp: str,
                              source: str) -> str:
        """生成 Why Questions 部分的 Markdown 内容"""
        lines = [
            "## 4. Why Questions",
            "",
            f"> **状态**: [pending]",
            f"> **生成时间**: {timestamp}",
            f"> **来源**: {source}",
            f"> **问题数量**: {len(questions)}",
            ""
        ]

        for i, question in enumerate(questions, 1):
            lines.extend([
                f"### 4.{i} {question}",
                "",
                "（请在此回答）",
                ""
            ])

        return '\n'.join(lines)

    def mark_why_questions_answered(self, task_path: str) -> bool:
        """
        标记 Why Questions 已回答

        Args:
            task_path: 任务目录路径

        Returns:
            是否成功
        """
        research_path = Path(task_path) / "research.md"

        if not research_path.exists():
            return False

        with open(research_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 更新状态标记
        new_content = re.sub(
            r'> \*\*状态\*\*: \[pending\]',
            '> **状态**: [answered]',
            content
        )

        if new_content == content:
            # 没有变化，可能已经是 answered 或没有该标记
            return False

        with open(research_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    def check_why_completion(self, task_path: str) -> Dict[str, any]:
        """
        检查 Why Questions 完成情况

        Args:
            task_path: 任务目录路径

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
            return {
                'has_why_section': False,
                'status': 'missing',
                'total_questions': 0,
                'answered_questions': 0,
                'unanswered': []
            }

        with open(research_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取 Why Questions 部分
        why_match = re.search(
            r'## 4\. Why Questions(.*?)(?=## 5\.|\Z)',
            content, re.DOTALL
        )

        if not why_match:
            return {
                'has_why_section': False,
                'status': 'missing',
                'total_questions': 0,
                'answered_questions': 0,
                'unanswered': []
            }

        why_section = why_match.group(1)

        # 检查状态
        status_match = re.search(r'> \*\*状态\*\*: \[(\w+)\]', why_section)
        status = status_match.group(1).lower() if status_match else 'pending'

        # 统计问题
        question_pattern = r'### 4\.(\d+) (.+?)\n\n(.*?)(?=### 4\.\d+|$)'
        questions = re.findall(question_pattern, why_section, re.DOTALL)
        total = len(questions)

        # 检查每个问题是否有回答
        answered = 0
        unanswered = []

        for _, question_title, answer in questions:
            answer_text = answer.strip()
            # 检查是否有实质内容（非占位符且超过 10 字符）
            if len(answer_text) > 10 and not answer_text.startswith('（'):
                answered += 1
            else:
                unanswered.append(question_title.strip())

        return {
            'has_why_section': True,
            'status': status,
            'total_questions': total,
            'answered_questions': answered,
            'unanswered': unanswered
        }
