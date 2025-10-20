# -*- coding: utf-8 -*-
"""
PDF重命名工具自动更新模块
提供基于GitHub Releases的自动更新功能
"""

from .version_manager import VersionManager
from .github_client import GitHubClient
from .download_manager import DownloadManager
from .backup_manager import BackupManager
from .update_executor import UpdateExecutor
from .config import *

# 自定义异常类
class UpdateError(Exception):
    """更新功能基础异常"""
    pass

class NetworkError(UpdateError):
    """网络连接异常"""
    pass

class VersionCheckError(UpdateError):
    """版本检查异常"""
    pass

class DownloadError(UpdateError):
    """文件下载异常"""
    pass

class BackupError(UpdateError):
    """备份操作异常"""
    pass

class UpdateExecutionError(UpdateError):
    """更新执行异常"""
    pass

# 主要接口类
class AutoUpdater:
    """
    自动更新器主类
    整合所有更新功能组件，提供统一的更新接口
    """

    def __init__(self, parent=None):
        """
        初始化自动更新器
        :param parent: 父对象（用于GUI信号连接）
        """
        self.version_manager = VersionManager()
        self.github_client = GitHubClient()
        self.download_manager = DownloadManager()
        self.backup_manager = BackupManager()
        self.update_executor = UpdateExecutor()
        self.parent = parent

    def check_for_updates(self, force_check=False) -> tuple:
        """
        检查更新
        :param force_check: 是否强制检查（忽略时间间隔）
        :return: (是否有更新, 远程版本, 本地版本, 错误信息)
        """
        try:
            # 检查是否应该进行更新检查
            if not force_check and not self.version_manager.should_check_for_updates():
                local_version = self.version_manager.get_local_version()
                return False, None, local_version, "距离上次检查时间过短"

            # 获取远程版本信息
            release_info = self.github_client.get_latest_release()
            if not release_info:
                local_version = self.version_manager.get_local_version()
                return False, None, local_version, "无法获取远程版本信息"

            remote_version = release_info.get('tag_name', '').lstrip('v')
            if not remote_version:
                local_version = self.version_manager.get_local_version()
                return False, None, local_version, "远程版本格式无效"

            # 检查是否有更新
            has_update, local_version = self.version_manager.is_update_available(remote_version)

            # 更新最后检查时间
            self.version_manager.update_last_check_time()

            return has_update, remote_version, local_version, None

        except Exception as e:
            local_version = self.version_manager.get_local_version()
            return False, None, local_version, f"检查更新失败: {str(e)}"

    def download_update(self, version: str, progress_callback=None) -> tuple:
        """
        下载更新文件
        :param version: 要下载的版本号
        :param progress_callback: 进度回调函数
        :return: (是否成功, 下载文件路径, 错误信息)
        """
        try:
            # 获取下载链接
            download_url = self.github_client.get_download_url(version)
            if not download_url:
                return False, None, "无法获取下载链接"

            # 创建备份
            backup_path = self.backup_manager.create_backup()
            if not backup_path:
                return False, None, "创建备份失败"

            # 下载文件
            downloaded_file = self.download_manager.download_file(
                download_url,
                version,
                progress_callback
            )

            if downloaded_file:
                return True, downloaded_file, None
            else:
                return False, None, "下载失败"

        except Exception as e:
            return False, None, f"下载更新失败: {str(e)}"

    def execute_update(self, update_file_path: str) -> tuple:
        """
        执行更新
        :param update_file_path: 更新文件路径
        :return: (是否成功, 错误信息)
        """
        try:
            success = self.update_executor.execute_update(update_file_path)
            if success:
                return True, None
            else:
                return False, "更新执行失败"

        except Exception as e:
            return False, f"执行更新异常: {str(e)}"

    def rollback_update(self) -> tuple:
        """
        回滚更新
        :return: (是否成功, 错误信息)
        """
        try:
            success = self.backup_manager.restore_from_backup()
            if success:
                return True, None
            else:
                return False, "回滚失败"

        except Exception as e:
            return False, f"回滚异常: {str(e)}"

# 导出的公共接口
__all__ = [
    'AutoUpdater',
    'VersionManager',
    'GitHubClient',
    'DownloadManager',
    'BackupManager',
    'UpdateExecutor',
    'UpdateError',
    'NetworkError',
    'VersionCheckError',
    'DownloadError',
    'BackupError',
    'UpdateExecutionError'
]