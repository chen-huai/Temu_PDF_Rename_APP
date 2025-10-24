# 错误处理 (error_handler.py) 功能详解

## 文件概述

`error_handler.py` 提供统一的错误处理和日志记录功能，为更新模块提供完善的异常管理机制。

## 核心类：ErrorHandler

### 主要功能

#### `handle_update_error(self, error: Exception, context: str = "") -> dict`
**功能**：处理更新相关错误
**参数**：
- `error`: 异常对象
- `context`: 错误上下文信息
**返回值**：错误信息字典

#### `log_error(self, error: Exception, context: str = "")`
**功能**：记录错误日志
**参数**：
- `error`: 异常对象
- `context`: 错误上下文

#### `get_user_friendly_message(self, error: Exception) -> str`
**功能**：获取用户友好的错误信息
**参数**：`error` - 异常对象
**返回值**：用户友好的错误描述

## 错误分类

### 网络错误
- 连接超时
- DNS解析失败
- SSL证书问题

### 文件错误
- 权限不足
- 磁盘空间不足
- 文件被占用

### 配置错误
- 配置文件格式错误
- 必需配置项缺失
- 配置值无效

## 使用示例

```python
error_handler = ErrorHandler()

try:
    # 更新操作
    pass
except Exception as e:
    error_info = error_handler.handle_update_error(e, "下载阶段")
    user_message = error_handler.get_user_friendly_message(e)
    QMessageBox.critical(self, "错误", user_message)
```