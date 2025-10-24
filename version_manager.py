# -*- coding: utf-8 -*-
"""
统一版本管理模块
实现单一数据源的版本控制，确保所有版本信息同步更新
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VersionManager:
    """统一版本管理器 - 配置文件驱动的版本控制"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化版本管理器
        :param config_file: 配置文件路径，默认使用根目录的updater_config.json
        """
        if config_file is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(current_dir, "updater_config.json")

        self.config_file = config_file
        self._config = self._load_config()

        # 保持向后兼容的版本文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.version_file = os.path.join(current_dir, "version.txt")
        self._ensure_version_file_exists()

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 如果配置文件不存在，使用默认配置
                logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "app": {
                "name": "PDF重命名工具",
                "executable": "PDF_Rename_Operation.exe"
            },
            "version": {
                "current": "1.0.0"
            },
            "update": {
                "check_interval_days": 30,
                "backup_count": 3
            }
        }

    @property
    def CURRENT_VERSION(self) -> str:
        """当前版本号（从配置文件读取）"""
        try:
            return self._config.get("version", {}).get("current", "1.0.0")
        except Exception:
            return "1.0.0"

    def _ensure_version_file_exists(self):
        """确保版本文件存在且内容正确"""
        try:
            if not os.path.exists(self.version_file):
                self._save_version_to_file()
            else:
                # 验证文件中的版本是否与代码中的版本一致
                file_version = self._read_version_from_file()
                if file_version != self.CURRENT_VERSION:
                    logger.warning(f"版本文件({file_version})与代码版本({self.CURRENT_VERSION})不一致，已同步")
                    self._save_version_to_file()
        except Exception as e:
            logger.error(f"处理版本文件失败: {e}")

    def _read_version_from_file(self) -> str:
        """从文件读取版本号"""
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"读取版本文件失败: {e}")
            return self.CURRENT_VERSION

    def _save_version_to_file(self):
        """保存版本号到文件"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                f.write(self.CURRENT_VERSION)
            logger.info(f"版本文件已更新: {self.CURRENT_VERSION}")
        except Exception as e:
            logger.error(f"保存版本文件失败: {e}")

    def get_version(self) -> str:
        """
        获取当前版本号
        :return: 版本字符串
        """
        return self.CURRENT_VERSION

    def get_version_display_text(self) -> str:
        """
        获取UI显示的版本文本
        :return: 格式化的版本文本
        """
        return f"Version v{self.CURRENT_VERSION}"

    def get_about_dialog_title(self) -> str:
        """
        获取关于对话框标题
        :return: 包含版本的标题
        """
        return f"关于 PDF重命名工具 v{self.CURRENT_VERSION}"

    def update_app_version(self, new_version: str):
        """
        更新应用版本号
        这是唯一应该修改版本号的地方
        :param new_version: 新版本号
        """
        try:
            # 验证版本号格式
            if not self._is_valid_version_format(new_version):
                raise ValueError(f"无效的版本号格式: {new_version}")

            # 更新代码中的版本常量
            old_version = self.CURRENT_VERSION

            # 这里需要直接修改源代码文件
            self._update_source_version_file(new_version)

            logger.info(f"版本已更新: {old_version} → {new_version}")

        except Exception as e:
            logger.error(f"更新版本失败: {e}")
            raise

    def _update_source_version_file(self, new_version: str):
        """更新源代码文件中的版本常量"""
        try:
            # 更新版本管理器本身
            source_file = os.path.abspath(__file__)
            self._update_version_in_file(source_file, 'CURRENT_VERSION = ', new_version)

            # 更新主程序文件
            main_file = os.path.join(os.path.dirname(__file__), 'PDF_Rename_Operation.py')
            self._update_version_in_file(main_file, 'CURRENT_VERSION = ', new_version)

        except Exception as e:
            logger.error(f"更新源代码版本失败: {e}")
            raise

    def _update_version_in_file(self, file_path: str, pattern: str, new_version: str):
        """在文件中更新版本号"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找并替换版本行
            lines = content.split('\n')
            updated_lines = []

            for line in lines:
                if pattern in line and '=' in line:
                    # 找到版本定义行，更新版本号
                    updated_line = f'{pattern}"{new_version}"'
                    updated_lines.append(updated_line)
                    logger.debug(f"更新 {file_path}: {line} → {updated_line}")
                else:
                    updated_lines.append(line)

            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(updated_lines))

        except Exception as e:
            logger.error(f"更新文件 {file_path} 中的版本失败: {e}")
            raise

    def _is_valid_version_format(self, version: str) -> bool:
        """验证版本号格式"""
        try:
            parts = version.split('.')
            if len(parts) < 2:
                return False
            for part in parts:
                if not part.isdigit():
                    return False
            return True
        except:
            return False

    def get_all_version_info(self) -> dict:
        """
        获取所有版本相关信息
        :return: 版本信息字典
        """
        return {
            'version': self.get_version(),
            'display_text': self.get_version_display_text(),
            'about_title': self.get_about_dialog_title(),
            'version_file': self.version_file,
            'file_exists': os.path.exists(self.version_file),
            'file_version': self._read_version_from_file() if os.path.exists(self.version_file) else None
        }

    def sync_all_versions(self):
        """同步所有版本信息"""
        try:
            # 确保版本文件与代码版本一致
            if self._read_version_from_file() != self.CURRENT_VERSION:
                self._save_version_to_file()

            # 更新配置文件
            self._update_config_files()

            logger.info("所有版本信息已同步")

        except Exception as e:
            logger.error(f"同步版本信息失败: {e}")
            raise

    def _update_config_files(self):
        """更新配置文件中的版本信息"""
        try:
            # 更新自动更新配置
            config_file = os.path.join(os.path.dirname(__file__), 'update_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                if config.get('current_version') != self.CURRENT_VERSION:
                    config['current_version'] = self.CURRENT_VERSION

                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)

                    logger.info("配置文件版本已更新")

        except Exception as e:
            logger.error(f"更新配置文件失败: {e}")


# 全局版本管理器实例
_version_manager = None

def get_version_manager() -> VersionManager:
    """获取全局版本管理器实例"""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager

def get_version() -> str:
    """获取当前版本号"""
    return get_version_manager().get_version()

def get_version_display_text() -> str:
    """获取版本显示文本"""
    return get_version_manager().get_version_display_text()

# 便捷函数，用于其他模块导入
def update_app_version(new_version: str):
    """更新应用版本 - 统一的版本更新入口"""
    get_version_manager().update_app_version(new_version)