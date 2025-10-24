# 配置管理 (config.py) 功能详解

## 文件概述

`auto_updater/config.py` 是更新模块的配置管理核心，负责从外部配置文件读取项目特定信息，并提供统一的配置访问接口。该模块实现了配置驱动设计的核心逻辑。

## 设计目标

- **配置驱动**：所有项目特定信息通过配置文件管理
- **向后兼容**：保持原有全局变量接口
- **默认配置**：配置文件缺失时的安全回退
- **环境适配**：支持开发环境和生产环境

## 核心类：Config

### 类职责
- 加载和解析配置文件
- 提供类型安全的配置访问
- 处理配置异常情况
- 管理默认配置值

### 配置文件依赖
```python
# 配置文件路径
UPDATER_CONFIG_FILE = "updater_config.json"

# 自动检测运行环境
if getattr(sys, 'frozen', False):
    # 生产环境（打包后的exe）
    exec_dir = os.path.dirname(sys.executable)
else:
    # 开发环境
    exec_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

## 配置加载机制

### `_load_config(self) -> dict`
**功能**：加载配置文件
**返回值**：配置字典

**加载策略**：
1. 优先级：配置文件 > 默认配置
2. 异常处理：配置文件损坏时使用默认配置
3. 路径解析：自动适应开发/生产环境

```python
def _load_config(self) -> dict:
    """加载配置文件"""
    try:
        # 自动检测运行环境
        if getattr(sys, 'frozen', False):
            exec_dir = os.path.dirname(sys.executable)
        else:
            exec_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        config_path = os.path.join(exec_dir, UPDATER_CONFIG_FILE)

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._get_default_config()
    except Exception as e:
        print(f"加载配置文件失败: {e}，使用默认配置")
        return self._get_default_config()
```

### `_get_default_config(self) -> dict`
**功能**：获取默认配置
**用途**：配置文件缺失或损坏时的安全回退

**默认配置结构**：
```python
{
    "app": {
        "name": "默认应用",
        "executable": "your_app.exe",
        "version_file": "version.txt"
    },
    "repository": {
        "owner": "your-username",
        "repo": "your-repo",
        "api_base": "https://api.github.com"
    },
    "version": {
        "current": "1.0.0",
        "check_interval_days": 30,
        "auto_check_enabled": True
    },
    "update": {
        "backup_count": 3,
        "download_timeout": 300,
        "max_retries": 3,
        "auto_restart": True
    },
    "network": {
        "request_headers": {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "App-Updater/1.0"
        }
    }
}
```

## 配置属性访问

### 应用配置 (app)

#### `app_name` (属性)
**功能**：获取应用可执行文件名
**配置路径**：`app.executable`
**默认值**：`"your_app.exe"`

```python
@property
def app_name(self) -> str:
    """应用可执行文件名"""
    return self._config.get("app", {}).get("executable", DEFAULT_APP_NAME)
```

#### `version_file` (属性)
**功能**：获取版本文件名
**配置路径**：`app.version_file`
**默认值**：`"version.txt"`

### 仓库配置 (repository)

#### `github_repo` (属性)
**功能**：获取GitHub仓库路径
**配置路径**：`repository.owner` + `repository.repo`
**格式**：`"owner/repo"`

```python
@property
def github_repo(self) -> str:
    """GitHub仓库路径"""
    repo = self._config.get("repository", {})
    return f"{repo.get('owner', 'your-username')}/{repo.get('repo', 'your-repo')}"
```

#### `github_api_base` (属性)
**功能**：获取GitHub API基础URL
**配置路径**：`repository.api_base`
**默认值**：`"https://api.github.com"`

#### `github_releases_url` (属性)
**功能**：获取GitHub Releases API URL
**格式**：`"{api_base}/repos/{repo}/releases"`

#### `github_latest_release_url` (属性)
**功能**：获取GitHub最新Release API URL
**格式**：`"{releases_url}/latest"`

### 版本配置 (version)

#### `update_check_interval_days` (属性)
**功能**：获取更新检查间隔天数
**配置路径**：`version.check_interval_days`
**默认值**：`30`

#### `current_version` (属性)
**功能**：获取当前版本号
**配置路径**：`version.current`
**默认值**：`"1.0.0"`

### 更新配置 (update)

#### `max_backup_count` (属性)
**功能**：获取最大备份数量
**配置路径**：`update.backup_count`
**默认值**：`3`

#### `download_timeout` (属性)
**功能**：获取下载超时时间（秒）
**配置路径**：`update.download_timeout`
**默认值**：`300`

### 网络配置 (network)

#### `request_headers` (属性)
**功能**：获取网络请求头
**配置路径**：`network.request_headers`
**默认值**：标准的GitHub API请求头

## 全局配置实例

### 单例模式实现
```python
_config = None

def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config
```

### 使用示例
```python
from auto_updater.config import get_config

config = get_config()
repo = config.github_repo
version = config.current_version
timeout = config.download_timeout
```

## 向后兼容支持

### 全局变量映射
为了保持向后兼容，模块提供了传统的全局变量接口：

```python
def _get_config_value(attr_name: str, default_value=None):
    """获取配置值的辅助函数"""
    try:
        return getattr(get_config(), attr_name)
    except Exception:
        return default_value

# GitHub配置
GITHUB_REPO = _get_config_value('github_repo', DEFAULT_GITHUB_REPO)
GITHUB_API_BASE = _get_config_value('github_api_base', DEFAULT_GITHUB_API_BASE)

