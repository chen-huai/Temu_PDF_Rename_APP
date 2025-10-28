[根目录](../../CLAUDE.md) > **PDF签名工具**

## 变更记录 (Changelog)

- **2025-10-24 16:16:03** - 创建数字签名工具文档
- **原始版本** - 数字签名功能实现

## 模块职责

PDF签名工具是PDF重命名工具的专用数字签名模块，负责对打包后的可执行文件进行代码签名，使用TUVSUD颁发的数字证书确保软件的安全性和可信度。

## 模块结构

### 核心文件
```
PDF签名工具/
├── PDF签名工具.py        # 主签名脚本
├── 170859-code-signing.cer # TUVSUD数字证书文件
└── 签名使用说明.md       # 签名工具使用文档
```

## 入口与启动

### 主入口脚本
- **PDF签名工具.py**: 数字签名主程序

### 运行方式
```bash
# 直接运行签名工具
python PDF签名工具.py

# 或通过打包工具调用
python 打包工具.py  # 内部会自动调用签名工具
```

## 对外接口

### 主要签名函数
```python
def sign_executable(exe_path: str, cert_path: str = None) -> bool:
    """对可执行文件进行数字签名"""

def verify_signature(exe_path: str) -> bool:
    """验证文件数字签名"""

def find_signtool() -> Optional[str]:
    """查找系统中的signtool.exe"""

def find_exe_file() -> Optional[str]:
    """查找待签名的exe文件"""

def generate_signature_record(signature_info: dict) -> str:
    """生成签名记录文件"""
```

### 证书管理接口
```python
def verify_certificate_exists(cert_sha1: str) -> bool:
    """验证指定证书是否存在"""

def get_certificate_info(cert_sha1: str) -> Optional[dict]:
    """获取证书详细信息"""

def check_certificate_validity(cert_path: str) -> bool:
    """检查证书有效性"""
```

## 关键依赖与配置

### 证书依赖
- **170859-code-signing.cer**: TUVSUD颁发的代码签名证书
  - **SHA1**: 144ac4069565211ab67d25a9d6d33af0e18e511e
  - **Subject**: CN=PDF_Rename_Operation, OU=PS:Softlines, O=TÜV SÜD Certification and Testing (China) Co. Ltd. Xiamen Branch, L=Xiamen, C=CN
  - **Issuer**: CN=TUVSUD-IssuingCA, O=TUVSUD, C=SG

### 系统依赖
- **signtool.exe**: Windows SDK中的代码签名工具
- **PowerShell**: 用于PowerShell签名方式
- **osslsigncode**: 跨平台签名工具（可选）

### 证书查找路径
```python
# Windows SDK路径
"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe"
"C:\Program Files\Windows Kits\10\bin\*\x64\signtool.exe"

# 默认exe文件路径
"dist/PDF_Rename_Operation.exe"
"PDF重命名工具_便携版/PDF_Rename_Operation.exe"
"PDF_Rename_Operation.exe"
```

## 数据模型

### 签名信息模型
```python
{
    "file_path": "dist/PDF_Rename_Operation.exe",
    "certificate_sha1": "144ac4069565211ab67d25a9d6d33af0e18e511e",
    "signing_method": "signtool",  # signtool/powershell/osslsigncode
    "timestamp_server": "http://timestamp.digicert.com",
    "signing_time": "2025-10-24 16:16:03",
    "file_hash": "sha256_hash_value",
    "signature_status": "success",
    "certificate_info": {
        "subject": "CN=PDF_Rename_Operation...",
        "issuer": "CN=TUVSUD-IssuingCA...",
        "valid_from": "2024-01-01",
        "valid_to": "2025-12-31"
    }
}
```

### 签名记录模型
```python
{
    "signing_records": [
        {
            "timestamp": "2025-10-24 16:16:03",
            "file_name": "PDF_Rename_Operation.exe",
            "file_size": 15728640,
            "signing_method": "signtool",
            "certificate_thumbprint": "144ac4069565211ab67d25a9d6d33af0e18e511e",
            "timestamp_server": "http://timestamp.digicert.com",
            "status": "success",
            "error_message": null
        }
    ]
}
```

## 测试与质量

### 签名验证测试
- **证书有效性检查**: 验证证书是否在有效期内
- **签名完整性验证**: 检查签名是否被篡改
- **时间戳验证**: 确认时间戳服务的有效性
- **证书链验证**: 验证证书链的完整性

### 多方式签名测试
- **signtool方式**: 测试Windows SDK签名工具
- **PowerShell方式**: 测试PowerShell Set-AuthenticodeSignature
- **osslsigncode方式**: 测试跨平台签名工具

### 错误处理测试
- **证书不存在**: 测试证书缺失情况
- **证书过期**: 测试过期证书处理
- **权限不足**: 测试无签名权限情况
- **网络问题**: 测试时间戳服务不可用

