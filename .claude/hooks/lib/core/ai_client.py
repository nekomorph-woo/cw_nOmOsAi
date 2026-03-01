"""
AI 客户端模块 - 提供 AI 调用能力

l3_foundation 基础能力层核心模块
轻量级 AI 客户端 - 零配置设计
"""

import os
import json
import hashlib
import time
import ssl
import urllib.request
import urllib.error
from typing import Optional, Dict


class AIClient:
    """
    轻量级 AI 客户端 - 零配置设计

    环境变量 (优先级递减):
      API Key: ANTHROPIC_API_KEY > ANTHROPIC_AUTH_TOKEN > NOMOS_API_KEY
      Base URL: ANTHROPIC_BASE_URL > NOMOS_API_BASE_URL
      Model: ANTHROPIC_DEFAULT_HAIKU_MODEL > DEFAULT_HAIKU_MODEL
      Timeout: NOMOS_AI_TIMEOUT (默认 30 秒)
    """

    _instance = None
    _initialized = False

    # 默认配置
    DEFAULT_MODEL = "claude-3-5-haiku-20241022"
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 AI 客户端"""
        if self._initialized:
            return

        # 读取 API Key
        self.api_key = (
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("ANTHROPIC_AUTH_TOKEN") or
            os.environ.get("NOMOS_API_KEY") or
            os.environ.get("CLAUDE_API_KEY")
        )

        # 读取 Base URL
        self.base_url = (
            os.environ.get("ANTHROPIC_BASE_URL") or
            os.environ.get("NOMOS_API_BASE_URL") or
            self.DEFAULT_BASE_URL
        )

        # 读取 Model
        self.model = (
            os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL") or
            os.environ.get("DEFAULT_HAIKU_MODEL") or
            os.environ.get("NOMOS_HAIKU_MODEL") or
            self.DEFAULT_MODEL
        )

        # 读取超时
        try:
            self.timeout = int(os.environ.get("NOMOS_AI_TIMEOUT", str(self.DEFAULT_TIMEOUT)))
        except ValueError:
            self.timeout = self.DEFAULT_TIMEOUT

        # 可用性标志
        self._available = self.api_key is not None

        # 简单内存缓存 (hash -> result)
        self._cache: Dict[str, Dict] = {}
        self._cache_max_size = 100

        self._initialized = True

    @property
    def available(self) -> bool:
        """AI 服务是否可用"""
        return self._available

    def call(self, prompt: str, content: str, max_tokens: int = 512) -> Optional[Dict]:
        """
        调用 AI 进行判断 (带重试机制)

        Args:
            prompt: 系统提示词
            content: 待分析的代码内容
            max_tokens: 最大 token 数

        Returns:
            解析后的 JSON 结果, 或 None (调用失败时)
        """
        if not self._available:
            return None

        # 检查缓存
        cache_key = hashlib.md5(f"{prompt}:{content}".encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 构建请求
        full_prompt = f"{prompt}\n\n---\n代码:\n```\n{content}\n```"

        request_body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": full_prompt}]
        }

        url = f"{self.base_url.rstrip('/')}/v1/messages"

        # 重试机制
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                result = self._make_request(url, request_body)

                # 尝试解析 JSON
                try:
                    parsed = json.loads(result)
                except json.JSONDecodeError:
                    # 尝试提取 markdown 代码块中的 JSON
                    import re
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            parsed = {"raw_response": result, "violations": []}
                    else:
                        # AI 返回非 JSON, 包装成标准格式
                        parsed = {"raw_response": result, "violations": []}

                # 写入缓存
                self._cache[cache_key] = parsed
                if len(self._cache) > self._cache_max_size:
                    # 简单 LRU: 清空一半
                    keys = list(self._cache.keys())
                    for k in keys[:len(keys)//2]:
                        del self._cache[k]

                return parsed

            except (urllib.error.URLError, urllib.error.HTTPError,
                    KeyError, TimeoutError, Exception) as e:
                last_error = e
                # 重试前等待 (指数退避)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(1 * (attempt + 1))
                continue

        # 所有重试失败
        return None

    def _make_request(self, url: str, body: Dict) -> str:
        """发起 HTTP 请求"""
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            method="POST"
        )

        # 创建 SSL 上下文 (处理证书验证问题)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result["content"][0]["text"]
