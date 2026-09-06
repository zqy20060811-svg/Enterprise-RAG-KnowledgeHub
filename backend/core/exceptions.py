"""
统一异常定义
"""


class BizException(Exception):
    """业务异常：用于主动抛出业务逻辑错误"""

    def __init__(self, msg: str = "业务错误", code: int = 400):
        self.code = code
        self.msg = msg
        super().__init__(msg)
