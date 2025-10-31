# -*- coding: utf-8 -*-
"""
自动更新器配置常量
将JSON配置信息转换为Python常量，消除外部文件依赖
"""

# 应用配置
APP_NAME: str = "PDF重命名工具"
APP_EXECUTABLE: str = "PDF_Rename_Operation.exe"

# GitHub仓库配置
GITHUB_OWNER: str = "chen-huai"
GITHUB_REPO: str = "Temu_PDF_Rename_APP"
GITHUB_API_BASE: str = "https://api.github.com"

# 版本配置
CURRENT_VERSION: str = "4.0.2"
UPDATE_CHECK_INTERVAL_DAYS: int = 30
AUTO_CHECK_ENABLED: bool = True

# 更新配置
MAX_BACKUP_COUNT: int = 3
DOWNLOAD_TIMEOUT: int = 300
MAX_RETRIES: int = 3
AUTO_RESTART: bool = True

# 网络配置
REQUEST_HEADERS: dict = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "PDF-Rename-Tool-Updater/1.0"
}

# 便利常量（兼容现有API）
GITHUB_REPO_PATH: str = f"{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_RELEASES_URL: str = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_PATH}/releases"
GITHUB_LATEST_RELEASE_URL: str = f"{GITHUB_RELEASES_URL}/latest"

# 默认配置字典（保持JSON格式兼容）
DEFAULT_CONFIG: dict = {
    "app": {
        "name": APP_NAME,
        "executable": APP_EXECUTABLE
    },
    "repository": {
        "owner": GITHUB_OWNER,
        "repo": GITHUB_REPO,
        "api_base": GITHUB_API_BASE
    },
    "version": {
        "current": CURRENT_VERSION,
        "check_interval_days": UPDATE_CHECK_INTERVAL_DAYS,
        "auto_check_enabled": AUTO_CHECK_ENABLED
    },
    "update": {
        "backup_count": MAX_BACKUP_COUNT,
        "download_timeout": DOWNLOAD_TIMEOUT,
        "max_retries": MAX_RETRIES,
        "auto_restart": AUTO_RESTART
    },
    "network": {
        "request_headers": REQUEST_HEADERS
    }
}

# 版本信息验证
def validate_version_format(version_str: str) -> bool:
    """验证版本号格式是否有效"""
    try:
        from packaging import version as pkg_version
        pkg_version.parse(version_str)
        return True
    except Exception:
        return False

# 配置完整性验证
def validate_config() -> bool:
    """验证配置信息的完整性"""
    try:
        # 验证必要常量
        required_constants = [
            APP_NAME, APP_EXECUTABLE, GITHUB_OWNER, GITHUB_REPO,
            GITHUB_API_BASE, CURRENT_VERSION, REQUEST_HEADERS
        ]

        for const in required_constants:
            if not const:
                return False

        # 验证版本号格式
        if not validate_version_format(CURRENT_VERSION):
            return False

        # 验证URL格式
        if not GITHUB_API_BASE.startswith("https://"):
            return False

        return True
    except Exception:
        return False

# 在模块加载时验证配置
if not validate_config():
    raise ValueError("配置信息验证失败，请检查config_constants.py中的配置")