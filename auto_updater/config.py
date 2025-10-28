# -*- coding: utf-8 -*-
"""
自动更新配置模块
提供更新功能的全局配置和常量定义
使用内置配置常量，消除外部文件依赖
集成版本管理功能，提供完整的配置和版本管理
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from packaging import version

# 导入配置常量
from .config_constants import (
    APP_NAME, APP_EXECUTABLE, GITHUB_OWNER, GITHUB_REPO, GITHUB_API_BASE,
    CURRENT_VERSION, UPDATE_CHECK_INTERVAL_DAYS, AUTO_CHECK_ENABLED,
    MAX_BACKUP_COUNT, DOWNLOAD_TIMEOUT, MAX_RETRIES, AUTO_RESTART,
    REQUEST_HEADERS, DEFAULT_CONFIG, GITHUB_REPO_PATH,
    GITHUB_RELEASES_URL, GITHUB_LATEST_RELEASE_URL
)

# 配置文件名（保持兼容性）
UPDATE_STATE_FILE = "update_state.json"
DEFAULT_UPDATE_CONFIG_FILE = "update_config.json"  # 默认更新配置文件名

class Config:
    """配置管理类 - 使用内置配置常量"""

    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()  # 直接使用预定义的配置
        self._version_cache = {}  # 版本解析缓存

    @property
    def github_repo(self) -> str:
        """GitHub仓库路径"""
        repo = self._config.get("repository", {})
        return f"{repo.get('owner', 'your-username')}/{repo.get('repo', 'your-repo')}"

    @property
    def github_api_base(self) -> str:
        """GitHub API基础URL"""
        return self._config.get("repository", {}).get("api_base", GITHUB_API_BASE)

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
        return self._config.get("version", {}).get("check_interval_days", UPDATE_CHECK_INTERVAL_DAYS)

    @property
    def max_backup_count(self) -> int:
        """最大备份数量"""
        return self._config.get("update", {}).get("backup_count", MAX_BACKUP_COUNT)

    @property
    def download_timeout(self) -> int:
        """下载超时时间（秒）"""
        return self._config.get("update", {}).get("download_timeout", DOWNLOAD_TIMEOUT)

    @property
    def app_name(self) -> str:
        """应用可执行文件名"""
        return self._config.get("app", {}).get("executable", APP_EXECUTABLE)


    @property
    def request_headers(self) -> dict:
        """网络请求头"""
        return self._config.get("network", {}).get("request_headers", REQUEST_HEADERS)

    @property
    def current_version(self) -> str:
        """当前版本号"""
        return self._config.get("version", {}).get("current", "1.0.0")

    @property
    def github_owner(self) -> str:
        """GitHub仓库所有者"""
        return self._config.get("repository", {}).get("owner", "your-username")

    @property
    def github_repo_name(self) -> str:
        """GitHub仓库名称"""
        return self._config.get("repository", {}).get("repo", "your-repo")

    @property
    def is_valid_version(self) -> bool:
        """验证当前版本号格式是否有效"""
        parsed_version = self._parse_version(self.current_version)
        return parsed_version is not None

    def update_current_version(self, new_version: str) -> bool:
        """
        更新配置文件中的版本号
        :param new_version: 新版本号
        :return: 是否更新成功
        """
        try:
            self._config["version"]["current"] = new_version
            # 清除版本缓存以确保一致性
            self._version_cache.clear()
            self._save_config()
            return True
        except Exception as e:
            print(f"更新版本号失败: {e}")
            return False

    def _save_config(self) -> bool:
        """
        保存配置到文件
        :return: 是否保存成功
        """
        try:
            if getattr(sys, 'frozen', False):
                exec_dir = os.path.dirname(sys.executable)
            else:
                exec_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            config_path = os.path.join(exec_dir, UPDATER_CONFIG_FILE)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def _parse_version(self, version_str: str):
        """解析版本号（带缓存）"""
        if version_str not in self._version_cache:
            try:
                self._version_cache[version_str] = version.parse(version_str.lstrip('v'))
            except Exception:
                self._version_cache[version_str] = None
        return self._version_cache[version_str]

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号
        :param version1: 版本号1
        :param version2: 版本号2
        :return: -1(v1<v2), 0(v1=v2), 1(v1>v2)
        """
        try:
            v1 = self._parse_version(version1)
            v2 = self._parse_version(version2)

            if v1 is None or v2 is None:
                print(f"版本比较失败: 无效的版本号")
                return 0

            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
        except Exception as e:
            print(f"版本比较失败: {e}")
            return 0

    def is_newer_version(self, remote_version: str, local_version: str = None) -> bool:
        """
        检查远程版本是否比本地版本新
        :param remote_version: 远程版本号
        :param local_version: 本地版本号（可选）
        :return: 是否有更新
        """
        if local_version is None:
            local_version = self.current_version

        return self.compare_versions(remote_version, local_version) > 0

    def get_last_check_time(self) -> Optional[datetime]:
        """
        获取上次检查更新的时间
        :return: 上次检查时间，如果没有则返回None
        """
        try:
            state = self._load_state()
            last_check_str = state.get('last_check_date')
            if last_check_str:
                return datetime.fromisoformat(last_check_str)
        except Exception as e:
            print(f"读取上次检查时间失败: {e}")
        return None

    def should_check_for_updates(self) -> bool:
        """
        检查是否应该进行更新检查（基于时间间隔）
        :return: 是否应该检查更新
        """
        last_check = self.get_last_check_time()
        if last_check is None:
            return True

        # 检查距离上次检查是否超过配置的间隔天数
        time_since_last_check = datetime.now() - last_check
        return time_since_last_check.days >= self.update_check_interval_days

    def update_last_check_time(self) -> bool:
        """
        更新最后检查时间
        :return: 是否更新成功
        """
        try:
            state = self._load_state()
            state['last_check_date'] = datetime.now().isoformat()
            self._save_state(state)
            return True
        except Exception as e:
            print(f"更新检查时间失败: {e}")
            return False

    def _load_state(self) -> dict:
        """加载状态文件"""
        try:
            if getattr(sys, 'frozen', False):
                exec_dir = os.path.dirname(sys.executable)
            else:
                exec_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            state_path = os.path.join(exec_dir, UPDATE_STATE_FILE)
            if os.path.exists(state_path):
                with open(state_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"加载状态文件失败: {e}")
            return {}

    def _save_state(self, state: dict) -> bool:
        """保存状态文件"""
        try:
            if getattr(sys, 'frozen', False):
                exec_dir = os.path.dirname(sys.executable)
            else:
                exec_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            state_path = os.path.join(exec_dir, UPDATE_STATE_FILE)
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存状态文件失败: {e}")
            return False

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

# GitHub配置 - 直接使用配置常量
GITHUB_REPO = GITHUB_REPO_PATH
GITHUB_API_BASE = GITHUB_API_BASE
GITHUB_RELEASES_URL = GITHUB_RELEASES_URL
GITHUB_LATEST_RELEASE_URL = GITHUB_LATEST_RELEASE_URL

# 更新配置 - 直接使用配置常量
UPDATE_CHECK_INTERVAL_DAYS = UPDATE_CHECK_INTERVAL_DAYS
MAX_BACKUP_COUNT = MAX_BACKUP_COUNT
DOWNLOAD_TIMEOUT = DOWNLOAD_TIMEOUT

# 文件配置 - 直接使用配置常量
APP_NAME = APP_EXECUTABLE
UPDATE_CONFIG_FILE = DEFAULT_UPDATE_CONFIG_FILE  # 保持向后兼容
BACKUP_DIR = "backup"  # 保持向后兼容

# 网络配置 - 直接使用配置常量
REQUEST_HEADERS = REQUEST_HEADERS

# 版本配置 - 直接使用配置常量
CURRENT_VERSION = CURRENT_VERSION

def get_executable_dir():
    """
    获取可执行文件所在目录
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


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