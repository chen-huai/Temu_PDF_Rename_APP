# 版本管理 (version_manager.py) 功能详解

## 文件概述

`version_manager.py` 负责统一的版本控制管理，采用配置驱动的设计，从外部配置文件读取版本信息，提供版本比较、验证和同步等功能。

## 核心类：VersionManager

### 设计理念
- **配置驱动**：版本号从配置文件读取，而非硬编码
- **统一管理**：所有版本相关信息集中管理
- **向后兼容**：支持传统的版本文件机制

### 配置依赖
```python
# 从配置文件读取版本信息
self.config_file = "updater_config.json"
self._config = self._load_config()
```

## 核心属性和方法

### 配置文件管理

#### `_load_config(self) -> dict`
**功能**：加载配置文件
**返回值**：配置字典

**实现逻辑**：
1. 尝试读取 `updater_config.json`
2. 如果文件不存在，返回默认配置
3. 异常处理，确保程序正常运行

```python
def _load_config(self) -> dict:
    try:
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._get_default_config()
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return self._get_default_config()
```

#### `_get_default_config(self) -> dict`
**功能**：获取默认配置
**用途**：配置文件缺失时的回退方案

### 版本号管理

#### `CURRENT_VERSION` (属性)
**功能**：获取当前版本号（从配置文件读取）
**实现**：使用 `@property` 装饰器

```python
@property
def CURRENT_VERSION(self) -> str:
    """当前版本号（从配置文件读取）"""
    try:
        return self._config.get("version", {}).get("current", "1.0.0")
    except Exception:
        return "1.0.0"
```

#### `get_version(self) -> str`
**功能**：获取当前版本号
**返回值**：版本字符串

**使用示例**：
```python
vm = VersionManager()
current_version = vm.get_version()  # 返回: "2.0.0"
```

#### `get_version_display_text(self) -> str`
**功能**：获取UI显示的版本文本
**返回值**：格式化的版本文本

**示例**：
```python
display_text = vm.get_version_display_text()  # 返回: "Version v2.0.0"
```

#### `get_about_dialog_title(self) -> str`
**功能**：获取关于对话框标题
**返回值**：包含版本的标题

**示例**：
```python
title = vm.get_about_dialog_title()  # 返回: "关于 PDF重命名工具 v2.0.0"
```

### 版本验证与比较

#### `_is_valid_version_format(self, version: str) -> bool`
**功能**：验证版本号格式
**参数**：版本字符串
**返回值**：是否有效

**验证规则**：
- 版本号格式：`主版本.次版本.修订版本`
- 每部分必须是数字
- 至少包含主版本和次版本

```python
def _is_valid_version_format(self, version: str) -> bool:
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
```

**测试用例**：
```python
assert vm._is_valid_version_format("1.0.0") == True
assert vm._is_valid_version_format("2.1") == True
assert vm._is_valid_version_format("1.0.0-beta") == False
assert vm._is_valid_version_format("v1.0") == False
```

### 版本文件同步

#### `_ensure_version_file_exists(self)`
**功能**：确保版本文件存在且内容正确
**用途**：向后兼容传统版本文件机制

**实现逻辑**：
1. 检查版本文件是否存在
2. 如果不存在，创建文件
3. 如果存在，验证内容是否与配置一致
4. 不一致时自动同步

#### `_read_version_from_file(self) -> str`
**功能**：从版本文件读取版本号
**返回值**：文件中的版本号

#### `_save_version_to_file(self)`
**功能**：保存版本号到文件
**用途**：同步版本文件内容

### 版本更新功能

#### `update_app_version(self, new_version: str)`
**功能**：更新应用版本号
**参数**：新版本号
**异常**：版本格式无效时抛出异常

**实现流程**：
1. 验证新版本格式
2. 调用源代码更新方法
3. 记录更新日志

```python
def update_app_version(self, new_version: str):
    try:
        if not self._is_valid_version_format(new_version):
            raise ValueError(f"无效的版本号格式: {new_version}")

        old_version = self.CURRENT_VERSION
        self._update_source_version_file(new_version)
        logger.info(f"版本已更新: {old_version} → {new_version}")
    except Exception as e:
        logger.error(f"更新版本失败: {e}")
        raise
```

#### `_update_source_version_file(self, new_version: str)`
**功能**：更新源代码文件中的版本常量
**目标文件**：
- 当前版本管理器文件
- 主程序文件

**实现**：使用文本替换方式更新版本常量

#### `_update_version_in_file(self, file_path: str, pattern: str, new_version: str)`
**功能**：在文件中更新版本号
**实现**：逐行扫描，匹配模式，替换内容

