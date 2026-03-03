"""
核心基础设施层

提供系统级基础能力，可被所有模块依赖。
"""

from .ai_client import AIClient

__all__ = ["AIClient"]