# 更新配置
UPDATE_CHECK_INTERVAL_DAYS = _get_config_value('update_check_interval_days', 30)
MAX_BACKUP_COUNT = _get_config_value('max_backup_count', 3)
DOWNLOAD_TIMEOUT = _get_config_value('download_timeout', 300)

# 文件配置
APP_NAME = _get_config_value('app_name', DEFAULT_APP_NAME)
VERSION_FILE = _get_config_value('version_file', DEFAULT_VERSION_FILE)

# 版本配置
CURRENT_VERSION = _get_config_value('current_version', "1.0.0")
```

## 辅助函数

### `get_executable_dir()`
**功能**：获取可执行文件所在目录
**环境适配**：
- 开发环境：返回 `auto_updater/config.py` 所在目录
- 生产环境：返回exe文件所在目录

```python
def get_executable_dir():
    """获取可执行文件所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
```

### `get_version_file_path()`
**功能**：获取版本文件路径
**返回值**：完整的版本文件路径

### `get_update_config_path()`
**功能**：获取更新配置文件路径
**返回值**：完整的配置文件路径

### `get_backup_dir()`
**功能**：获取备份目录路径
**实现**：自动创建备份目录（如果不存在）

### `get_app_executable_path()`
**功能**：获取应用程序可执行文件路径
**返回值**：完整的可执行文件路径

## 配置文件示例

### 完整配置文件
```json
{
  "app": {
    "name": "我的应用",
    "executable": "MyApp.exe",
    "version_file": "version.txt"
  },
  "repository": {
    "owner": "myusername",
    "repo": "myapp",
    "api_base": "https://api.github.com"
  },
  "version": {
    "current": "2.1.0",
    "check_interval_days": 7,
    "auto_check_enabled": true
  },
  "update": {
    "backup_count": 5,
    "download_timeout": 600,
    "max_retries": 5,
    "auto_restart": true
  },
  "network": {
    "request_headers": {
      "Accept": "application/vnd.github.v3+json",
      "User-Agent": "MyApp-Updater/2.1.0"
    }
  }
}
```

### 最小配置文件
```json
{
  "app": {
    "name": "最小应用",
    "executable": "app.exe"
  },
  "repository": {
    "owner": "user",
    "repo": "repo"
  },
  "version": {
    "current": "1.0.0"
  }
}
```

## 配置验证

### 配置完整性检查
```python
def validate_config(config: dict) -> bool:
    """验证配置文件完整性"""
    required_keys = [
        "app.name",
        "app.executable",
        "repository.owner",
        "repository.repo",
        "version.current"
    ]

    for key in required_keys:
        parts = key.split('.')
        value = config
        for part in parts:
            value = value.get(part, None)
            if value is None:
                logger.error(f"缺少必需的配置项: {key}")
                return False
    return True
```

### 配置值验证
```python
def validate_config_values(config: dict) -> dict:
    """验证配置值的有效性"""
    issues = []

    # 验证版本号格式
    version = config.get("version", {}).get("current", "")
    if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
        issues.append(f"无效的版本号格式: {version}")

    # 验证超时值
    timeout = config.get("update", {}).get("download_timeout", 0)
    if timeout <= 0:
        issues.append(f"无效的超时时间: {timeout}")

    # 验证备份数量
    backup_count = config.get("update", {}).get("backup_count", 0)
    if backup_count < 0:
        issues.append(f"无效的备份数量: {backup_count}")

    return issues
```

## 使用示例

### 基本使用
```python
from auto_updater.config import get_config

config = get_config()

# 获取应用信息
app_name = config.app_name
version = config.current_version

# 获取仓库信息
repo = config.github_repo
api_url = config.github_api_base

# 获取更新配置
interval = config.update_check_interval_days
timeout = config.download_timeout
```

### 传统接口使用
```python
from auto_updater.config import GITHUB_REPO, APP_NAME, CURRENT_VERSION

# 使用传统的全局变量
repo = GITHUB_REPO
app = APP_NAME
version = CURRENT_VERSION
```

### 动态配置更新
```python
def reload_config():
    """重新加载配置文件"""
    global _config
    _config = None  # 重置全局实例
    return get_config()

# 配置文件更新后重新加载
new_config = reload_config()
```

## 设计优势

### 1. 配置驱动
- 项目特定信息外部化
- 支持运行时配置修改
- 便于多环境部署

### 2. 环境自适应
- 自动检测开发/生产环境
- 路径解析智能化
- 部署零配置

### 3. 向后兼容
- 保持原有API接口
- 渐进式升级路径
- 不破坏现有代码

### 4. 异常安全
- 配置文件损坏时的安全回退
- 默认配置保证基本功能
- 详细的错误日志

## 最佳实践

### 1. 配置文件管理
```python
# 确保配置文件存在
def ensure_config_exists():
    config = get_config()
    # Config类会自动处理配置文件不存在的情况
    return True
```

### 2. 配置验证
```python
def validate_and_get_config():
    config = get_config()

    # 基本验证
    if not config.github_repo or config.github_repo == "your-username/your-repo":
        raise ValueError("请配置正确的GitHub仓库信息")

    if not config.app_name or config.app_name == "your_app.exe":
        raise ValueError("请配置正确的应用名称")

    return config
```

### 3. 配置缓存
```python
# 使用单例模式避免重复加载
config = get_config()  # 第一次加载
# 后续调用直接返回缓存的实例
```

## 总结

`config.py` 通过配置驱动的设计，成功实现了更新模块与项目特定信息的解耦。该模块不仅提供了灵活的配置管理功能，还保持了向后兼容性，为更新模块的跨项目复用奠定了坚实的基础。