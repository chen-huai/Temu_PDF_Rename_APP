# -*- coding: utf-8 -*-
"""
PDF重命名工具专用数字签名工具
基于通用签名模块 signing_tool.py 构建
专门用于PDF_Rename_Operation证书 (TUVSUD颁发)
"""
import os
import sys
from signing_tool import SigningTool

# 项目配置
PROJECT_CERTIFICATE = "pdf_rename_operation"
PROJECT_NAME = "PDF重命名工具"

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

def display_certificate_info():
    """显示证书详细信息"""
    tool = SigningTool()
    tool.display_certificate_info(PROJECT_CERTIFICATE)

def main():
    """主函数"""
    print("="*60)
    print(f"{PROJECT_NAME} - 专用数字签名工具")
    print("="*60)

    # 初始化签名工具
    try:
        tool = SigningTool("signature_config.json")
    except Exception as e:
        print(f"[错误] 初始化签名工具失败: {e}")
        print("请确保signature_config.json文件存在且格式正确")
        input("\n按回车退出...")
        return

    # 显示证书信息
    display_certificate_info()

    # 验证配置中的证书是否存在
    cert_config = tool.get_certificate_config(PROJECT_CERTIFICATE)
    if not cert_config:
        print(f"[错误] 未找到证书配置: {PROJECT_CERTIFICATE}")
        input("\n按回车退出...")
        return

    if not tool.verify_certificate_exists(cert_config):
        print(f"[错误] 证书不存在或无法访问: {cert_config.get('name', PROJECT_CERTIFICATE)}")
        print("\n请确保证书已安装到当前用户的个人证书存储中")
        print("证书信息:")
        print(f"  SHA1: {cert_config.get('sha1', 'N/A')}")
        print(f"  使用者: {cert_config.get('subject', 'N/A')}")
        print(f"  颁发者: {cert_config.get('issuer', 'N/A')}")
        input("\n按回车退出...")
        return

    print(f"[成功] {cert_config.get('name', PROJECT_CERTIFICATE)}证书验证成功")

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
    verify_success, verify_message = tool.verify_signature(exe_file)
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
    success, message = tool.sign_file(exe_file, PROJECT_CERTIFICATE)

    if success:
        print(f"[成功] {message}")

        # 验证签名
        print("\n[验证] 正在验证签名...")
        verify_success, verify_message = tool.verify_signature(exe_file)

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
        print(f"[证书] {cert_config.get('name', PROJECT_CERTIFICATE)}")

    else:
        print(f"[错误] {message}")
        print("\n[建议] 可能的解决方案:")
        print("1. 确保Windows SDK已安装（包含signtool.exe）")
        print("2. 确保证书权限正确")
        print("3. 检查网络连接（时间戳服务器）")
        print("4. 确认文件未被占用")
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