# -*- coding: utf-8 -*-
"""
GitHub API客户端模块
负责与GitHub Releases API的交互，获取版本信息和下载链接
"""

import requests
import json
import time
from typing import Optional, Dict, List
from urllib.parse import urljoin

from .config import (
    GITHUB_LATEST_RELEASE_URL,
    GITHUB_RELEASES_URL,
    REQUEST_HEADERS,
    DOWNLOAD_TIMEOUT,
    APP_NAME
)
# 导入错误处理模块
from .error_handler import ErrorHandler, ErrorType

# 异常类将在__init__.py中定义，这里暂时直接定义
class NetworkError(Exception):
    """网络连接异常"""
    pass

class VersionCheckError(Exception):
    """版本检查异常"""
    pass

class GitHubClient:
    """GitHub API客户端"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)

    def _make_request(self, url: str, timeout: int = 30) -> Optional[Dict]:
        """
        发起HTTP请求
        :param url: 请求URL
        :param timeout: 超时时间
        :return: 响应数据字典，失败返回None
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise NetworkError(f"请求超时: {url}")
        except requests.exceptions.ConnectionError:
            raise NetworkError(f"网络连接失败: {url}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise NetworkError("API请求频率限制，请稍后重试")
            elif e.response.status_code == 404:
                raise NetworkError("仓库或Release不存在")
            else:
                raise NetworkError(f"HTTP错误 {e.response.status_code}: {url}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"请求异常: {str(e)}")
        except json.JSONDecodeError as e:
            raise NetworkError(f"响应解析失败: {str(e)}")

    def get_latest_release(self) -> Optional[Dict]:
        """
        获取最新的Release信息
        :return: Release信息字典，失败返回None
        """
        try:
            data = self._make_request(GITHUB_LATEST_RELEASE_URL)
            if data:
                return {
                    'tag_name': data.get('tag_name', ''),
                    'name': data.get('name', ''),
                    'body': data.get('body', ''),
                    'published_at': data.get('published_at', ''),
                    'prerelease': data.get('prerelease', False),
                    'assets': data.get('assets', [])
                }
            return None
        except Exception as e:
            raise VersionCheckError(f"获取最新Release失败: {str(e)}")

    def get_release_info(self, version: str) -> Optional[Dict]:
        """
        获取指定版本的Release信息
        :param version: 版本号（如 "1.0.0" 或 "v1.0.0"）
        :return: Release信息字典，失败返回None
        """
        try:
            # 确保版本号格式正确
            if not version.startswith('v'):
                version = f'v{version}'

            url = f"{GITHUB_RELEASES_URL}/tags/{version}"
            data = self._make_request(url)

            if data:
                return {
                    'tag_name': data.get('tag_name', ''),
                    'name': data.get('name', ''),
                    'body': data.get('body', ''),
                    'published_at': data.get('published_at', ''),
                    'prerelease': data.get('prerelease', False),
                    'assets': data.get('assets', [])
                }
            return None
        except Exception as e:
            raise VersionCheckError(f"获取Release信息失败: {str(e)}")

    def get_all_releases(self) -> List[Dict]:
        """
        获取所有Release列表
        :return: Release信息列表
        """
        try:
            data = self._make_request(GITHUB_RELEASES_URL)
            if data:
                releases = []
                for release in data:
                    releases.append({
                        'tag_name': release.get('tag_name', ''),
                        'name': release.get('name', ''),
                        'body': release.get('body', ''),
                        'published_at': release.get('published_at', ''),
                        'prerelease': release.get('prerelease', False),
                        'assets': release.get('assets', [])
                    })
                return releases
            return []
        except Exception as e:
            raise VersionCheckError(f"获取Release列表失败: {str(e)}")

    def get_download_url(self, version: str) -> Optional[str]:
        """
        获取指定版本的exe文件下载链接
        :param version: 版本号
        :return: 下载链接，失败返回None
        """
        try:
            release_info = self.get_release_info(version)
            if not release_info:
                return None

            # 查找exe文件
            assets = release_info.get('assets', [])
            for asset in assets:
                asset_name = asset.get('name', '')
                if asset_name == APP_NAME or asset_name.endswith('.exe'):
                    return asset.get('browser_download_url')

            return None
        except Exception as e:
            raise VersionCheckError(f"获取下载链接失败: {str(e)}")

    def get_latest_download_url(self) -> Optional[str]:
        """
        获取最新版本的exe文件下载链接
        :return: 下载链接，失败返回None
        """
        try:
            latest_release = self.get_latest_release()
            if not latest_release:
                return None

            version = latest_release.get('tag_name', '').lstrip('v')
            return self.get_download_url(version)
        except Exception as e:
            raise VersionCheckError(f"获取最新下载链接失败: {str(e)}")

    def check_repository_exists(self) -> bool:
        """
        检查仓库是否存在
        :return: 仓库是否存在
        """
        try:
            # 尝试获取仓库信息
            repo_url = GITHUB_LATEST_RELEASE_URL.replace('/releases/latest', '')
            self._make_request(repo_url, timeout=10)
            return True
        except NetworkError:
            return False
        except Exception:
            return False

    def test_connection(self) -> tuple:
        """
        测试GitHub连接
        :return: (是否连接成功, 详细信息)
        """
        try:
            # 测试基本连接
            if not self.check_repository_exists():
                return False, "仓库不存在或无访问权限"

            # 测试API访问
            latest_release = self.get_latest_release()
            if not latest_release:
                return False, "无法访问Release API"

            # 测试下载链接
            version = latest_release.get('tag_name', '').lstrip('v')
            download_url = self.get_download_url(version)
            if not download_url:
                return False, "无法找到可执行文件下载链接"

            return True, f"连接成功，最新版本: {version}"

        except Exception as e:
            return False, f"连接测试失败: {str(e)}"

    def get_release_notes(self, version: str) -> str:
        """
        获取版本发布说明
        :param version: 版本号
        :return: 发布说明文本
        """
        try:
            release_info = self.get_release_info(version)
            if release_info:
                return release_info.get('body', '无发布说明')
            return '无法获取发布说明'
        except Exception as e:
            return f'获取发布说明失败: {str(e)}'

    def is_version_prerelease(self, version: str) -> bool:
        """
        检查版本是否为预发布版本
        :param version: 版本号
        :return: 是否为预发布版本
        """
        try:
            release_info = self.get_release_info(version)
            if release_info:
                return release_info.get('prerelease', False)
            return False
        except Exception:
            return False