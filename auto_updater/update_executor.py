# -*- coding: utf-8 -*-
"""
更新执行模块
负责执行应用程序的热更新操作
"""

import os
import sys
import time
import subprocess
import shutil
import tempfile
from typing import Optional

from .config import (
    get_app_executable_path,
    get_executable_dir
)
from .config import get_config
from .backup_manager import BackupManager

# 异常类定义
class UpdateExecutionError(Exception):
    """更新执行异常"""
    pass

class UpdateExecutor:
    """更新执行器"""

    def __init__(self):
        self.config = get_config()
        self.backup_manager = BackupManager()

    def execute_update(self, update_file_path: str, new_version: str) -> bool:
        """
        执行应用程序更新
        :param update_file_path: 更新文件路径
        :param new_version: 新版本号
        :return: 是否更新成功
        """
        try:
            # 验证更新文件
            if not os.path.exists(update_file_path):
                raise UpdateExecutionError("更新文件不存在")

            if os.path.getsize(update_file_path) == 0:
                raise UpdateExecutionError("更新文件无效")

            # 获取当前可执行文件路径
            current_exe_path = get_app_executable_path()

            # 如果是开发环境，直接替换文件
            if not getattr(sys, 'frozen', False):
                return self._update_development_environment(update_file_path, new_version)

            # 生产环境（打包后的exe）需要特殊处理
            return self._update_production_environment(update_file_path, new_version)

        except UpdateExecutionError:
            raise
        except Exception as e:
            raise UpdateExecutionError(f"执行更新失败: {str(e)}")

    def _update_development_environment(self, update_file_path: str, new_version: str) -> bool:
        """
        开发环境下的更新（直接替换Python文件）
        :param update_file_path: 更新文件路径
        :param new_version: 新版本号
        :return: 是否更新成功
        """
        try:
            # 在开发环境下，我们只是更新版本号文件
            print(f"开发环境模拟更新: 版本 {new_version}")

            # 更新版本文件
            success = self.config.update_current_version(new_version)
            if success:
                print(f"版本已更新到: {new_version}")
                return True
            else:
                raise UpdateExecutionError("更新版本文件失败")

        except Exception as e:
            raise UpdateExecutionError(f"开发环境更新失败: {str(e)}")

    def _update_production_environment(self, update_file_path: str, new_version: str) -> bool:
        """
        生产环境下的更新（需要处理文件占用）
        :param update_file_path: 更新文件路径
        :param new_version: 新版本号
        :return: 是否更新成功
        """
        try:
            current_exe_path = get_app_executable_path()

            # 创建备份
            backup_path = self.backup_manager.create_backup()
            if not backup_path:
                raise UpdateExecutionError("创建备份失败")

            print(f"已创建备份: {backup_path}")

            # 尝试替换可执行文件
            if not self._replace_executable(update_file_path, current_exe_path):
                # 如果直接替换失败，使用批处理脚本延迟更新
                return self._schedule_delayed_update(update_file_path, current_exe_path, new_version)

            # 更新版本文件
            self.config.update_current_version(new_version)

            print("文件替换成功，更新完成")
            return True

        except Exception as e:
            raise UpdateExecutionError(f"生产环境更新失败: {str(e)}")

    def _replace_executable(self, source_path: str, target_path: str) -> bool:
        """
        替换可执行文件
        :param source_path: 源文件路径
        :param target_path: 目标文件路径
        :return: 是否替换成功
        """
        try:
            # 等待文件释放
            for _ in range(10):  # 最多等待10秒
                try:
                    # 尝试删除目标文件
                    if os.path.exists(target_path):
                        os.remove(target_path)

                    # 复制新文件
                    shutil.copy2(source_path, target_path)

                    # 验证文件是否正确复制
                    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                        return True

                except PermissionError:
                    print("文件被占用，等待释放...")
                    time.sleep(1)
                except Exception as e:
                    print(f"替换文件失败: {e}")
                    time.sleep(1)

            return False

        except Exception as e:
            print(f"替换可执行文件失败: {e}")
            return False

    def _schedule_delayed_update(self, update_file_path: str, current_exe_path: str, new_version: str) -> bool:
        """
        安排延迟更新（使用批处理脚本）
        :param update_file_path: 更新文件路径
        :param current_exe_path: 当前可执行文件路径
        :param new_version: 新版本号
        :return: 是否成功安排延迟更新
        """
        try:
            # 创建更新脚本
            script_content = f'''@echo off
echo 正在更新应用程序...
timeout /t 2 /nobreak >nul

REM 替换可执行文件
copy /Y "{update_file_path}" "{current_exe_path}"

REM 版本信息已通过配置文件更新，无需单独的版本文件

REM 启动新版本
start "" "{current_exe_path}"

REM 清理临时文件
del "{update_file_path}"
del "%~f0"

echo 更新完成！
timeout /t 3 /nobreak >nul
'''

            # 创建临时脚本文件
            script_path = os.path.join(tempfile.gettempdir(), "pdf_update_script.bat")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # 启动更新脚本
            subprocess.Popen([script_path],
                           creationflags=subprocess.DETACHED_PROCESS,
                           env=os.environ.copy(),
                           encoding='utf-8')

            print("已安排延迟更新，应用程序将重启")
            return True

        except Exception as e:
            raise UpdateExecutionError(f"安排延迟更新失败: {str(e)}")

    def restart_application(self) -> bool:
        """
        重启应用程序
        :return: 是否成功重启
        """
        try:
            if getattr(sys, 'frozen', False):
                # 打包后的exe
                current_exe = sys.executable
                subprocess.Popen([current_exe],
                               env=os.environ.copy(),
                               encoding='utf-8')
            else:
                # 开发环境
                current_script = sys.argv[0]
                subprocess.Popen([sys.executable, current_script],
                               env=os.environ.copy(),
                               encoding='utf-8')

            # 退出当前进程
            sys.exit(0)

        except Exception as e:
            print(f"重启应用程序失败: {e}")
            return False

    def rollback_update(self) -> bool:
        """
        回滚到上一个版本
        :return: 是否回滚成功
        """
        try:
            # 获取最新备份
            latest_backup = self.backup_manager.get_latest_backup()
            if not latest_backup:
                raise UpdateExecutionError("没有找到可用的备份文件")

            # 从备份恢复
            success = self.backup_manager.restore_from_backup(latest_backup)
            if not success:
                raise UpdateExecutionError("从备份恢复失败")

            # 更新版本文件
            # 注意：这里需要根据实际情况确定如何获取备份的版本号
            # 暂时使用本地版本管理器的当前版本

            print("回滚成功")
            return True

        except Exception as e:
            raise UpdateExecutionError(f"回滚失败: {str(e)}")

    def validate_update_file(self, update_file_path: str) -> tuple:
        """
        验证更新文件的有效性
        :param update_file_path: 更新文件路径
        :return: (是否有效, 错误信息)
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(update_file_path):
                return False, "更新文件不存在"

            # 检查文件大小
            file_size = os.path.getsize(update_file_path)
            if file_size == 0:
                return False, "更新文件为空"

            # 检查文件扩展名
            if not (update_file_path.endswith('.exe') or update_file_path.endswith('.zip')):
                return False, "更新文件格式不正确"

            # 基本可执行文件检查
            if update_file_path.endswith('.exe'):
                try:
                    # 检查PE文件头（简单检查）
                    with open(update_file_path, 'rb') as f:
                        header = f.read(2)
                        if header != b'MZ':  # DOS header
                            return False, "更新文件不是有效的可执行文件"
                except Exception as e:
                    return False, f"读取更新文件失败: {str(e)}"

            return True, "更新文件有效"

        except Exception as e:
            return False, f"验证更新文件失败: {str(e)}"

    def get_update_progress_info(self) -> dict:
        """
        获取更新进度信息
        :return: 进度信息字典
        """
        return {
            'is_updating': False,  # 是否正在更新
            'current_step': '',    # 当前步骤
            'progress': 0,         # 进度百分比
            'error_message': ''    # 错误信息
        }