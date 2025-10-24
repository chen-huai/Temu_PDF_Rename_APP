#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本更新工具
统一更新应用程序版本号，确保所有文件同步更新
使用方法: python update_version.py 2.1.0
"""

import sys
import os
import argparse
from version_manager import update_app_version, get_version_manager, get_version

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='更新应用程序版本号')
    parser.add_argument('version', help='新的版本号 (例如: 2.1.0)')
    parser.add_argument('--verify', action='store_true', help='仅验证当前版本一致性，不更新')
    parser.add_argument('--sync', action='store_true', help='同步所有版本文件，不更新版本号')

    args = parser.parse_args()

    # 获取版本管理器
    version_manager = get_version_manager()

    print("=" * 60)
    print("PDF重命名工具 - 版本管理器")
    print("=" * 60)

    if args.verify:
        # 验证模式
        print(f"当前版本: {get_version()}")
        print("\n验证版本一致性...")

        version_info = version_manager.get_all_version_info()
        print(f"代码版本: {version_info['version']}")
        print(f"版本文件: {version_info['file_version']}")
        print(f"显示文本: {version_info['display_text']}")
        print(f"关于标题: {version_info['about_title']}")

        if version_info['file_version'] == version_info['version']:
            print("✅ 版本一致性验证通过")
            return 0
        else:
            print("❌ 版本一致性验证失败")
            print("建议使用 --sync 参数同步版本")
            return 1

    elif args.sync:
        # 同步模式
        print(f"同步所有版本文件到当前版本: {get_version()}")
        try:
            version_manager.sync_all_versions()
            print("✅ 版本同步完成")
            return 0
        except Exception as e:
            print(f"❌ 版本同步失败: {e}")
            return 1

    else:
        # 更新模式
        new_version = args.version
        current_version = get_version()

        print(f"当前版本: {current_version}")
        print(f"目标版本: {new_version}")

        if current_version == new_version:
            print("✅ 版本号已经是最新，无需更新")
            return 0

        # 确认更新
        response = input(f"\n确认将版本从 {current_version} 更新到 {new_version}? (y/N): ")
        if response.lower() not in ['y', 'yes', '是']:
            print("操作已取消")
            return 0

        try:
            # 执行版本更新
            print(f"\n正在更新版本到 {new_version}...")
            update_app_version(new_version)

            # 同步所有版本文件
            print("正在同步版本文件...")
            version_manager.sync_all_versions()

            print("\n✅ 版本更新完成！")
            print(f"新版本: {get_version()}")

            print("\n更新内容:")
            print("  - version_manager.py")
            print("  - PDF_Rename_Operation.py")
            print("  - version.txt")
            print("  - update_config.json (如存在)")

            print("\n建议后续操作:")
            print("  1. 测试应用程序功能")
            print("  2. 更新 CHANGELOG.md")
            print("  3. 创建 Git 标签和 Release")

            return 0

        except Exception as e:
            print(f"❌ 版本更新失败: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main())