# -*- coding: utf-8 -*-
"""
自动更新配置模块
提供更新功能的全局配置和常量定义
支持从外部配置文件读取项目特定信息
"""

import os
import sys
import json
from pathlib import Path

# 默认配置（如果配置文件不存在时使用）
DEFAULT_GITHUB_REPO = "your-username/your-repo"
DEFAULT_GITHUB_API_BASE = "https://api.github.com"
DEFAULT_UPDATE_CHECK_INTERVAL_DAYS = 30
DEFAULT_MAX_BACKUP_COUNT = 3
DEFAULT_DOWNLOAD_TIMEOUT = 300
DEFAULT_APP_NAME = "your_app.exe"
DEFAULT_VERSION_FILE = "version.txt"
DEFAULT_UPDATE_CONFIG_FILE = "update_config.json"
DEFAULT_BACKUP_DIR = "backup"

# 默认网络配置
DEFAULT_REQUEST_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "App-Updater/1.0"
}

# 配置文件名
UPDATER_CONFIG_FILE = "updater_config.json"

class Config:
    """配置管理类 - 从配置文件加载项目特定信息"""

    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            # 手动获取可执行文件目录
            if getattr(sys, 'frozen', False):
                exec_dir = os.path.dirname(sys.executable)
            else:
                exec_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            config_path = os.path.join(exec_dir, UPDATER_CONFIG_FILE)
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 如果配置文件不存在，返回默认配置
                return self._get_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "app": {
                "name": "默认应用",
                "executable": DEFAULT_APP_NAME,
                "version_file": DEFAULT_VERSION_FILE
            },
            "repository": {
                "owner": "your-username",
                "repo": "your-repo",
                "api_base": DEFAULT_GITHUB_API_BASE
            },
            "version": {
                "current": "1.0.0",
                "check_interval_days": DEFAULT_UPDATE_CHECK_INTERVAL_DAYS,
                "auto_check_enabled": True
            },
            "update": {
                "backup_count": DEFAULT_MAX_BACKUP_COUNT,
                "download_timeout": DEFAULT_DOWNLOAD_TIMEOUT,
                "max_retries": 3,
                "auto_restart": True
            },
            "network": {
                "request_headers": DEFAULT_REQUEST_HEADERS
            }
        }

    @property
    def github_repo(self) -> str:
        """GitHub仓库路径"""
        repo = self._config.get("repository", {})
        return f"{repo.get('owner', 'your-username')}/{repo.get('repo', 'your-repo')}"

    @property
    def github_api_base(self) -> str:
        """GitHub API基础URL"""
        return self._config.get("repository", {}).get("api_base", DEFAULT_GITHUB_API_BASE)

    @property
    def github_releases_url(self) -> str:
        """GitHub Releases API URL"""
        return f"{self.github_api_base}/repos/{self.github_repo}/releases"

    @property
    def github_latest_release_url(self) -> str:
        """GitHub最新Release API URL"""
        return f"{self.github_releases_url}/latest"

    @property
    def update_check_interval_days(self) -> int:
        """更新检查间隔（天）"""
        return self._config.get("version", {}).get("check_interval_days", DEFAULT_UPDATE_CHECK_INTERVAL_DAYS)

    @property
    def max_backup_count(self) -> int:
        """最大备份数量"""
        return self._config.get("update", {}).get("backup_count", DEFAULT_MAX_BACKUP_COUNT)

    @property
    def download_timeout(self) -> int:
        """下载超时时间（秒）"""
        return self._config.get("update", {}).get("download_timeout", DEFAULT_DOWNLOAD_TIMEOUT)

    @property
    def app_name(self) -> str:
        """应用可执行文件名"""
        return self._config.get("app", {}).get("executable", DEFAULT_APP_NAME)

    @property
    def version_file(self) -> str:
        """版本文件名"""
        return self._config.get("app", {}).get("version_file", DEFAULT_VERSION_FILE)

    @property
    def request_headers(self) -> dict:
        """网络请求头"""
        return self._config.get("network", {}).get("request_headers", DEFAULT_REQUEST_HEADERS)

    @property
    def current_version(self) -> str:
        """当前版本号"""
        return self._config.get("version", {}).get("current", "1.0.0")

# 全局配置实例
_config = None

def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config

# 保持向后兼容的全局变量（现在从配置文件读取）
def _get_config_value(attr_name: str, default_value=None):
    """获取配置值的辅助函数"""
    try:
        return getattr(get_config(), attr_name)
    except Exception:
        return default_value

# GitHub配置
GITHUB_REPO = _get_config_value('github_repo', DEFAULT_GITHUB_REPO)
GITHUB_API_BASE = _get_config_value('github_api_base', DEFAULT_GITHUB_API_BASE)
GITHUB_RELEASES_URL = _get_config_value('github_releases_url', f"{DEFAULT_GITHUB_API_BASE}/repos/{DEFAULT_GITHUB_REPO}/releases")
GITHUB_LATEST_RELEASE_URL = _get_config_value('github_latest_release_url', f"{GITHUB_RELEASES_URL}/latest")

# 更新配置
UPDATE_CHECK_INTERVAL_DAYS = _get_config_value('update_check_interval_days', DEFAULT_UPDATE_CHECK_INTERVAL_DAYS)
MAX_BACKUP_COUNT = _get_config_value('max_backup_count', DEFAULT_MAX_BACKUP_COUNT)
DOWNLOAD_TIMEOUT = _get_config_value('download_timeout', DEFAULT_DOWNLOAD_TIMEOUT)

# 文件配置
APP_NAME = _get_config_value('app_name', DEFAULT_APP_NAME)
VERSION_FILE = _get_config_value('version_file', DEFAULT_VERSION_FILE)
UPDATE_CONFIG_FILE = DEFAULT_UPDATE_CONFIG_FILE  # 保持向后兼容
BACKUP_DIR = DEFAULT_BACKUP_DIR  # 保持向后兼容

# 网络配置
REQUEST_HEADERS = _get_config_value('request_headers', DEFAULT_REQUEST_HEADERS)

# 版本配置
CURRENT_VERSION = _get_config_value('current_version', "1.0.0")

def get_executable_dir():
    """
    获取可执行文件所在目录
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_version_file_path():
    """
    获取版本文件路径
    """
    return os.path.join(get_executable_dir(), VERSION_FILE)

def get_update_config_path():
    """
    获取更新配置文件路径
    """
    return os.path.join(get_executable_dir(), UPDATE_CONFIG_FILE)

def get_backup_dir():
    """
    获取备份目录路径
    """
    backup_dir = os.path.join(get_executable_dir(), BACKUP_DIR)
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def get_app_executable_path():
    """
    获取应用程序可执行文件路径
    """
    return os.path.join(get_executable_dir(), APP_NAME)