# Code Signer - 模块化代码签名工具

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个完全模块化的代码签名工具，支持多种签名工具和灵活的配置方式。设计用于可移植到其他项目，同时支持独立运行和集成使用。

## ✨ 主要特性

- 🔧 **模块化设计** - 易于集成到任何项目
- 🐍 **Python配置** - 类型安全的配置文件，支持复杂逻辑
- 🛠️ **多工具支持** - signtool、PowerShell、osslsigncode
- 🚀 **独立运行** - 可作为命令行工具使用
- 📦 **即插即用** - 简单的API接口
- 🔄 **向后兼容** - 与现有signing_tool.py兼容
- 📝 **详细记录** - 完整的签名历史和日志

## 🚀 快速开始

### 安装

将 `code_signer` 文件夹复制到您的项目中：

```bash
cp -r code_signer /path/to/your/project/
```

### 基本使用

```python
from code_signer import CodeSigner

# 使用默认配置
signer = CodeSigner()

# 签名文件
success, message = signer.sign_file("my_app.exe")
if success:
    print(f"签名成功: {message}")
else:
    print(f"签名失败: {message}")
```

### 使用配置文件

```python
from code_signer import CodeSigner

# 从配置文件创建签名器
signer = CodeSigner.from_config("signing_config.py")

# 签名文件
success, message = signer.sign_file("my_app.exe", "my_certificate")
```

## 📋 配置文件

### 基础配置 (signing_config.py)

```python
from code_signer.config import SigningConfig, CertificateConfig

# 创建配置实例
CONFIG = SigningConfig()

# 启用签名功能
CONFIG.enabled = True
CONFIG.default_certificate = "my_app"
CONFIG.timestamp_server = "http://timestamp.digicert.com"
CONFIG.hash_algorithm = "sha256"

# 添加证书配置
cert = CertificateConfig(
    name="my_app",
    sha1="YOUR_CERTIFICATE_SHA1_HERE",
    subject="CN=My Application",
    description="我的应用程序证书"
)
CONFIG.add_certificate(cert)

# 输出配置
CONFIG.output.verbose = True
CONFIG.output.save_records = True
```

### 高级配置

```python
from code_signer.config import (
    SigningConfig, CertificateConfig, ToolConfig,
    FilePathsConfig, PoliciesConfig, OutputConfig
)

CONFIG = SigningConfig()

# 证书配置
prod_cert = CertificateConfig(
    name="production",
    sha1="PRODUCTION_CERT_SHA1",
    subject="CN=My Production App",
    description="生产环境证书"
)

dev_cert = CertificateConfig(
    name="development",
    sha1="DEV_CERT_SHA1",
    subject="CN=My Development App",
    description="开发环境证书"
)

CONFIG.add_certificate(prod_cert)
CONFIG.add_certificate(dev_cert)

# 工具配置
signtool_config = ToolConfig(
    name="signtool",
    enabled=True,
    path="auto",  # 自动查找或指定路径
    priority=1,
    description="Windows SDK signtool.exe"
)

CONFIG.add_tool(signtool_config)

# 策略配置
CONFIG.policies = PoliciesConfig(
    verify_before_sign=True,
    auto_retry=True,
    max_retries=3,
    record_signing_history=True
)
```

## 🛠️ 命令行使用

### 签名单个文件

```bash
# 基本签名
python -m code_signer.cli sign my_app.exe

# 使用指定配置
python -m code_signer.cli --config my_config.py sign my_app.exe

# 使用指定证书
python -m code_signer.cli --cert my_certificate sign my_app.exe
```

### 批量签名

```bash
# 批量签名目录中的所有exe文件
python -m code_signer.cli batch ./dist/

# 使用指定配置批量签名
python -m code_signer.cli --config my_config.py batch ./dist/
```

### 验证签名

```bash
# 验证文件签名
python -m code_signer.cli verify my_app.exe
```

### 查看证书信息

```bash
# 显示默认证书信息
python -m code_signer.cli cert-info

# 显示指定证书信息
python -m code_signer.cli cert-info --cert my_certificate
```

