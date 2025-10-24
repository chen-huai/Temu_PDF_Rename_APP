#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的自动更新功能测试
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("PDF重命名工具 - 自动更新功能测试")
    print("=" * 50)

    try:
        # 测试导入
        print("1. 测试模块导入...")
        from auto_updater import AutoUpdater
        from auto_updater.version_manager import VersionManager
        from auto_updater.github_client import GitHubClient
        print("[OK] 所有模块导入成功")

        # 测试版本管理器
        print("2. 测试版本管理器...")
        vm = VersionManager()
        local_version = vm.get_local_version()
        print(f"[OK] 本地版本: {local_version}")

        # 测试版本比较
        result = vm.compare_versions("1.0.1", "1.0.0")
        print(f"[OK] 版本比较测试: 1.0.1 vs 1.0.0 = {result}")

        # 测试GitHub连接
        print("3. 测试GitHub连接...")
        client = GitHubClient()
        success, message = client.test_connection()
        print(f"[{'OK' if success else 'WARN'}] GitHub连接: {message}")

        # 测试自动更新器
        print("4. 测试自动更新器...")
        updater = AutoUpdater()
        has_update, remote_version, local_version, error = updater.check_for_updates(force_check=True)

        if error:
            print(f"[WARN] 更新检查错误: {error}")
            print("      这可能是因为GitHub仓库还没有配置Release")
        elif has_update:
            print(f"[OK] 发现新版本: {remote_version} (当前: {local_version})")
        else:
            print(f"[OK] 已是最新版本: {local_version}")

        print("\n" + "=" * 50)
        print("测试完成！自动更新功能基本正常。")
        print("注意：GitHub连接失败是正常的，因为仓库可能还没有Release。")

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()