### 版本信息查询

#### `get_all_version_info(self) -> dict`
**功能**：获取所有版本相关信息
**返回值**：版本信息字典

**返回内容**：
```python
{
    'version': '2.0.0',
    'display_text': 'Version v2.0.0',
    'about_title': '关于 PDF重命名工具 v2.0.0',
    'version_file': 'version.txt',
    'file_exists': True,
    'file_version': '2.0.0'
}
```

#### `sync_all_versions(self)`
**功能**：同步所有版本信息
**实现**：
1. 同步版本文件
2. 更新配置文件
3. 记录同步日志

## 全局实例和便捷函数

### 全局版本管理器实例
```python
_version_manager = None

def get_version_manager() -> VersionManager:
    """获取全局版本管理器实例"""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager
```

### 便捷函数
```python
def get_version() -> str:
    """获取当前版本号"""
    return get_version_manager().get_version()

def get_version_display_text() -> str:
    """获取版本显示文本"""
    return get_version_manager().get_version_display_text()

def update_app_version(new_version: str):
    """更新应用版本"""
    get_version_manager().update_app_version(new_version)
```

## 配置文件结构

### 版本配置部分
```json
{
  "version": {
    "current": "2.0.0",
    "check_interval_days": 30,
    "auto_check_enabled": true
  }
}
```

### 配置项说明
- `current`: 当前版本号
- `check_interval_days`: 自动检查间隔天数
- `auto_check_enabled`: 是否启用自动检查

## 使用示例

### 基本使用
```python
from version_manager import get_version_manager, get_version

# 获取版本信息
vm = get_version_manager()
version = vm.get_version()
display_text = vm.get_version_display_text()

print(f"当前版本: {version}")
print(f"显示文本: {display_text}")
```

### 版本比较
```python
def is_newer(remote_version: str, local_version: str) -> bool:
    """简单的版本比较函数"""
    remote_parts = list(map(int, remote_version.split('.')))
    local_parts = list(map(int, local_version.split('.')))

    # 补齐版本号长度
    max_len = max(len(remote_parts), len(local_parts))
    remote_parts.extend([0] * (max_len - len(remote_parts)))
    local_parts.extend([0] * (max_len - len(local_parts)))

    return remote_parts > local_parts

# 使用示例
if is_newer("2.1.0", "2.0.0"):
    print("有新版本可用")
```

### 版本更新
```python
from version_manager import update_app_version

try:
    update_app_version("2.1.0")
    print("版本更新成功")
except ValueError as e:
    print(f"版本格式错误: {e}")
except Exception as e:
    print(f"更新失败: {e}")
```

## 设计优势

### 1. 配置驱动
- 版本号外部化，易于管理
- 支持运行时配置修改
- 便于多环境配置

### 2. 向后兼容
- 支持传统版本文件
- 平滑升级路径
- 不破坏现有功能

### 3. 单例模式
- 全局统一版本管理
- 避免重复实例化
- 确保数据一致性

### 4. 异常处理
- 完善的错误处理机制
- 详细的日志记录
- 友好的错误提示

## 最佳实践

### 1. 版本号命名
```python
# 推荐的版本号格式
VERSION_FORMATS = {
    "MAJOR.MINOR.PATCH": "1.0.0",      # 语义化版本
    "MAJOR.MINOR": "1.0",            # 简化版本
    "MAJOR.MINOR.PATCH.BUILD": "1.0.0.100"  # 包含构建号
}
```

### 2. 配置文件管理
```python
# 确保配置文件可读
try:
    vm = VersionManager()
    version = vm.get_version()
except Exception as e:
    logger.error(f"版本管理器初始化失败: {e}")
    version = "1.0.0"  # 使用默认版本
```

### 3. 版本更新策略
```python
def update_version_safely(new_version: str):
    """安全更新版本号"""
    vm = get_version_manager()

    # 验证格式
    if not vm._is_valid_version_format(new_version):
        raise ValueError(f"无效版本号: {new_version}")

    # 备份当前版本
    current_version = vm.get_version()

    try:
        # 更新版本
        vm.update_app_version(new_version)
        logger.info(f"版本更新成功: {current_version} → {new_version}")
    except Exception as e:
        logger.error(f"版本更新失败: {e}")
        # 回滚到原版本
        vm.update_app_version(current_version)
        raise
```

## 总结

`version_manager.py` 通过配置驱动的设计，实现了灵活、可维护的版本管理功能。该模块不仅支持传统的版本文件机制，还提供了现代化的配置文件驱动方案，为不同类型的项目提供了适配的版本管理解决方案。