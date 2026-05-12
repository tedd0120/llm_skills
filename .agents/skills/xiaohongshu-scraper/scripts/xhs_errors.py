"""
小红书抓取异常定义

提供细粒度的异常类型，便于调用方区分错误类型并采取相应策略：
- LoginError: 需要重新登录
- RateLimitError: 触发风控，需要等待或更换策略
- SelectorError: 页面改版，选择器失效
- NetworkError: 网络/超时问题，可重试
"""

from typing import Optional


class XHSError(Exception):
    """小红书抓取基础异常"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class LoginError(XHSError):
    """登录相关错误

    表示需要重新登录才能继续操作。

    可能原因：
    - Cookie 过期
    - 账号被登出
    - 需要扫码验证
    """
    pass


class RateLimitError(XHSError):
    """风控限流错误

    表示检测到异常行为，被限流。

    可能原因：
    - 请求频率过高
    - 同一账号多设备登录
    - 爬虫行为被识别

    建议：等待一段时间后重试，或更换账号。
    """
    pass


class SelectorError(XHSError):
    """选择器失效错误

    表示页面改版导致选择器无法匹配。

    可能原因：
    - 小红书页面结构变更
    - CSS 类名随机化

    建议：检查页面 DOM 并更新选择器。
    """
    pass


class NetworkError(XHSError):
    """网络相关错误

    表示网络连接或超时问题。

    可能原因：
    - 网络连接超时
    - DNS 解析失败
    - 服务器无响应

    建议：检查网络连接后重试。
    """
    pass
