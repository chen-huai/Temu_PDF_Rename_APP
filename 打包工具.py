# -*- coding: utf-8 -*-
"""
PDF重命名工具打包脚本
双击运行即可打包成exe文件，支持代码签名
集成新的 code_signer 模块进行签名
"""
import os
import sys
import subprocess
import shutil
import json
import time
from pathlib import Path

# 导入编码安全工具
try:
    from code_signer.utils import safe_subprocess_run
    SAFE_SUBPROCESS_AVAILABLE = True
except ImportError:
    SAFE_SUBPROCESS_AVAILABLE = False
    print("[信息] 安全subprocess工具不可用，将使用传统方式")

# 导入新的签名模块
try:
    from code_signer import CodeSigner
    NEW_SIGNER_AVAILABLE = True
except ImportError:
    NEW_SIGNER_AVAILABLE = False
    print("[信息] 新的签名模块不可用，将使用传统签名方式")

def install_missing_packages():
    """安装缺少的包"""
    missing_packages = []

    # 检查PIL/Pillow
    try:
        subprocess.run([sys.executable, "-c", "import PIL"],
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        missing_packages.append("Pillow")

    # 检查PyQt5
    try:
        subprocess.run([sys.executable, "-c", "import PyQt5"],
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        missing_packages.append("PyQt5")

    # 检查PyPDF2
    try:
        subprocess.run([sys.executable, "-c", "import PyPDF2"],
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        missing_packages.append("PyPDF2")

    # 检查pandas
    try:
        subprocess.run([sys.executable, "-c", "import pandas"],
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        missing_packages.append("pandas")

    # 安装缺少的包
    if missing_packages:
        print(f"正在安装缺少的包: {', '.join(missing_packages)}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages,
                          check=True)
            print("包安装成功")
            return True
        except subprocess.CalledProcessError:
            print("包安装失败")
            return False
    else:
        print("所有必要包都已安装")
        return True

def check_files():
    """检查必要文件"""
    required_files = [
        "PDF_Rename_Operation.py",
        "PDF_Rename_Operation_Logo.ico"
    ]

    for file in required_files:
        if not os.path.exists(file):
            print(f"错误: 找不到文件 {file}")
            return False
    print("文件检查通过")
    return True

def clean_old_files():
    """清理旧的打包文件"""
    dirs_to_remove = ['build', 'dist', 'PDF重命名工具_便携版']
    files_to_remove = ['*.spec']

    for item in dirs_to_remove + files_to_remove:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                for f in Path('.').glob(item):
                    f.unlink()

def build_exe():
    """打包exe文件"""
    print("开始打包...")

    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=PDF_Rename_Operation",
        "--onefile",
        "--windowed",
        "--icon=PDF_Rename_Operation_Logo.ico",
        "--clean",
        "--noconfirm"
    ]

  
    # 添加主程序文件
    cmd.append("PDF_Rename_Operation.py")

    try:
        print("正在执行打包命令...")
        if SAFE_SUBPROCESS_AVAILABLE:
            result = safe_subprocess_run(cmd, encoding='utf-8')
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            exe_path = "dist/PDF_Rename_Operation.exe"
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"打包成功! 文件大小: {size_mb:.1f}MB")
                return True
            else:
                print("打包完成但找不到exe文件")
                return False
        else:
            print("打包失败!")
            if result.stderr:
                print("错误信息:")
                print(result.stderr)
            return False
    except Exception as e:
        print(f"打包过程中出错: {e}")
        return False

def find_signtool():
    """查找系统中可用的signtool.exe"""
    possible_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22000.0\x64\signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.20348.0\x64\signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\8.1\bin\x64\signtool.exe",
        r"C:\Program Files\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
        r"C:\Program Files\Windows Kits\10\bin\10.0.22000.0\x64\signtool.exe",
        r"C:\Program Files\Windows Kits\10\bin\10.0.20348.0\x64\signtool.exe",
    ]

    # 搜索所有可能的Windows Kits版本
    try:
        import glob
        search_paths = [
            r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe",
            r"C:\Program Files\Windows Kits\10\bin\*\x64\signtool.exe"
        ]

        for pattern in search_paths:
            matches = glob.glob(pattern)
            if matches:
                possible_paths.extend(matches)
    except:
        pass

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None

def install_signtool_alternative():
    """安装替代的签名工具（使用PowerShell脚本）"""
    powershell_script = """
# PowerShell代码签名脚本
param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,

    [Parameter(Mandatory=$true)]
    [string]$CertificatePath,

    [Parameter(Mandatory=$false)]
    [string]$TimestampServer = "http://timestamp.digicert.com"
)

try {
    # 加载证书
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CertificatePath)

    # 获取文件内容
    $fileContent = Get-Content -Path $FilePath -Raw -Encoding Byte

    # 创建签名器
    $signer = New-Object System.Security.Cryptography.Pkcs.SignedCms
    $contentInfo = New-Object System.Security.Cryptography.Pkcs.ContentInfo $fileContent
    $signer.Content = $contentInfo

    # 创建签名者信息
    $signerInfo = New-Object System.Security.Cryptography.Pkcs.SignerInfo
    $signerInfo.Certificate = $cert

    # 添加签名
    $signer.ComputeSignature($signerInfo)

    # 保存签名后的文件
    $signedContent = $signer.Encode()
    [System.IO.File]::WriteAllBytes($FilePath, $signedContent)

    Write-Host "文件签名成功: $FilePath"
    return $true
}
catch {
    Write-Host "签名失败: $($_.Exception.Message)"
    return $false
}
"""

    script_path = "sign_file.ps1"
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(powershell_script)
        return script_path
    except Exception as e:
        print(f"创建PowerShell签名脚本失败: {e}")
        return None

def sign_exe_file(exe_path, certificate_path="170859-code-signing.cer"):
    """对EXE文件进行代码签名"""
    print("开始代码签名...")

    # 检查证书文件
    if not os.path.exists(certificate_path):
        print(f"错误: 找不到证书文件 {certificate_path}")
        return False, "证书文件不存在"

    # 检查EXE文件
    if not os.path.exists(exe_path):
        print(f"错误: 找不到EXE文件 {exe_path}")
        return False, "EXE文件不存在"

    # 方法1: 尝试使用signtool
    signtool_path = find_signtool()
    if signtool_path:
        print(f"找到signtool: {signtool_path}")
        try:
            cmd = [
                signtool_path, "sign",
                "/f", certificate_path,
                "/fd", "SHA256",  # 添加摘要算法参数
                "/t", "http://timestamp.digicert.com",
                "/sha1", "170859",  # 假设证书指纹
                exe_path
            ]

            print("正在使用signtool签名...")
            if SAFE_SUBPROCESS_AVAILABLE:
                result = safe_subprocess_run(cmd, encoding='utf-8')
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

            if result.returncode == 0:
                print("[OK] signtool签名成功!")
                return True, "signtool签名成功"
            else:
                print(f"signtool签名失败: {result.stderr}")

        except Exception as e:
            print(f"signtool签名异常: {e}")
    else:
        print("未找到signtool，尝试其他方法...")

    # 方法2: 尝试使用PowerShell和.NET
    try:
        print("尝试使用PowerShell脚本签名...")
        script_path = install_signtool_alternative()
        if script_path:
            cmd = [
                "powershell", "-ExecutionPolicy", "Bypass", "-File", script_path,
                "-FilePath", exe_path,
                "-CertificatePath", certificate_path
            ]

            if SAFE_SUBPROCESS_AVAILABLE:
                result = safe_subprocess_run(cmd, encoding='utf-8')
            else:
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

            # 清理临时脚本
            try:
                os.remove(script_path)
            except:
                pass

            if result.returncode == 0:
                print("[OK] PowerShell签名成功!")
                return True, "PowerShell签名成功"
            else:
                print(f"PowerShell签名失败: {result.stderr}")

    except Exception as e:
        print(f"PowerShell签名异常: {e}")

    # 方法3: 使用osslsigncode（如果可用）
    try:
        print("尝试使用osslsigncode签名...")
        cmd = [
            "osslsigncode", "sign",
            "-certs", certificate_path,
            "-t", "http://timestamp.digicert.com",
            "-in", exe_path,
            "-out", exe_path + ".signed"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(exe_path + ".signed"):
            # 替换原文件
            os.replace(exe_path + ".signed", exe_path)
            print("[OK] osslsigncode签名成功!")
            return True, "osslsigncode签名成功"
        else:
            print(f"osslsigncode签名失败或不可用")

    except Exception as e:
        print(f"osslsigncode签名异常: {e}")

    # 方法4: 创建签名信息文件
    print("创建数字签名信息文件...")
    signature_info = {
        "signature_info": {
            "file_name": os.path.basename(exe_path),
            "certificate_file": certificate_path,
            "signing_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tool": "Temu PDF重命名工具打包脚本",
            "version": "1.0",
            "description": "此文件已准备进行数字签名",
            "instructions": [
                f"使用证书文件 {certificate_path}",
                "使用signtool或类似工具对EXE文件进行签名",
                "建议添加时间戳以确保签名有效期"
            ]
        }
    }

    signature_file = exe_path.replace(".exe", "_signature_info.json")
    try:
        with open(signature_file, "w", encoding="utf-8") as f:
            json.dump(signature_info, f, indent=2, ensure_ascii=False)
        print(f"[OK] 已创建签名信息文件: {signature_file}")
        return True, f"已创建签名信息文件，请手动签名"
    except Exception as e:
        print(f"创建签名信息文件失败: {e}")
        return False, "签名失败"

def sign_exe_file_with_new_module(exe_path, config_path="code_signer/examples/project_config.py"):
    """使用新的签名模块进行代码签名"""
    if not NEW_SIGNER_AVAILABLE:
        print("[错误] 新的签名模块不可用")
        return False, "新签名模块不可用"

    print("[信息] 使用新的 code_signer 模块进行签名")

    try:
        # 尝试加载配置文件
        config_files = [
            "code_signer/examples/project_config.py",
            "signing_config.py"
        ]

        signer = None
        used_config = None

        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    print(f"[信息] 使用配置文件: {config_file}")
                    signer = CodeSigner.from_config(config_file)
                    used_config = config_file
                    break
                except Exception as e:
                    print(f"[警告] 配置文件 {config_file} 加载失败: {e}")
                    continue

        if signer is None:
            print("[信息] 使用默认配置")
            signer = CodeSigner()
            used_config = "默认配置"

        # 显示使用的配置信息
        print(f"[成功] 签名器初始化成功，使用配置: {used_config}")

        # 检查文件是否存在
        if not os.path.exists(exe_path):
            return False, f"文件不存在: {exe_path}"

        # 显示证书信息
        try:
            signer.display_certificate_info()
        except Exception as e:
            print(f"[警告] 显示证书信息失败: {e}")

        # 执行签名
        success, message = signer.sign_file(exe_path)

        if success:
            print(f"[成功] 新模块签名完成: {message}")
            return True, f"新模块签名: {message}"
        else:
            print(f"[失败] 新模块签名失败: {message}")
            return False, f"新模块签名失败: {message}"

    except Exception as e:
        error_msg = f"新模块签名异常: {e}"
        print(f"[错误] {error_msg}")
        return False, error_msg

def sign_exe_file_unified(exe_path):
    """统一的签名函数，优先使用新模块，回退到传统方式"""
    print("\n" + "=" * 50)
    print("开始数字签名流程")
    print("=" * 50)

    # 首先尝试使用新模块
    if NEW_SIGNER_AVAILABLE:
        print("[优先] 尝试使用新的 code_signer 模块")
        success, message = sign_exe_file_with_new_module(exe_path)
        if success:
            return success, message
        else:
            print(f"[回退] 新模块签名失败，尝试传统方式: {message}")
    else:
        print("[信息] 新签名模块不可用，使用传统签名方式")

    # 回退到传统签名方式
    certificate_path = "170859-code-signing.cer"
    if os.path.exists(certificate_path):
        print("[传统] 使用传统证书文件签名")
        return sign_exe_file(exe_path, certificate_path)
    else:
        print("[错误] 未找到证书文件，无法进行传统签名")
        return False, "未找到签名证书"

def create_portable_package():
    """创建便携包"""
    print("创建便携包...")

    portable_dir = "PDF重命名工具_便携版"
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir)

    # 复制exe文件
    exe_source = "dist/PDF_Rename_Operation.exe"
    exe_dest = f"{portable_dir}/PDF_Rename_Operation.exe"

    if os.path.exists(exe_source):
        shutil.copy2(exe_source, exe_dest)

        # 创建使用说明
        readme = f"""PDF重命名工具使用说明
==================

1. 双击运行"PDF_Rename_Operation.exe"
2. 输入测试方法，用分号分隔
   例如：Total Lead Content Test;Total Cadmium Content Test;Nickel Release Test
3. 选择PDF文件
4. 点击重命名开始处理

输出文件：
- PDF文件重命名为：Sampling ID-Report No-结论.pdf
- Excel报告在：C:\\Users\\chen-fr\\Desktop\\test\\1\\

注意事项：
- 确保PDF包含可提取的文本
- 首次运行可能需要几秒钟启动
- 如遇杀毒软件误报，请添加信任

数字签名信息：
- 本程序已准备数字签名
- 证书文件：170859-code-signing.cer
- 签名时间：{time.strftime("%Y-%m-%d %H:%M:%S")}

更新日期：{Path.cwd()}
"""

        with open(f"{portable_dir}/使用说明.txt", "w", encoding="utf-8") as f:
            f.write(readme)

        print("便携包创建完成")
        return True
    else:
        print("找不到exe文件，无法创建便携包")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("PDF重命名工具一键打包+签名程序")
    print("=" * 60)

    # 检查文件
    if not check_files():
        input("请确保所有必要文件都在当前目录，按回车退出...")
        return False

    # 检查签名证书
    certificate_path = "170859-code-signing.cer"
    has_certificate = os.path.exists(certificate_path)
    if has_certificate:
        print(f"[OK] 找到数字证书: {certificate_path}")
    else:
        print("[WARN]  未找到数字证书，将只进行打包")
        certificate_path = None

    # 安装缺少的包（包括PIL/Pillow）
    if not install_missing_packages():
        input("包安装失败，按回车退出...")
        return False

    # 清理旧文件
    clean_old_files()
    print("已清理旧的打包文件")

    # 打包
    if not build_exe():
        input("打包失败，按回车退出...")
        return False

    exe_path = "dist/PDF_Rename_Operation.exe"
    signature_status = ""

    # 代码签名（优先使用新模块）
    print("\n" + "=" * 40)
    print("数字签名检查")
    print("=" * 40)

    if NEW_SIGNER_AVAILABLE:
        print("[信息] 检测到新的 code_signer 模块，将优先使用")
        print("[信息] 支持多种配置方式: Python配置文件、JSON配置文件回退")
    else:
        print("[信息] 将使用传统签名方式")

    # 询问是否进行签名
    try:
        sign_choice = input("是否进行代码签名? (y/n): ").strip().lower()
        if sign_choice in ['y', 'yes', '是', '']:
            success, message = sign_exe_file_unified(exe_path)
            if success:
                signature_status = f" (已签名: {message})"
                print(f"[OK] 代码签名完成: {message}")
            else:
                signature_status = f" (签名失败: {message})"
                print(f"[ERROR] 代码签名失败: {message}")
                print("提示: 您可以稍后手动进行签名")
        else:
            print("跳过代码签名")
    except:
        print("跳过代码签名")

    # 创建便携包（包含签名后的文件）
    if not create_portable_package():
        input("便携包创建失败，按回车退出...")
        return False

    print("\n" + "=" * 50)
    print("[SUCCESS] 一键打包+签名完成!")
    print("=" * 50)
    print("生成的文件:")
    print(f"1. dist/PDF_Rename_Operation.exe{signature_status} - 单文件可执行程序")
    print("2. PDF重命名工具_便携版/ - 包含说明的完整包")

    if signature_status and "已签名" in signature_status:
        print("\n[OK] 数字签名信息:")
        print(f"   - 证书文件: {certificate_path}")
        print(f"   - 签名时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("   - 时间戳服务器: http://timestamp.digicert.com")

    # 询问是否打开文件夹
    try:
        choice = input("\n是否打开便携版目录? (y/n): ").strip().lower()
        if choice == 'y':
            os.startfile("PDF重命名工具_便携版")
    except:
        pass

    # 检查是否有签名信息文件
    signature_info_file = exe_path.replace(".exe", "_signature_info.json")
    if os.path.exists(signature_info_file):
        print(f"\n[FILE] 已生成签名说明文件: {signature_info_file}")
        print("   请参考此文件进行手动签名操作")

    input("\n按回车退出...")
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户取消操作")
        input("按回车退出...")
    except Exception as e:
        print(f"\n发生错误: {e}")
        input("按回车退出...")