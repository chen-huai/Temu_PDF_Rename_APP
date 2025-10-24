# GitHub客户端 (github_client.py) 功能详解

## 文件概述

`github_client.py` 负责与GitHub API交互，获取Release信息、下载链接和版本数据。该模块是更新功能的核心数据源，提供了完整的GitHub Releases API封装。

## 核心类：GitHubClient

### 类职责
- GitHub API请求封装
- Release信息获取
- 下载链接解析
- 网络异常处理

### 依赖关系
- 依赖配置模块获取仓库信息
- 使用标准库进行HTTP请求
- 依赖JSON解析API响应

## 主要功能模块

### 1. API请求管理

#### `_make_request(self, url: str, timeout: int = 30) -> dict`
**功能**：发送HTTP GET请求
**参数**：
- `url`: 请求URL
- `timeout`: 超时时间

**实现特点**：
- 自动添加请求头
- 超时控制
- 异常处理
- JSON解析

```python
def _make_request(self, url: str, timeout: int = 30) -> dict:
    """发送HTTP GET请求"""
    try:
        response = requests.get(
            url,
            headers=self.request_headers,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"GitHub API请求失败: {e}")
        return {}
```

### 2. Release信息获取

#### `get_latest_release(self) -> dict`
**功能**：获取最新Release信息
**返回值**：Release信息字典

**返回数据结构**：
```python
{
    "tag_name": "v2.0.0",
    "name": "版本2.0.0发布",
    "body": "更新内容说明...",
    "published_at": "2024-01-01T00:00:00Z",
    "assets": [
        {
            "name": "MyApp-2.0.0.exe",
            "browser_download_url": "https://github.com/...",
            "size": 10240000,
            "content_type": "application/x-msdownload"
        }
    ]
}
```

#### `get_release_by_tag(self, tag: str) -> dict`
**功能**：根据标签获取特定Release信息
**参数**：`tag` - 版本标签

**使用场景**：
- 获取特定版本信息
- 下载指定版本
- 版本回滚操作

### 3. 下载链接管理

#### `get_download_url(self, version: str) -> str`
**功能**：获取指定版本的下载链接
**参数**：`version` - 版本号
**返回值**：下载URL

**选择策略**：
1. 优先选择.exe文件
2. 匹配应用名称的文件
3. 选择第一个可用文件

```python
def get_download_url(self, version: str) -> str:
    """获取指定版本的下载链接"""
    release_info = self.get_release_by_tag(f"v{version}")

    if not release_info:
        return ""

    assets = release_info.get("assets", [])
    for asset in assets:
        name = asset.get("name", "")
        if name.endswith(".exe"):
            return asset.get("browser_download_url", "")

    return ""
```

#### `get_release_notes(self, from_version: str = None) -> str`
**功能**：获取Release更新说明
**参数**：`from_version` - 起始版本（可选）
**返回值**：更新说明文本

### 4. 版本信息解析

#### `parse_version_from_tag(self, tag: str) -> str`
**功能**：从标签解析版本号
**参数**：`tag` - 版本标签
**返回值**：纯版本号

**处理逻辑**：
- 移除'v'前缀
- 去除空白字符
- 验证格式有效性

```python
def parse_version_from_tag(self, tag: str) -> str:
    """从标签解析版本号"""
    if not tag:
        return ""

    # 移除v前缀
    version = tag.lstrip('v').strip()

    # 验证格式
    if re.match(r'^\d+\.\d+(\.\d+)?$', version):
        return version

    return ""
```

## 网络配置

### 请求头设置
```python
request_headers = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "App-Updater/1.0"
}
```

### API端点配置
- `GITHUB_API_BASE`: GitHub API基础URL
- `GITHUB_RELEASES_URL`: Releases API端点
- `GITHUB_LATEST_RELEASE_URL`: 最新Release端点

## 异常处理

### 自定义异常
```python
class NetworkError(Exception):
    """网络连接异常"""
    pass

class GitHubAPIError(Exception):
    """GitHub API错误"""
    pass
```

### 错误处理策略
1. **网络错误**：重试机制
2. **API错误**：返回空数据
3. **解析错误**：记录日志
4. **超时错误**：使用默认值

## 使用示例

### 基本使用
```python
from auto_updater.github_client import GitHubClient

client = GitHubClient()

# 获取最新版本
latest = client.get_latest_release()
version = client.parse_version_from_tag(latest.get("tag_name", ""))

# 获取下载链接
download_url = client.get_download_url(version)

# 获取更新说明
notes = client.get_release_notes()
```

### 错误处理
```python
def get_version_info():
    client = GitHubClient()

    try:
        release = client.get_latest_release()
        if not release:
            logger.warning("无法获取Release信息")
            return None

        return release
    except NetworkError as e:
        logger.error(f"网络错误: {e}")
        return None
    except GitHubAPIError as e:
        logger.error(f"API错误: {e}")
        return None
```

## 性能优化

### 请求缓存
```python
class GitHubClient:
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300  # 5分钟缓存

    def get_latest_release(self) -> dict:
        cache_key = "latest_release"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]["data"]

        data = self._fetch_latest_release()
        self._cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }
        return data
```

### 并发控制
```python
import threading

class GitHubClient:
    def __init__(self):
        self._lock = threading.Lock()

    def get_latest_release(self) -> dict:
        with self._lock:
            return self._fetch_latest_release()
```

## 安全考虑

### 认证处理
```python
def _get_auth_headers(self) -> dict:
    """获取认证请求头"""
    headers = self.request_headers.copy()

    # 如果有GitHub Token，添加认证头
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    return headers
```

### HTTPS验证
```python
def _make_request(self, url: str, timeout: int = 30) -> dict:
    try:
        response = requests.get(
            url,
            headers=self.request_headers,
            timeout=timeout,
            verify=True  # 验证SSL证书
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL验证失败: {e}")
        raise NetworkError(f"SSL验证失败: {e}")
```

## 测试策略

### Mock测试
```python
import unittest
from unittest.mock import patch, MagicMock

class TestGitHubClient(unittest.TestCase):
    @patch('requests.get')
    def test_get_latest_release(self, mock_get):
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tag_name": "v2.0.0",
            "name": "版本2.0.0"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = GitHubClient()
        result = client.get_latest_release()

        self.assertEqual(result["tag_name"], "v2.0.0")
        mock_get.assert_called_once()
```

### 集成测试
```python
def test_real_github_api():
    """真实API测试（仅在CI环境中运行）"""
    if not os.getenv("CI"):
        return

    client = GitHubClient()
    result = client.get_latest_release()

    assert isinstance(result, dict)
    assert "tag_name" in result
    assert "assets" in result
```

## 设计优势

### 1. 模块化设计
- 单一职责原则
- 接口简洁清晰
- 易于测试和维护

### 2. 异常安全
- 完善的错误处理
- 详细的日志记录
- 优雅的降级策略

### 3. 性能优化
- 请求缓存机制
- 合理的超时控制
- 资源及时释放

### 4. 扩展性
- 支持自定义请求头
- 可配置的API端点
- 支持认证机制

## 总结

`github_client.py` 提供了完整的GitHub API封装，为更新模块提供了可靠的数据源。通过合理的异常处理和性能优化，确保了在各种网络环境下都能稳定工作。该模块的设计体现了良好的软件工程实践，为整个更新系统的稳定性奠定了基础。