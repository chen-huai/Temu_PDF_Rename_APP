# -*- coding: utf-8 -*-
"""
工具函数模块
提供文件操作、工具查找、验证等通用功能
"""
import os
import subprocess
import glob
import hashlib
from typing import Optional, Tuple


def find_signtool(path_config: str = "auto") -> Optional[str]:
    """
    查找signtool.exe
    :param path_config: 路径配置，"auto"表示自动查找，或指定具体路径
    :return: signtool路径，如果未找到返回None
    """
    if path_config != "auto":
        return path_config if os.path.exists(path_config) else None

    try:
        search_paths = [
            r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe",
            r"C:\Program Files\Windows Kits\10\bin\*\x64\signtool.exe"
        ]

        for pattern in search_paths:
            matches = glob.glob(pattern)
            if matches:
                return matches[-1]  # 使用最新版本
    except Exception:
        pass

    return None


def find_osslsigncode(path_config: str = "auto") -> Optional[str]:
    """
    查找osslsigncode
    :param path_config: 路径配置，"auto"表示在PATH中查找，或指定具体路径
    :return: osslsigncode路径，如果未找到返回None
    """
    if path_config != "auto":
        return path_config if os.path.exists(path_config) else None

    # 在PATH中查找
    try:
        result = subprocess.run(['where', 'osslsigncode'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except Exception:
        pass

    return None


def find_signing_tools() -> dict:
    """
    查找所有可用的签名工具
    :return: 工具名称到路径的映射
    """
    tools = {}

    signtool_path = find_signtool()
    if signtool_path:
        tools['signtool'] = signtool_path

    # PowerShell总是可用的
    try:
        subprocess.run(['powershell', '-Command', 'Write-Host test'],
                      capture_output=True, check=True)
        tools['powershell'] = 'powershell'
    except Exception:
        pass

    osslsigncode_path = find_osslsigncode()
    if osslsigncode_path:
        tools['osslsigncode'] = osslsigncode_path

    return tools


def calculate_file_hash(file_path: str) -> str:
    """
    计算文件SHA256哈希
    :param file_path: 文件路径
    :return: 十六进制哈希值
    """
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""


def verify_signature(file_path: str) -> Tuple[bool, str]:
    """
    验证文件签名
    :param file_path: 文件路径
    :return: (是否成功, 消息)
    """
    signtool_path = find_signtool()
    if not signtool_path:
        return False, "[错误] 未找到signtool.exe"

    try:
        cmd = [signtool_path, "verify", "/pa", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr

    except Exception as e:
        return False, f"[错误] 验证异常: {e}"


def is_admin() -> bool:
    """
    检查当前用户是否具有管理员权限
    :return: 是否为管理员
    """
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_certificate_info(sha1_hash: str) -> Optional[dict]:
    """
    获取证书信息
    :param sha1_hash: 证书SHA1哈希
    :return: 证书信息字典，如果获取失败返回None
    """
    try:
        cmd = ['certutil', '-user', '-store', 'My', sha1_hash]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            # 解析证书信息
            info = {}
            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            return info
        else:
            return None
    except Exception:
        return None


def backup_file(file_path: str, backup_dir: str = None) -> str:
    """
    备份文件
    :param file_path: 要备份的文件路径
    :param backup_dir: 备份目录，如果为None则在原文件目录创建backup子目录
    :return: 备份文件路径
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(file_path), "backup")
    os.makedirs(backup_dir, exist_ok=True)

    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    backup_filename = f"{name}_backup_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_filename)

    import shutil
    shutil.copy2(file_path, backup_path)
    return backup_path


def ensure_directory_exists(directory: str):
    """
    确保目录存在，如果不存在则创建
    :param directory: 目录路径
    """
    os.makedirs(directory, exist_ok=True)


def get_file_size(file_path: str) -> int:
    """
    获取文件大小
    :param file_path: 文件路径
    :return: 文件大小（字节）
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    :param size_bytes: 字节数
    :return: 格式化的大小字符串
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def validate_file_path(file_path: str, required_extensions: list = None) -> Tuple[bool, str]:
    """
    验证文件路径
    :param file_path: 文件路径
    :param required_extensions: 要求的文件扩展名列表，如 ['.exe', '.dll']
    :return: (是否有效, 错误信息)
    """
    if not file_path:
        return False, "文件路径不能为空"

    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"

    if not os.path.isfile(file_path):
        return False, f"路径不是文件: {file_path}"

    if required_extensions:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext not in [e.lower() for e in required_extensions]:
            return False, f"不支持的文件类型: {ext}，支持的类型: {', '.join(required_extensions)}"

    return True, ""


def run_command(cmd: list, cwd: str = None, timeout: int = None) -> Tuple[bool, str, str]:
    """
    运行命令
    :param cmd: 命令列表
    :param cwd: 工作目录
    :param timeout: 超时时间（秒）
    :return: (是否成功, 标准输出, 标准错误)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=cwd,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "命令执行超时"
    except Exception as e:
        return False, "", f"命令执行异常: {e}"


def get_system_info() -> dict:
    """
    获取系统信息
    :return: 系统信息字典
    """
    import platform
    return {
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'is_admin': is_admin()
    }