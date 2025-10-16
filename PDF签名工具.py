# -*- coding: utf-8 -*-
"""
PDF重命名工具专用数字签名工具
专门用于PDF_Rename_Operation证书 (TUVSUD颁发)
SHA1: 144ac4069565211ab67d25a9d6d33af0e18e511e
"""
import os
import sys
import subprocess
import time
import json
from pathlib import Path

# PDF_Rename_Operation证书信息
CERTIFICATE_SHA1 = "144ac4069565211ab67d25a9d6d33af0e18e511e"
CERTIFICATE_SUBJECT = "CN=PDF_Rename_Operation, OU=PS:Softlines, O=TÜV SÜD Certification and Testing (China) Co. Ltd. Xiamen Branch, L=Xiamen, C=CN"
CERTIFICATE_ISSUER = "CN=TUVSUD-IssuingCA, O=TUVSUD, C=SG"

def find_signtool():
    """查找signtool.exe"""
    try:
        import glob
        search_paths = [
            r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe",
            r"C:\Program Files\Windows Kits\10\bin\*\x64\signtool.exe"
        ]

        for pattern in search_paths:
            matches = glob.glob(pattern)
            if matches:
                return matches[-1]  # 使用最新版本
    except:
        pass
    return None

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

def verify_certificate_exists():
    """验证PDF_Rename_Operation证书是否存在"""
    try:
        cmd = ['certutil', '-user', '-store', 'My', CERTIFICATE_SHA1]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        return result.returncode == 0
    except:
        return False

def sign_exe_file(exe_path):
    """使用PDF_Rename_Operation证书签名exe文件"""
    signtool_path = find_signtool()
    if not signtool_path:
        return False, "[错误] 未找到signtool.exe，请安装Windows SDK"

    # 构建签名命令
    cmd = [
        signtool_path, "sign",
        "/sha1", CERTIFICATE_SHA1,
        "/fd", "sha256",
        "/td", "sha256",
        "/tr", "http://timestamp.digicert.com",
        exe_path
    ]

    try:
        print(f"正在使用PDF_Rename_Operation证书签名...")
        print(f"证书SHA1: {CERTIFICATE_SHA1}")
        print(f"文件: {exe_path}")
        print(f"命令: {' '.join(cmd[:6])} ...")

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            return True, "[成功] 签名成功"
        else:
            return False, f"[错误] 签名失败: {result.stderr}"

    except Exception as e:
        return False, f"[错误] 签名异常: {e}"

def verify_signature(exe_path):
    """验证文件签名"""
    signtool_path = find_signtool()
    if not signtool_path:
        return False, "[错误] 未找到signtool.exe"

    try:
        cmd = [signtool_path, "verify", "/pa", exe_path]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr

    except Exception as e:
        return False, f"[错误] 验证异常: {e}"

def save_signature_record(exe_path, success, message):
    """保存签名记录"""
    record = {
        "file": exe_path,
        "certificate_sha1": CERTIFICATE_SHA1,
        "certificate_subject": CERTIFICATE_SUBJECT,
        "certificate_issuer": CERTIFICATE_ISSUER,
        "signing_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success" if success else "failed",
        "message": message,
        "tool": "PDF签名工具.py"
    }

    try:
        record_file = exe_path.replace(".exe", "_签名记录.json")
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        print(f"[成功] 签名记录已保存到: {record_file}")
    except:
        pass

def display_certificate_info():
    """显示证书详细信息"""
    print("\n" + "="*60)
    print("PDF_Rename_Operation 证书信息")
    print("="*60)
    print(f"证书名称: PDF_Rename_Operation")
    print(f"颁发机构: TUVSUD-IssuingCA")
    print(f"SHA1哈希: {CERTIFICATE_SHA1}")
    print(f"有效期: 2025/10/15 - 2027/10/15")
    print(f"私钥状态: 不可导出")
    print(f"使用者: TUV SUD Certification and Testing (China) Co. Ltd.")
    print("="*60)

def main():
    """主函数"""
    print("="*60)
    print("PDF重命名工具 - 专用数字签名工具")
    print("="*60)

    # 显示证书信息
    display_certificate_info()

    # 1. 验证证书是否存在
    print("\n[检查] 正在验证PDF_Rename_Operation证书...")
    if not verify_certificate_exists():
        print("[错误] 未找到PDF_Rename_Operation证书")
        print("\n请确保证书已安装到当前用户的个人证书存储中")
        print("证书信息:")
        print(f"  SHA1: {CERTIFICATE_SHA1}")
        print(f"  使用者: PDF_Rename_Operation")
        print(f"  颁发者: TUVSUD-IssuingCA")
        input("\n按回车退出...")
        return

    print("[成功] PDF_Rename_Operation证书验证成功")

    # 2. 查找exe文件
    print("\n[检查] 正在查找PDF_Rename_Operation.exe...")
    exe_file = find_exe_file()

    if not exe_file:
        print("[错误] 未找到PDF_Rename_Operation.exe文件")
        print("请先运行打包工具生成exe文件")
        print("预期路径: dist/PDF_Rename_Operation.exe")
        input("\n按回车退出...")
        return

    print(f"[成功] 找到文件: {exe_file}")

    # 3. 检查是否已签名
    print("\n[检查] 正在检查文件签名状态...")
    signtool_path = find_signtool()
    if signtool_path:
        try:
            result = subprocess.run([signtool_path, "verify", "/pa", exe_file],
                                  capture_output=True, text=True, encoding='utf-8')
            if result.returncode == 0:
                print("[警告] 文件已有签名")
                choice = input("是否重新签名? (y/n): ").strip().lower()
                if choice not in ['y', 'yes', '是']:
                    print("跳过签名操作")
                    input("\n按回车退出...")
                    return
        except:
            pass
    else:
        print("[警告] 无法检查签名状态（未找到signtool）")

    # 4. 执行签名
    print("\n[签名] 开始签名过程...")
    success, message = sign_exe_file(exe_file)

    if success:
        print(f"[成功] {message}")

        # 5. 验证签名
        print("\n[验证] 正在验证签名...")
        verify_success, verify_message = verify_signature(exe_file)

        if verify_success:
            print("[成功] 签名验证成功!")
            print("\n[详情] 签名详情:")
            for line in verify_message.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"[警告] 签名验证失败: {verify_message}")

        # 6. 保存签名记录
        save_signature_record(exe_file, True, message)

        print(f"\n[完成] 签名完成！")
        print(f"[文件] 签名文件: {exe_file}")

    else:
        print(f"[错误] {message}")
        print("\n[建议] 可能的解决方案:")
        print("1. 确保Windows SDK已安装（包含signtool.exe）")
        print("2. 确保证书权限正确")
        print("3. 检查网络连接（时间戳服务器）")
        print("4. 确认文件未被占用")

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