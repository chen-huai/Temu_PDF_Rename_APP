# -*- coding: utf-8 -*-
"""
文件下载管理模块
负责下载更新文件、验证文件完整性和显示下载进度
"""

import os
import requests
import hashlib
import time
from typing import Optional, Callable
from urllib.parse import urlparse

from .config import (
    DOWNLOAD_TIMEOUT,
    get_executable_dir,
    APP_NAME
)

# 异常类定义
class DownloadError(Exception):
    """文件下载异常"""
    pass

class DownloadManager:
    """文件下载管理器"""

    def __init__(self):
        self.session = requests.Session()
        # 设置用户代理
        self.session.headers.update({
            'User-Agent': 'PDF-Rename-Tool-Updater/1.0'
        })

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的SHA256哈希值
        :param file_path: 文件路径
        :return: SHA256哈希值
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # 分块读取文件以避免内存问题
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            raise DownloadError(f"计算文件哈希失败: {str(e)}")

    def _verify_file_integrity(self, file_path: str, expected_hash: Optional[str] = None) -> bool:
        """
        验证文件完整性
        :param file_path: 文件路径
        :param expected_hash: 期望的哈希值（可选）
        :return: 文件是否完整
        """
        try:
            if not os.path.exists(file_path):
                return False

            # 检查文件大小
            if os.path.getsize(file_path) == 0:
                return False

            # 如果提供了期望的哈希值，进行哈希验证
            if expected_hash:
                calculated_hash = self._calculate_file_hash(file_path)
                return calculated_hash.lower() == expected_hash.lower()

            # 基本完整性检查：文件不为空且可以读取
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)  # 尝试读取第一个字节
                return True
            except Exception:
                return False

        except Exception as e:
            raise DownloadError(f"验证文件完整性失败: {str(e)}")

    def download_file(self, url: str, version: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        下载文件
        :param url: 下载链接
        :param version: 版本号
        :param progress_callback: 进度回调函数 (downloaded, total, percentage)
        :return: 下载的文件路径，失败返回None
        """
        try:
            # 验证URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise DownloadError("无效的下载链接")

            # 创建下载目录
            download_dir = os.path.join(get_executable_dir(), "downloads")
            os.makedirs(download_dir, exist_ok=True)

            # 生成下载文件名
            file_name = f"{APP_NAME}.v{version}.exe"
            file_path = os.path.join(download_dir, file_name)

            # 如果文件已存在，先删除
            if os.path.exists(file_path):
                os.remove(file_path)

            # 开始下载
            try:
                response = self.session.get(
                    url,
                    stream=True,
                    timeout=DOWNLOAD_TIMEOUT
                )
                response.raise_for_status()

                # 获取文件总大小
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                # 写入文件
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # 调用进度回调
                            if progress_callback:
                                percentage = (downloaded / total_size * 100) if total_size > 0 else 0
                                progress_callback(downloaded, total_size, percentage)

                # 验证下载的文件
                if not self._verify_file_integrity(file_path):
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise DownloadError("下载的文件完整性验证失败")

                return file_path

            except requests.exceptions.Timeout:
                raise DownloadError("下载超时")
            except requests.exceptions.ConnectionError:
                raise DownloadError("网络连接失败")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    raise DownloadError("下载文件不存在")
                else:
                    raise DownloadError(f"HTTP错误 {e.response.status_code}")
            except requests.exceptions.RequestException as e:
                raise DownloadError(f"下载请求异常: {str(e)}")

        except DownloadError:
            raise
        except Exception as e:
            raise DownloadError(f"下载失败: {str(e)}")

    def download_with_retry(self, url: str, version: str, max_retries: int = 3,
                           progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        带重试机制的文件下载
        :param url: 下载链接
        :param version: 版本号
        :param max_retries: 最大重试次数
        :param progress_callback: 进度回调函数
        :return: 下载的文件路径，失败返回None
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # 重试前等待
                    wait_time = 2 ** attempt  # 指数退避
                    if progress_callback:
                        progress_callback(0, 0, -wait_time)  # 负数表示等待时间
                    time.sleep(wait_time)

                file_path = self.download_file(url, version, progress_callback)
                if file_path:
                    return file_path

            except DownloadError as e:
                last_error = e
                print(f"下载尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
                continue

        # 所有重试都失败了
        if last_error:
            raise DownloadError(f"下载失败，已重试{max_retries}次: {str(last_error)}")
        else:
            raise DownloadError("下载失败，原因未知")

    def cleanup_downloads(self, keep_count: int = 2) -> bool:
        """
        清理下载目录，保留最近的几个文件
        :param keep_count: 保留文件数量
        :return: 是否清理成功
        """
        try:
            download_dir = os.path.join(get_executable_dir(), "downloads")
            if not os.path.exists(download_dir):
                return True

            # 获取所有下载文件
            files = []
            for file_name in os.listdir(download_dir):
                if file_name.startswith(APP_NAME) and file_name.endswith('.exe'):
                    file_path = os.path.join(download_dir, file_name)
                    if os.path.isfile(file_path):
                        files.append((file_path, os.path.getmtime(file_path)))

            # 按修改时间排序，保留最新的文件
            files.sort(key=lambda x: x[1], reverse=True)

            # 删除旧文件
            for file_path, _ in files[keep_count:]:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")

            return True

        except Exception as e:
            print(f"清理下载目录失败: {e}")
            return False

    def get_download_size(self, url: str) -> Optional[int]:
        """
        获取下载文件大小
        :param url: 下载链接
        :return: 文件大小（字节），获取失败返回None
        """
        try:
            response = self.session.head(url, timeout=30)
            response.raise_for_status()
            return int(response.headers.get('content-length', 0))
        except Exception:
            return None

    def test_download_speed(self, url: str) -> float:
        """
        测试下载速度
        :param url: 测试URL
        :return: 下载速度（KB/s）
        """
        try:
            start_time = time.time()

            # 下载一小块数据来测试速度
            response = self.session.get(url, stream=True, timeout=10)
            response.raise_for_status()

            downloaded = 0
            test_size = 1024 * 100  # 100KB

            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    downloaded += len(chunk)
                    if downloaded >= test_size:
                        break

            end_time = time.time()
            duration = end_time - start_time

            if duration > 0:
                speed_kb_per_sec = (downloaded / 1024) / duration
                return speed_kb_per_sec

            return 0.0

        except Exception:
            return 0.0