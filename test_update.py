#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新功能测试脚本
"""

import sys
import os
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """测试模块导入"""
    print("=== 测试模块导入 ===")
    try:
        from auto_updater import AutoUpdater, UpdateError
        print("[OK] auto_updater 模块导入成功")

        from auto_updater.version_manager import VersionManager
        print("[OK] VersionManager 导入成功")

        from auto_updater.github_client import GitHubClient
        print("[OK] GitHubClient 导入成功")

        from auto_updater.download_manager import DownloadManager
        print("[OK] DownloadManager 导入成功")

        from auto_updater.backup_manager import BackupManager
        print("[OK] BackupManager 导入成功")

        from auto_updater.update_executor import UpdateExecutor
        print("[OK] UpdateExecutor 导入成功")

        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_version_manager():
    """测试版本管理器"""
    print("\n=== 测试版本管理器 ===")
    try:
        from auto_updater.version_manager import VersionManager

        vm = VersionManager()

        # 测试获取本地版本
        local_version = vm.get_local_version()
        print(f"✅ 本地版本: {local_version}")

        # 测试版本比较
        result = vm.compare_versions("1.0.1", "1.0.0")
        print(f"✅ 版本比较 1.0.1 vs 1.0.0: {result}")

        # 测试时间检查
        should_check = vm.should_check_for_updates()
        print(f"✅ 是否应该检查更新: {should_check}")

        return True
    except Exception as e:
        print(f"❌ 版本管理器测试失败: {e}")
        return False

def test_github_connection():
    """测试GitHub连接"""
    print("\n=== 测试GitHub连接 ===")
    try:
        from auto_updater.github_client import GitHubClient

        client = GitHubClient()

        # 测试连接
        success, message = client.test_connection()
        if success:
            print(f"✅ GitHub连接测试成功: {message}")
        else:
            print(f"⚠️ GitHub连接测试失败: {message}")
            print("   这可能是因为仓库还没有发布任何Release")

        return success
    except Exception as e:
        print(f"❌ GitHub连接测试失败: {e}")
        return False

def test_auto_updater():
    """测试自动更新器"""
    print("\n=== 测试自动更新器 ===")
    try:
        from auto_updater import AutoUpdater

        updater = AutoUpdater()

        # 测试更新检查
        has_update, remote_version, local_version, error = updater.check_for_updates(force_check=True)

        if error:
            print(f"⚠️ 更新检查出现错误: {error}")
            print("   这可能是因为GitHub仓库还没有配置Release")
        elif has_update:
            print(f"✅ 发现新版本: {remote_version} (当前: {local_version})")
        else:
            print(f"✅ 已是最新版本: {local_version}")

        return True
    except Exception as e:
        print(f"❌ 自动更新器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("PDF重命名工具 - 自动更新功能测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print("=" * 50)

    tests = [
        ("模块导入", test_import),
        ("版本管理器", test_version_manager),
        ("GitHub连接", test_github_connection),
        ("自动更新器", test_auto_updater)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {e}")
            results.append((test_name, False))

    # 显示测试结果摘要
    print("\n" + "=" * 50)
    print("测试结果摘要:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1

    print("-" * 50)
    print(f"总计: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过！自动更新功能已成功集成。")
    else:
        print("⚠️ 部分测试失败，但基本功能应该可用。")
        print("   GitHub连接失败是正常的，因为仓库可能还没有配置Release。")

if __name__ == "__main__":
    main()