## 常见问题 (FAQ)

### Q: 签名失败提示"证书不存在"怎么办？
A: 确认170859-code-signing.cer文件存在，并已正确安装到系统证书存储中。

### Q: 找不到signtool.exe怎么办？
A: 安装Windows 10 SDK，或使用PowerShell/osslsigncode替代方式。

### Q: 时间戳服务连接失败怎么办？
A: 检查网络连接，或尝试其他时间戳服务器如http://timestamp.comodoca.com。

### Q: 如何验证签名是否成功？
A: 右键点击exe文件 -> 属性 -> 数字签名，查看签名详情。

### Q: 签名后文件变大是否正常？
A: 是的，数字签名会增加文件大小，通常增加几KB到几十KB。

## 相关文件清单

### 核心文件
- **PDF签名工具.py**: 主签名脚本
- **170859-code-signing.cer**: TUVSUD数字证书

### 配置和记录文件
- **PDF_Rename_Operation_签名记录.json**: 签名操作记录
- **签名使用说明.md**: 详细使用说明

### 签名目标文件
- **dist/PDF_Rename_Operation.exe**: 打包后的主程序
- **PDF重命名工具_便携版/PDF_Rename_Operation.exe**: 便携版程序

### 相关文档
- **打包使用说明.txt**: 打包工具使用说明
- **版本更新清单.md**: 版本发布记录

## 架构设计模式

### 签名策略模式
支持多种签名方式的自动选择：
1. **signtool**: 优先使用Windows SDK工具
2. **PowerShell**: 备用PowerShell方式
3. **osslsigncode**: 跨平台备用方案

### 错误处理策略
- **优雅降级**: 一种方式失败自动尝试其他方式
- **详细日志**: 记录每个步骤的详细信息
- **用户友好**: 提供清晰的错误信息和解决建议

### 安全考虑
- **证书保护**: 签名证书安全存储和使用
- **完整性校验**: 签名前后文件哈希校验
- **时间戳服务**: 确保签名的长期有效性

## 使用示例

### 基本签名
```python
from PDF签名工具 import sign_executable

# 使用默认证书签名
success = sign_executable("dist/PDF_Rename_Operation.exe")
if success:
    print("签名成功")
else:
    print("签名失败")
```

### 指定证书签名
```python
# 使用指定证书签名
success = sign_executable(
    exe_path="dist/PDF_Rename_Operation.exe",
    cert_path="path/to/certificate.cer"
)
```

### 验证签名
```python
from PDF签名工具 import verify_signature

# 验证文件签名
is_valid = verify_signature("dist/PDF_Rename_Operation.exe")
print(f"签名有效: {is_valid}")
```

### 批量签名
```python
import os
from PDF签名工具 import sign_executable

# 批量签名目录中的所有exe文件
exe_files = [f for f in os.listdir("dist") if f.endswith(".exe")]
for exe_file in exe_files:
    path = os.path.join("dist", exe_file)
    if sign_executable(path):
        print(f"{exe_file} 签名成功")
    else:
        print(f"{exe_file} 签名失败")
```

## 签名流程详解

### 准备阶段
1. **查找证书**: 确认TUVSUD证书可用
2. **查找签名工具**: 检测signtool、PowerShell等工具
3. **验证目标文件**: 确认exe文件存在且可访问

### 签名执行
1. **计算文件哈希**: 记录签名前文件完整性
2. **执行签名操作**: 使用选定方式进行签名
3. **添加时间戳**: 连接时间戳服务器添加时间戳
4. **验证签名结果**: 检查签名是否成功

### 记录生成
1. **生成签名记录**: 保存签名操作的详细信息
2. **更新JSON记录**: 写入签名历史记录文件
3. **输出用户反馈**: 显示签名结果和相关信息

## 错误处理机制

### 证书相关错误
- **证书不存在**: 检查证书文件和系统存储
- **证书过期**: 提示更新证书
- **证书权限不足**: 检查证书私钥访问权限

### 工具相关错误
- **signtool未找到**: 提供安装Windows SDK指引
- **PowerShell权限**: 提示以管理员身份运行
- **osslsigncode缺失**: 提供安装指引

### 网络相关错误
- **时间戳服务不可用**: 尝试备用时间戳服务器
- **网络连接超时**: 建议检查网络连接
- **DNS解析失败**: 建议检查DNS设置

## 性能优化

### 签名速度优化
- **工具选择优化**: 自动选择最快的可用签名工具
- **并行处理**: 支持多文件并行签名
- **缓存机制**: 缓存证书和工具查找结果

### 资源管理
- **内存优化**: 大文件分块处理
- **临时文件清理**: 自动清理签名过程中的临时文件
- **连接复用**: 复用时间戳服务器连接

## 变更记录 (Changelog)

- **2025-10-24 16:16:03** - 创建数字签名工具文档
- **原始版本** - 数字签名功能实现