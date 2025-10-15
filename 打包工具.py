# -*- coding: utf-8 -*-
"""
PDF重命名工具打包脚本
双击运行即可打包成exe文件
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

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
        "--noconfirm",
        "PDF_Rename_Operation.py"
    ]

    try:
        print("正在执行打包命令...")
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
    print("=" * 50)
    print("PDF重命名工具打包程序")
    print("=" * 50)

    # 检查文件
    if not check_files():
        input("请确保所有必要文件都在当前目录，按回车退出...")
        return False

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

    # 创建便携包
    if not create_portable_package():
        input("便携包创建失败，按回车退出...")
        return False

    print("\n打包完成!")
    print("生成的文件:")
    print("1. dist/PDF_Rename_Operation.exe - 单文件可执行程序")
    print("2. PDF重命名工具_便携版/ - 包含说明的完整包")

    # 询问是否打开文件夹
    try:
        choice = input("\n是否打开便携版目录? (y/n): ").strip().lower()
        if choice == 'y':
            os.startfile("PDF重命名工具_便携版")
    except:
        pass

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