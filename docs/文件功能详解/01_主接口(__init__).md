# 主接口文件 (__init__.py) 功能详解

## 文件概述

`auto_updater/__init__.py` 是更新模块的主入口文件，提供统一的自动更新接口。该文件采用门面模式（Facade Pattern），将复杂的更新流程封装为简单易用的API。

## 核心类：AutoUpdater

### 类职责
- 统一更新功能接口
- 协调各子模块工作
- 提供完整的更新流程管理
- 处理更新过程中的异常情况

### 依赖关系
```
AutoUpdater
├── VersionManager (版本管理)
├── GitHubClient (GitHub交互)
├── DownloadManager (文件下载)
├── BackupManager (备份管理)
└── UpdateExecutor (更新执行)
```

## 主要方法详解

### `__init__(self, parent=None)`
**功能**：初始化自动更新器
**参数**：
- `parent`: 父对象，通常用于GUI信号连接

**实现逻辑**：
```python
def __init__(self, parent=None):
    self.version_manager = VersionManager()
    self.github_client = GitHubClient()
    self.download_manager = DownloadManager()
    self.backup_manager = BackupManager()
    self.update_executor = UpdateExecutor()
    self.parent = parent
```

### `check_for_updates(self, force_check=False) -> tuple`
**功能**：检查是否有可用更新
**参数**：
- `force_check`: 是否强制检查（忽略时间间隔）

**返回值**：`(是否有更新, 远程版本, 本地版本, 错误信息)`

**实现流程**：
1. 检查是否应该进行更新检查
2. 调用GitHubClient获取远程版本信息
3. 使用VersionManager进行版本比较
4. 更新最后检查时间
5. 返回检查结果

**关键逻辑**：
```python
# 检查时间间隔
if not force_check and not self.version_manager.should_check_for_updates():
    return False, None, local_version, "距离上次检查时间过短"

# 获取远程版本
release_info = self.github_client.get_latest_release()
remote_version = release_info.get('tag_name', '').lstrip('v')

# 版本比较
has_update, local_version = self.version_manager.is_update_available(remote_version)
```

### `download_update(self, version: str, progress_callback=None) -> tuple`
**功能**：下载指定版本的更新文件
**参数**：
- `version`: 要下载的版本号
- `progress_callback`: 进度回调函数

**返回值**：`(是否成功, 下载文件路径, 错误信息)`

**实现流程**：
1. 获取下载链接
2. 创建备份
3. 下载文件
4. 返回下载结果

**关键逻辑**：
```python
# 获取下载链接
download_url = self.github_client.get_download_url(version)

# 创建备份
backup_path = self.backup_manager.create_backup()

# 下载文件
downloaded_file = self.download_manager.download_file(
    download_url, version, progress_callback
)
```

### `execute_update(self, update_file_path: str) -> tuple`
**功能**：执行更新操作
**参数**：
- `update_file_path`: 更新文件路径

**返回值**：`(是否成功, 错误信息)`

**实现流程**：
1. 验证更新文件
2. 调用UpdateExecutor执行更新
3. 返回执行结果

### `rollback_update(self) -> tuple`
**功能**：回滚到上一个版本
**返回值**：`(是否成功, 错误信息)`

**实现流程**：
1. 调用BackupManager恢复备份
2. 返回回滚结果

## 异常类定义

### `UpdateError` (基础异常)
**用途**：更新功能的基础异常类

### `NetworkError` (网络异常)
**用途**：网络连接相关的错误

### `VersionCheckError` (版本检查异常)
**用途**：版本检查过程中的错误

### `DownloadError` (下载异常)
**用途**：文件下载过程中的错误

### `BackupError` (备份异常)
**用途**：备份操作过程中的错误

### `UpdateExecutionError` (更新执行异常)
**用途**：更新执行过程中的错误

## 使用示例

### 基本使用
```python
from auto_updater import AutoUpdater

# 创建更新器实例
updater = AutoUpdater(parent=self)

# 检查更新
has_update, remote_version, local_version, error = updater.check_for_updates()

if has_update:
    # 下载更新
    success, download_path, error = updater.download_update(remote_version)

    if success:
        # 执行更新
        success, error = updater.execute_update(download_path)
        if success:
            print("更新成功！")
        else:
            print(f"更新失败: {error}")
```

### 带进度回调的使用
```python
def progress_callback(downloaded, total, percentage):
    print(f"下载进度: {percentage}%")

updater = AutoUpdater()
success, download_path, error = updater.download_update("1.1.0", progress_callback)
```

## 设计特点

### 1. 门面模式
- 隐藏内部复杂性
- 提供统一接口
- 简化客户端使用

### 2. 异步支持
- 支持进度回调
- 不阻塞主线程
- 实时状态反馈

### 3. 错误处理
- 分类异常处理
- 详细错误信息
- 友好的用户提示

### 4. 配置驱动
- 从配置文件读取参数
- 支持运行时配置
- 高度可定制

## 最佳实践

### 1. 初始化配置
```python
# 推荐在应用启动时初始化
try:
    self.auto_updater = AutoUpdater(self)
    logger.info("自动更新器初始化成功")
except Exception as e:
    logger.error(f"自动更新器初始化失败: {e}")
    self.auto_updater = None
```

### 2. 错误处理
```python
def check_updates(self):
    if not self.auto_updater:
        QMessageBox.warning(self, "更新功能不可用", "自动更新功能未正确初始化")
        return

    try:
        has_update, remote_version, local_version, error = self.auto_updater.check_for_updates()
        # 处理结果...
    except Exception as e:
        logger.error(f"检查更新异常: {e}")
        QMessageBox.critical(self, "错误", f"检查更新时发生异常：{str(e)}")
```

### 3. 进度显示
```python
def on_progress_update(self, downloaded, total, percentage):
    # 更新进度条
    self.progress_bar.setValue(percentage)

    # 更新状态文本
    self.status_label.setText(f"下载中... {percentage}%")
```

## 总结

`__init__.py` 文件作为更新模块的主接口，成功地将复杂的更新流程封装为简单易用的API。通过门面模式的设计，客户端代码只需要与AutoUpdater类交互，无需了解内部复杂的模块结构和实现细节。这种设计大大提高了模块的可用性和可维护性。