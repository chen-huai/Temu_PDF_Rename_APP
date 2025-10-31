# -*- coding: utf-8 -*-
"""
PDF重命名工具专用数字签名工具
基于新的 code_signer 模块构建
专门用于PDF_Rename_Operation证书 (TUVSUD颁发)
"""
import os
import sys

# 导入新的签名模块
try:
    from code_signer import CodeSigner
    NEW_MODULE_AVAILABLE = True
except ImportError:
    # 如果新模块不可用，回退到旧模块
    from signing_tool import SigningTool
    NEW_MODULE_AVAILABLE = False

# 项目配置
PROJECT_CERTIFICATE = "pdf_rename_operation"
PROJECT_NAME = "PDF重命名工具"
CONFIG_FILES = [
    "code_signer/examples/project_config.py",  # 新模块配置
    "signature_config.json"                    # 旧模块配置
]

def find_exe_file():
    """查找PDF_Rename_Operation.exe文件"""
    default_paths = [
        "dist/PDF_Rename_Operation.exe",
        "PDF重命名工具_便携版/PDF_Rename_Operation.exe",
        "PDF_Rename_Operation.exe"
    ]

    for path in default_paths:
        if os.path.exists(path):
            return path
    return None

def initialize_signer():
    """初始化签名器，支持新旧模块兼容"""
    if NEW_MODULE_AVAILABLE:
        # 尝试使用新模块配置
        for config_file in CONFIG_FILES:
            if os.path.exists(config_file):
                try:
                    print(f"[信息] 使用配置文件: {config_file}")
                    return CodeSigner.from_config(config_file), config_file
                except Exception as e:
                    print(f"[警告] 配置文件 {config_file} 加载失败: {e}")
                    continue

        # 如果没有配置文件，使用默认配置
        print("[信息] 使用默认配置")
        return CodeSigner(), "默认配置"
    else:
        # 回退到旧模块
        config_file = "signature_config.json"
        if os.path.exists(config_file):
            return SigningTool(config_file), config_file
        else:
            raise FileNotFoundError(f"配置文件不存在: {config_file}")

def display_certificate_info(tool):
    """显示证书详细信息"""
    if NEW_MODULE_AVAILABLE:
        tool.display_certificate_info(PROJECT_CERTIFICATE)
    else:
        tool.display_certificate_info(PROJECT_CERTIFICATE)

def get_certificate_config(tool):
    """获取证书配置"""
    if NEW_MODULE_AVAILABLE:
        return tool.config.get_certificate(PROJECT_CERTIFICATE)
    else:
        return tool.get_certificate_config(PROJECT_CERTIFICATE)

def verify_certificate_exists(tool, cert_config):
    """验证证书是否存在"""
    if NEW_MODULE_AVAILABLE:
        return tool.verify_certificate_exists(cert_config)
    else:
        return tool.verify_certificate_exists(cert_config)

def verify_file_signature(tool, file_path):
    """验证文件签名"""
    if NEW_MODULE_AVAILABLE:
        return tool.verify_signature(file_path)
    else:
        return tool.verify_signature(file_path)

def sign_file_with_cert(tool, file_path, certificate_name):
    """使用指定证书签名文件"""
    if NEW_MODULE_AVAILABLE:
        return tool.sign_file(file_path, certificate_name)
    else:
        return tool.sign_file(file_path, certificate_name)

def main():
    """主函数"""
    print("="*60)
    print(f"{PROJECT_NAME} - 专用数字签名工具")
    print("="*60)

    if NEW_MODULE_AVAILABLE:
        print("[信息] 使用新的 code_signer 模块")
    else:
        print("[信息] 回退到旧的 signing_tool 模块")

    # 初始化签名工具
    try:
        tool, used_config = initialize_signer()
        print(f"[成功] 签名工具初始化成功，使用配置: {used_config}")
    except Exception as e:
        print(f"[错误] 初始化签名工具失败: {e}")
        if NEW_MODULE_AVAILABLE:
            print("请确保 code_signer 模块和配置文件存在且格式正确")
        else:
            print("请确保signature_config.json文件存在且格式正确")
        input("\n按回车退出...")
        return

    # 显示证书信息
    display_certificate_info(tool)

    # 验证配置中的证书是否存在
    cert_config = get_certificate_config(tool)
    if not cert_config:
        print(f"[错误] 未找到证书配置: {PROJECT_CERTIFICATE}")
        input("\n按回车退出...")
        return

    cert_name = cert_config.name if hasattr(cert_config, 'name') else cert_config.get('name', PROJECT_CERTIFICATE)
    cert_sha1 = cert_config.sha1 if hasattr(cert_config, 'sha1') else cert_config.get('sha1', 'N/A')
    cert_subject = cert_config.subject if hasattr(cert_config, 'subject') else cert_config.get('subject', 'N/A')
    cert_issuer = cert_config.issuer if hasattr(cert_config, 'issuer') else cert_config.get('issuer', 'N/A')

    if not verify_certificate_exists(tool, cert_config):
        print(f"[错误] 证书不存在或无法访问: {cert_name}")
        print("\n请确保证书已安装到当前用户的个人证书存储中")
        print("证书信息:")
        print(f"  SHA1: {cert_sha1}")
        print(f"  使用者: {cert_subject}")
        print(f"  颁发者: {cert_issuer}")
        input("\n按回车退出...")
        return

    print(f"[成功] {cert_name}证书验证成功")

    # 查找exe文件
    print("\n[检查] 正在查找PDF_Rename_Operation.exe...")
    exe_file = find_exe_file()

    if not exe_file:
        print("[错误] 未找到PDF_Rename_Operation.exe文件")
        print("请先运行打包工具生成exe文件")
        print("预期路径: dist/PDF_Rename_Operation.exe")
        input("\n按回车退出...")
        return

    print(f"[成功] 找到文件: {exe_file}")

    # 检查是否已签名
    print("\n[检查] 正在检查文件签名状态...")
    verify_success, verify_message = verify_file_signature(tool, exe_file)
    if verify_success:
        print("[警告] 文件已有签名")
        choice = input("是否重新签名? (y/n): ").strip().lower()
        if choice not in ['y', 'yes', '是']:
            print("跳过签名操作")
            input("\n按回车退出...")
            return
    else:
        print("[信息] 文件未签名，将进行签名")

    # 执行签名
    print("\n[签名] 开始签名过程...")
    success, message = sign_file_with_cert(tool, exe_file, PROJECT_CERTIFICATE)

    if success:
        print(f"[成功] {message}")

        # 验证签名
        print("\n[验证] 正在验证签名...")
        verify_success, verify_message = verify_file_signature(tool, exe_file)

        if verify_success:
            print("[成功] 签名验证成功!")
            print("\n[详情] 签名详情:")
            for line in verify_message.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"[警告] 签名验证失败: {verify_message}")

        print(f"\n[完成] 签名完成！")
        print(f"[文件] 签名文件: {exe_file}")
        print(f"[证书] {cert_name}")

    else:
        print(f"[错误] {message}")
        print("\n[建议] 可能的解决方案:")
        print("1. 确保Windows SDK已安装（包含signtool.exe）")
        print("2. 确保证书权限正确")
        print("3. 检查网络连接（时间戳服务器）")
        print("4. 确认文件未被占用")
        if NEW_MODULE_AVAILABLE:
            print("5. 检查 code_signer 配置文件是否正确")
        else:
            print("5. 检查signature_config.json配置是否正确")

    input("\n按回车退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[取消] 用户取消操作")
        input("按回车退出...")
    except Exception as e:
        print(f"\n\n[错误] 发生错误: {e}")
        input("按回车退出...")