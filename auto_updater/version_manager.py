# -*- coding: utf-8 -*-
"""
版本管理模块
负责版本号的读取、比较和更新检查逻辑
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
from packaging import version

from .config import (
    CURRENT_VERSION,
    get_version_file_path,
    get_update_config_path,
    UPDATE_CHECK_INTERVAL_DAYS
)

class VersionManager:
    """版本管理器"""

    def __init__(self):
        self.current_version = CURRENT_VERSION
        self._ensure_version_file()

    def _ensure_version_file(self):
        """
        确保版本文件存在
        """
        version_file = get_version_file_path()
        if not os.path.exists(version_file):
            try:
                with open(version_file, 'w', encoding='utf-8') as f:
                    f.write(self.current_version)
            except Exception as e:
                print(f"创建版本文件失败: {e}")

    def get_local_version(self) -> str:
        """
        获取本地版本号
        :return: 本地版本号字符串
        """
        try:
            version_file = get_version_file_path()
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_str = f.read().strip()
                    if version_str:
                        return version_str
            return self.current_version
        except Exception as e:
            print(f"读取本地版本失败: {e}")
            return self.current_version

    def update_local_version(self, new_version: str) -> bool:
        """
        更新本地版本号
        :param new_version: 新版本号
        :return: 是否更新成功
        """
        try:
            version_file = get_version_file_path()
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(new_version)
            self.current_version = new_version
            return True
        except Exception as e:
            print(f"更新本地版本失败: {e}")
            return False

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号
        :param version1: 版本号1
        :param version2: 版本号2
        :return: -1(v1<v2), 0(v1=v2), 1(v1>v2)
        """
        try:
            v1 = version.parse(version1.lstrip('v'))
            v2 = version.parse(version2.lstrip('v'))
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
            local_version = self.get_local_version()

        return self.compare_versions(remote_version, local_version) > 0

    def get_last_check_time(self) -> Optional[datetime]:
        """
        获取上次检查更新的时间
        :return: 上次检查时间，如果没有则返回None
        """
        try:
            config_file = get_update_config_path()
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    last_check_str = config.get('last_check_date')
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
        return time_since_last_check.days >= UPDATE_CHECK_INTERVAL_DAYS

    def update_last_check_time(self) -> bool:
        """
        更新最后检查时间
        :return: 是否更新成功
        """
        try:
            config_file = get_update_config_path()
            config = {}

            # 如果配置文件存在，先读取现有配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # 更新检查时间
            config['last_check_date'] = datetime.now().isoformat()

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"更新检查时间失败: {e}")
            return False

    def is_update_available(self, remote_version: str) -> Tuple[bool, str]:
        """
        检查是否有可用更新
        :param remote_version: 远程版本号
        :return: (是否有更新, 本地版本号)
        """
        local_version = self.get_local_version()

        if not remote_version:
            return False, local_version

        has_update = self.is_newer_version(remote_version, local_version)
        return has_update, local_version