# -*- coding: utf-8 -*-
"""
自动更新配置模块
提供更新功能的全局配置和常量定义
"""

import os
import sys
from pathlib import Path

# GitHub配置
GITHUB_REPO = "chen-huai/Temu_PDF_Rename_APP"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RELEASES_URL = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/releases"
GITHUB_LATEST_RELEASE_URL = f"{GITHUB_RELEASES_URL}/latest"

# 更新配置
UPDATE_CHECK_INTERVAL_DAYS = 30  # 自动更新检查间隔（天）
MAX_BACKUP_COUNT = 3  # 最大备份数量
DOWNLOAD_TIMEOUT = 300  # 下载超时时间（秒）

# 文件配置
APP_NAME = "PDF_Rename_Operation.exe"
VERSION_FILE = "version.txt"
UPDATE_CONFIG_FILE = "update_config.json"
BACKUP_DIR = "backup"

# 网络配置
REQUEST_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "PDF-Rename-Tool-Updater/1.0"
}

# 版本配置
CURRENT_VERSION = "1.0.0"

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