### 生成配置模板

```bash
# 生成基础配置模板
python -m code_signer.cli init-config

# 生成高级配置模板
python -m code_signer.cli init-config --type advanced --output my_config.py
```

### 查看系统信息

```bash
# 显示系统信息和可用工具
python -m code_signer.cli info
```

## 🔧 API 参考

### CodeSigner 类

```python
class CodeSigner:
    def __init__(self, config: SigningConfig = None)
    def sign_file(self, file_path: str, certificate_name: str = None) -> Tuple[bool, str]
    def verify_signature(self, file_path: str) -> Tuple[bool, str]
    def batch_sign(self, search_dir: str = ".", certificate_name: str = None) -> Dict[str, Tuple[bool, str]]
    def display_certificate_info(self, certificate_name: str = None)
```

### 便捷函数

```python
from code_signer import sign_file, verify_file_signature

# 签名文件
success, message = sign_file("my_app.exe", "config.py", "my_cert")

# 验证签名
success, message = verify_file_signature("my_app.exe")
```

## 📁 项目结构

```
code_signer/
├── __init__.py              # 模块入口
├── core.py                  # 核心签名逻辑
├── config.py                # 配置管理系统
├── utils.py                 # 工具函数
├── cli.py                   # 命令行接口
├── README.md               # 使用文档
├── MIGRATION.md            # 迁移指南
└── examples/               # 配置示例
    ├── __init__.py
    ├── default_config.py   # 基础配置示例
    └── project_config.py   # 项目配置示例
```

## 🔄 从 signing_tool.py 迁移

### 兼容性

新模块完全向后兼容现有的 `signing_tool.py`。您的现有代码无需修改即可使用：

```python
# 现有代码继续工作
from signing_tool import SigningTool

# 新代码可以使用新模块
from code_signer import CodeSigner
```

### 迁移步骤

1. **复制配置**：将 `signature_config.json` 转换为 Python 配置文件
2. **更新导入**：将 `from signing_tool import SigningTool` 改为 `from code_signer import CodeSigner`
3. **配置文件**：将 JSON 配置转换为 Python 配置（见 MIGRATION.md）

详细迁移指南请参考 [MIGRATION.md](MIGRATION.md)

## 🛠️ 支持的签名工具

| 工具 | 优先级 | 描述 | 要求 |
|------|--------|------|------|
| signtool | 1 | Windows SDK signtool.exe | Windows SDK |
| PowerShell | 2 | PowerShell Set-AuthenticodeSignature | Windows PowerShell |
| osslsigncode | 3 | osslsigncode 工具 | osslsigncode 安装 |

## 📝 签名记录

所有签名操作都会自动记录到 `signature_records/` 目录：

```json
{
  "file_path": "my_app.exe",
  "file_hash": "sha256_hash_here",
  "certificate_name": "my_app",
  "certificate_sha1": "cert_sha1_here",
  "signing_time": "2024-01-01 12:00:00",
  "success": true,
  "message": "签名成功",
  "tool": "signtool"
}
```

## 🔍 故障排除

### 常见问题

**Q: 找不到 signtool.exe**
```bash
# 检查可用工具
python -m code_signer.cli tools

# 安装 Windows SDK
# 下载并安装 Windows 10 SDK
```

**Q: 证书不存在或无法访问**
```bash
# 检查证书信息
python -m code_signer.cli cert-info

# 确保证书已安装到当前用户的个人证书存储中
```

**Q: 配置文件加载失败**
```bash
# 验证配置文件
python -c "from code_signer import load_config_from_file; load_config_from_file('config.py')"
```

### 调试模式

启用详细输出进行调试：

```python
CONFIG.output.verbose = True
```

或在命令行中使用：

```bash
python -m code_signer.cli --verbose sign my_app.exe
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🆘 支持

如果您遇到问题或有疑问，请：

1. 查看 [FAQ](#故障排除)
2. 搜索现有的 [Issues](../../issues)
3. 创建新的 Issue 并提供详细信息

---

**Code Signer** - 让代码签名变得简单而强大！ 🚀