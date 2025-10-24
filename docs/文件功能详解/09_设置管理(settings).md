# 设置管理 (settings.py) 功能详解

## 文件概述

`settings.py` 提供更新模块的设置管理功能，支持用户偏好设置、更新策略配置等。

## 核心类：SettingsManager

### 主要功能

#### `load_settings(self) -> dict`
**功能**：加载用户设置
**返回值**：设置字典

#### `save_settings(self, settings: dict) -> bool`
**功能**：保存用户设置
**参数**：`settings` - 设置字典
**返回值**：是否保存成功

#### `get_setting(self, key: str, default_value=None)`
**功能**：获取指定设置项
**参数**：
- `key`: 设置键
- `default_value`: 默认值
**返回值**：设置值

#### `set_setting(self, key: str, value)`
**功能**：设置指定项
**参数**：
- `key`: 设置键
- `value`: 设置值

## 默认设置

```python
DEFAULT_SETTINGS = {
    "auto_check_enabled": True,
    "check_interval_days": 30,
    "download_timeout": 300,
    "backup_count": 3,
    "auto_restart": True,
    "show_update_notifications": True
}
```

## 使用示例

```python
settings = SettingsManager()

# 获取设置
auto_check = settings.get_setting("auto_check_enabled", True)

# 设置值
settings.set_setting("check_interval_days", 7)

# 保存设置
settings.save_settings()
```