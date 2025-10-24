# 备份管理 (backup_manager.py) 功能详解

## 文件概述

`backup_manager.py` 负责更新前的备份管理和回滚功能，确保更新失败时可以安全恢复到原始状态。

## 核心类：BackupManager

### 主要功能

#### `create_backup(self) -> str`
**功能**：创建应用备份
**返回值**：备份文件路径

**实现逻辑**：
1. 检查当前可执行文件
2. 创建备份目录
3. 复制文件到备份位置
4. 按时间戳命名备份

#### `restore_from_backup(self, backup_path: str = None) -> bool`
**功能**：从备份恢复应用
**参数**：`backup_path` - 备份文件路径（可选，默认使用最新备份）
**返回值**：是否恢复成功

#### `cleanup_old_backups(self, keep_count: int = 3)`
**功能**：清理旧备份文件
**参数**：`keep_count` - 保留备份数量

#### `get_latest_backup(self) -> str`
**功能**：获取最新备份路径
**返回值**：最新备份文件路径

## 使用示例

```python
# 创建备份
backup_path = backup_manager.create_backup()

# 恢复备份
success = backup_manager.restore_from_backup()

# 清理旧备份
backup_manager.cleanup_old_backups(keep_count=3)
```