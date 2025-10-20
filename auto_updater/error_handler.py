# -*- coding: utf-8 -*-
"""
统一错误处理模块
提供用户友好的错误信息和异常处理
"""

import traceback
from typing import Optional, Tuple
from enum import Enum

class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "网络连接错误"
    DOWNLOAD_ERROR = "文件下载错误"
    VERSION_ERROR = "版本检查错误"
    BACKUP_ERROR = "备份操作错误"
    UPDATE_ERROR = "更新执行错误"
    PERMISSION_ERROR = "权限不足"
    FILE_ERROR = "文件操作错误"
    CONFIG_ERROR = "配置错误"
    UNKNOWN_ERROR = "未知错误"

class UserFriendlyError:
    """用户友好的错误信息"""

    @staticmethod
    def get_user_message(error_type: ErrorType, technical_details: str = "") -> str:
        """
        获取用户友好的错误信息
        :param error_type: 错误类型
        :param technical_details: 技术细节（用于日志）
        :return: 用户友好的错误信息
        """
        messages = {
            ErrorType.NETWORK_ERROR: "无法连接到更新服务器，请检查网络连接后重试。",
            ErrorType.DOWNLOAD_ERROR: "下载更新文件失败，请稍后重试或联系技术支持。",
            ErrorType.VERSION_ERROR: "版本检查失败，请确保软件版本信息正确。",
            ErrorType.BACKUP_ERROR: "创建备份失败，更新过程可能无法回滚，是否继续？",
            ErrorType.UPDATE_ERROR: "更新过程中发生错误，请重新下载完整程序。",
            ErrorType.PERMISSION_ERROR: "权限不足，请以管理员身份运行程序。",
            ErrorType.FILE_ERROR: "文件操作失败，请确保磁盘空间充足且文件未被占用。",
            ErrorType.CONFIG_ERROR: "配置文件错误，请重新安装程序。",
            ErrorType.UNKNOWN_ERROR: "发生未知错误，请重启程序后重试。"
        }

        return messages.get(error_type, messages[ErrorType.UNKNOWN_ERROR])

    @staticmethod
    def classify_error(exception: Exception) -> ErrorType:
        """
        根据异常类型分类错误
        :param exception: 异常对象
        :return: 错误类型
        """
        error_message = str(exception).lower()

        if "network" in error_message or "connection" in error_message or "timeout" in error_message:
            return ErrorType.NETWORK_ERROR
        elif "download" in error_message or "http" in error_message:
            return ErrorType.DOWNLOAD_ERROR
        elif "version" in error_message or "release" in error_message:
            return ErrorType.VERSION_ERROR
        elif "backup" in error_message:
            return ErrorType.BACKUP_ERROR
        elif "permission" in error_message or "access denied" in error_message:
            return ErrorType.PERMISSION_ERROR
        elif "file" in error_message or "directory" in error_message:
            return ErrorType.FILE_ERROR
        elif "config" in error_message or "json" in error_message:
            return ErrorType.CONFIG_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR

class ErrorHandler:
    """错误处理器"""

    @staticmethod
    def handle_exception(exception: Exception, context: str = "") -> Tuple[str, ErrorType]:
        """
        处理异常并返回用户友好的错误信息
        :param exception: 异常对象
        :param context: 上下文信息
        :return: (用户友好的错误信息, 错误类型)
        """
        try:
            # 分类错误
            error_type = UserFriendlyError.classify_error(exception)

            # 获取用户友好的错误信息
            user_message = UserFriendlyError.get_user_message(error_type)

            # 记录技术详情到日志
            technical_details = f"Context: {context}\nException: {exception}\nTraceback: {traceback.format_exc()}"
            print(f"技术错误详情:\n{technical_details}")

            return user_message, error_type

        except Exception as e:
            # 如果错误处理本身出错，返回基本错误信息
            return f"处理错误时发生异常: {str(e)}", ErrorType.UNKNOWN_ERROR

    @staticmethod
    def log_error(error_type: ErrorType, message: str, technical_details: str = ""):
        """
        记录错误日志
        :param error_type: 错误类型
        :param message: 错误消息
        :param technical_details: 技术细节
        """
        import logging
        logger = logging.getLogger(__name__)

        log_message = f"[{error_type.value}] {message}"
        if technical_details:
            log_message += f"\n技术详情: {technical_details}"

        logger.error(log_message)