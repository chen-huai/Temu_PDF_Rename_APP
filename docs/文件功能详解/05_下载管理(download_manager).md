# 下载管理 (download_manager.py) 功能详解

## 文件概述

`download_manager.py` 负责文件下载功能，支持进度回调、断点续传、重试机制等高级特性，为更新功能提供可靠的文件下载服务。

## 核心类：DownloadManager

### 类职责
- 文件下载管理
- 进度回调支持
- 断点续传功能
- 重试和超时控制
- 下载状态管理

### 主要功能

#### `download_file(self, url: str, version: str, progress_callback=None) -> str`
**功能**：下载文件
**参数**：
- `url`: 下载链接
- `version`: 版本号（用于文件命名）
- `progress_callback`: 进度回调函数

**返回值**：下载文件路径

**实现流程**：
1. 构建下载路径
2. 检查文件是否已存在
3. 执行下载（支持断点续传）
4. 验证文件完整性
5. 返回文件路径

#### `progress_callback_wrapper(self, callback, current, total)`
**功能**：进度回调包装器
**用途**：统一进度回调格式

#### `retry_download(self, url: str, file_path: str, max_retries: int = 3)`
**功能**：重试下载机制
**参数**：
- `url`: 下载链接
- `file_path`: 本地文件路径
- `max_retries`: 最大重试次数

## 使用示例

```python
def progress_callback(downloaded, total, percentage):
    print(f"下载进度: {percentage}%")

manager = DownloadManager()
file_path = manager.download_file(
    "https://github.com/.../app.exe",
    "2.0.0",
    progress_callback
)
```