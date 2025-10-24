# -*- coding: utf-8 -*-
"""
PDF重命名工具主程序
负责用户界面和应用程序的主要逻辑
"""
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog,
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PDF_Rename_UI import Ui_MainWindow
import subprocess
import webbrowser

# 导入自定义模块
from pdf_processor import PDFProcessor
from version_manager import get_version_manager, get_version, get_version_display_text

# 导入更新模块
try:
    from auto_updater import AutoUpdater, UpdateError
    AUTO_UPDATE_AVAILABLE = True
except ImportError as e:
    print(f"自动更新模块导入失败: {e}")
    AUTO_UPDATE_AVAILABLE = False

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow, Ui_MainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pdf_files = []
        self.processor = PDFProcessor()

        # 初始化更新器
        self.auto_updater = None
        if AUTO_UPDATE_AVAILABLE:
            try:
                self.auto_updater = AutoUpdater(self)
                logger.info("自动更新器初始化成功")
            except Exception as e:
                logger.error(f"自动更新器初始化失败: {e}")
                self.auto_updater = None

        # 连接信号和槽
        self.pushButton_2.clicked.connect(self.select_files)
        self.pushButton_3.clicked.connect(self.rename_files)
        self.pushButton.clicked.connect(self.test_method)  # 添加测试方法按钮连接

        # 设置动态菜单文本
        self.actionbangbenv1_0_0.setText(get_version_display_text())

        # 连接菜单事件
        self.actionUpdate.triggered.connect(self.check_for_updates)
        self.actionbangbenv1_0_0.triggered.connect(self.show_about_dialog)
        self.actionexit.triggered.connect(self.close)

        # 输出目录将根据用户选择的文件动态确定
        self.output_dir = None

        # 启动时检查更新（如果在生产环境）
        if self.auto_updater and getattr(sys, 'frozen', False):
            self.schedule_startup_update_check()

        logger.info("主窗口初始化完成")

    
    
    
    def select_files(self):
        """选择PDF文件"""
        default_dir = r"N:\XM Softlines\6. Personel\6. Daily Priority Testing List"
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            default_dir,
            "PDF文件 (*.pdf);;所有文件 (*)"
        )

        if files:
            self.pdf_files = files
            self.textBrowser.append(f"已选择 {len(files)} 个文件:")
            for file in files:
                self.textBrowser.append(f"  - {os.path.basename(file)}")
            self.textBrowser.append("")

            logger.info(f"选择了 {len(files)} 个PDF文件")

    def rename_files(self):
        """重命名文件"""
        if not self.pdf_files:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return

        test_methods_str = self.lineEdit.text()
        if not test_methods_str:
            QMessageBox.warning(self, "警告", "请输入测试方法，用分号分隔")
            return

        # 确认操作
        reply = QMessageBox.question(
            self,
            "确认",
            f"确定要重命名 {len(self.pdf_files)} 个文件吗？\n此操作将在原始位置重命名文件。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # 设置测试方法
        self.processor.set_test_methods(test_methods_str)

        # 禁用按钮
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)

        # 清空信息显示
        self.textBrowser.clear()
        self.textBrowser.append("开始重命名文件...\n")

        # 直接处理文件，不使用多线程
        results = self.process_files_directly()

        # 重新启用按钮
        self.pushButton_2.setEnabled(True)
        self.pushButton_3.setEnabled(True)

        # 生成Excel报告
        self.generate_excel_report(results)

        # 显示完成信息
        success_count = sum(1 for r in results if r['rename_success'])
        self.textBrowser.append(f"\n处理完成！成功: {success_count}/{len(results)}")

        if success_count < len(results):
            self.textBrowser.append("部分文件重命名失败，请检查错误信息。")

    def process_files_directly(self):
        """直接处理PDF文件，不使用多线程"""
        results = []

        try:
            for i, pdf_path in enumerate(self.pdf_files):
                self.textBrowser.append(f"正在处理第 {i+1}/{len(self.pdf_files)} 个文件: {os.path.basename(pdf_path)}")

                # 处理单个文件
                result = self.process_single_file(pdf_path)
                results.append(result)

                # 显示处理结果
                result_info = f"\n=== 处理结果 ===\n"
                result_info += f"文件: {os.path.basename(pdf_path)}\n"
                result_info += f"Sampling ID: {result['sampling_id']}\n"
                result_info += f"Report No: {result['report_no']}\n"
                result_info += f"测试结果: {result['test_results']}\n"
                result_info += f"最终结论: {result['final_conclusion']}\n"
                result_info += f"新文件名: {result['new_name']}\n"
                result_info += f"重命名状态: {'成功' if result['rename_success'] else '失败'}\n"

                if result['error']:
                    result_info += f"错误: {result['error']}\n"

                result_info += "-" * 50 + "\n"
                self.textBrowser.append(result_info)

                # 确保界面更新
                QApplication.processEvents()

            self.textBrowser.append("所有文件处理完成！")

        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            self.textBrowser.append(f"处理过程中发生错误: {e}")

        return results

    def process_single_file(self, pdf_path):
        """处理单个PDF文件"""
        try:
            # 提取PDF信息
            info = self.processor.extract_pdf_info(pdf_path)

            if info['error']:
                logger.error(f"提取PDF信息失败: {info['error']}")
                return {
                    'original_name': os.path.basename(pdf_path),
                    'new_name': os.path.basename(pdf_path),
                    'sampling_id': None,
                    'report_no': None,
                    'test_results': {},
                    'final_conclusion': 'Fail',
                    'rename_success': False,
                    'error': info['error']
                }

            # 生成新文件名
            new_filename = self.processor.generate_new_filename(
                info['sampling_id'],
                info['report_no'],
                info['final_conclusion']
            )

            # 重命名文件
            old_path = pdf_path
            new_path = os.path.join(os.path.dirname(old_path), new_filename)
            rename_success = True
            error_msg = None

            try:
                # 检查目标文件是否已存在
                if os.path.exists(new_path):
                    # 如果目标文件已存在，直接跳过重命名
                    rename_success = False
                    error_msg = f"目标文件已存在，跳过重命名: {new_filename}"
                    logger.warning(error_msg)
                else:
                    # 执行重命名
                    os.rename(old_path, new_path)
                    rename_success = True
                    logger.info(f"成功重命名: {os.path.basename(old_path)} -> {new_filename}")

            except Exception as e:
                rename_success = False
                error_msg = str(e)
                logger.error(f"重命名文件失败: {e}")

            return {
                'original_name': os.path.basename(pdf_path),
                'new_name': new_filename if rename_success else os.path.basename(pdf_path),
                'sampling_id': info['sampling_id'],
                'report_no': info['report_no'],
                'test_results': info['test_results'],
                'final_conclusion': info['final_conclusion'],
                'rename_success': rename_success,
                'error': error_msg
            }

        except Exception as e:
            logger.error(f"处理文件 {pdf_path} 时出错: {e}")
            return {
                'original_name': os.path.basename(pdf_path),
                'new_name': os.path.basename(pdf_path),
                'sampling_id': None,
                'report_no': None,
                'test_results': {},
                'final_conclusion': 'Fail',
                'rename_success': False,
                'error': str(e)
            }

    def test_method(self):
        """测试方法按钮功能 - 只处理第一个文件，不实际重命名"""
        if not self.pdf_files:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return

        test_methods_str = self.lineEdit.text()
        if not test_methods_str:
            QMessageBox.warning(self, "警告", "请输入测试方法，用分号分隔")
            return

        # 设置测试方法
        self.processor.set_test_methods(test_methods_str)

        # 清空信息显示
        self.textBrowser.clear()
        self.textBrowser.append("=== 测试模式 - 只处理第一个文件 ===\n")

        # 只处理第一个选中的文件
        test_file = self.pdf_files[0]
        self.textBrowser.append(f"测试文件: {os.path.basename(test_file)}\n")

        try:
            # 提取PDF信息
            info = self.processor.extract_pdf_info(test_file)

            if info['error']:
                self.textBrowser.append(f"ERROR: {info['error']}")
                return

            # 显示提取的信息
            result_info = f"\n=== 测试结果 ===\n"
            result_info += f"文件: {os.path.basename(test_file)}\n"
            result_info += f"Sampling ID: {info['sampling_id']}\n"
            result_info += f"Report No: {info['report_no']}\n"

            # 显示每个测试方法的结果
            for test_method, result in info['test_results'].items():
                result_info += f"测试方法 '{test_method}': {result}\n"

            result_info += f"最终结论: {info['final_conclusion']}\n"

            # 生成新文件名但不实际重命名
            new_filename = self.processor.generate_new_filename(
                info['sampling_id'],
                info['report_no'],
                info['final_conclusion']
            )
            result_info += f"新文件名: {new_filename}\n"
            result_info += "注意：测试模式，文件未实际重命名\n"

            self.textBrowser.append(result_info)

        except Exception as e:
            logger.error(f"测试过程中出错: {e}")
            self.textBrowser.append(f"测试过程中出错: {e}")

    def _get_output_directory(self) -> str:
        """获取Excel报告输出目录"""
        if self.pdf_files:
            return os.path.dirname(self.pdf_files[0])
        return os.getcwd()

    def _ensure_directory_writable(self, directory: str) -> bool:
        """确保目录可写"""
        try:
            test_file = os.path.join(directory, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"目录可写性验证通过: {directory}")
            return True
        except Exception as e:
            logger.warning(f"目录不可写: {directory}, 错误: {e}")
            return False

    def generate_excel_report(self, results):
        """生成Excel报告"""
        try:
            # 获取输出目录
            output_directory = self._get_output_directory()

            # 验证目录可写性
            if not self._ensure_directory_writable(output_directory):
                # 如果当前目录不可写，尝试使用临时目录
                import tempfile
                output_directory = tempfile.gettempdir()
                self.textBrowser.append(f"警告：原目录不可写，报告将保存到临时目录: {output_directory}")
                logger.info(f"使用临时目录作为输出目录: {output_directory}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"pdf_rename_report_{timestamp}.xlsx"
            excel_path = os.path.join(output_directory, excel_filename)

            # 准备数据
            data = []
            for result in results:
                row = {
                    '原始文件名': result['original_name'],
                    '新文件名': result['new_name'],
                    'Sampling ID': result['sampling_id'],
                    'Report No': result['report_no'],
                    '最终结论': result['final_conclusion'],
                    '重命名状态': '成功' if result['rename_success'] else '失败'
                }

                # 添加测试结果列
                for test_method, test_result in result['test_results'].items():
                    row[f"测试_{test_method}"] = test_result

                if result['error']:
                    row['错误信息'] = result['error']

                data.append(row)

            # 创建DataFrame并保存
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)

            self.textBrowser.append(f"Excel报告已生成: {excel_path}")
            logger.info(f"Excel报告已保存: {excel_path}")

        except Exception as e:
            logger.error(f"生成Excel报告失败: {e}")
            self.textBrowser.append(f"生成Excel报告失败: {e}")

    def schedule_startup_update_check(self):
        """安排启动时的更新检查"""
        try:
            # 延迟3秒后检查更新，避免影响启动速度
            QTimer.singleShot(3000, self.startup_update_check)
        except Exception as e:
            logger.error(f"安排启动更新检查失败: {e}")

    def startup_update_check(self):
        """启动时的更新检查"""
        try:
            if self.auto_updater:
                has_update, remote_version, local_version, error = self.auto_updater.check_for_updates()
                if has_update:
                    reply = QMessageBox.question(
                        self,
                        "发现新版本",
                        f"发现新版本 {remote_version}！\n当前版本: {local_version}\n\n是否立即下载更新？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.start_update_process()
                elif error:
                    logger.warning(f"启动更新检查失败: {error}")
        except Exception as e:
            logger.error(f"启动更新检查异常: {e}")

    def check_for_updates(self):
        """手动检查更新（菜单点击）"""
        if not self.auto_updater:
            QMessageBox.warning(self, "更新功能不可用", "自动更新功能未正确初始化")
            return

        try:
            # 显示检查进度
            self.textBrowser.append("正在检查更新...")
            QApplication.processEvents()

            has_update, remote_version, local_version, error = self.auto_updater.check_for_updates(force_check=True)

            if error:
                QMessageBox.warning(self, "检查更新失败", f"检查更新时发生错误：\n{error}")
                self.textBrowser.append(f"检查更新失败: {error}")
                return

            if has_update:
                reply = QMessageBox.question(
                    self,
                    "发现新版本",
                    f"发现新版本 {remote_version}！\n当前版本: {local_version}\n\n是否立即下载更新？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.start_update_process(remote_version)
            else:
                QMessageBox.information(self, "检查更新", "您的软件已是最新版本！")
                self.textBrowser.append("您的软件已是最新版本")

        except Exception as e:
            logger.error(f"检查更新异常: {e}")
            QMessageBox.critical(self, "错误", f"检查更新时发生异常：\n{str(e)}")

    def start_update_process(self, version=None):
        """开始更新过程"""
        if not self.auto_updater:
            return

        try:
            # 创建并显示更新进度对话框
            progressDialog = UpdateProgressDialog(self)

            # 如果没有指定版本，先获取最新版本
            if not version:
                has_update, remote_version, local_version, error = self.auto_updater.check_for_updates(force_check=True)
                if has_update:
                    version = remote_version
                else:
                    QMessageBox.information(self, "无需更新", "您的软件已是最新版本")
                    return

            # 开始下载更新
            progressDialog.start_update(version, self.auto_updater)
            progressDialog.exec_()

        except Exception as e:
            logger.error(f"启动更新过程失败: {e}")
            QMessageBox.critical(self, "更新失败", f"启动更新过程时发生错误：\n{str(e)}")

    def show_about_dialog(self):
        """显示关于对话框"""
        try:
            dialog = AboutDialog(self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"显示关于对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"显示关于对话框时发生错误：\n{str(e)}")


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.auto_updater = getattr(parent, 'auto_updater', None)
        self.init_ui()
        self.load_version_info()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(get_version_manager().get_about_dialog_title())
        self.setFixedSize(450, 400)
        self.setModal(True)

        layout = QVBoxLayout()

        # 应用程序名称和版本
        title_label = QLabel("PDF重命名工具")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)

        # 版本信息
        self.version_label = QLabel("正在加载版本信息...")
        self.version_label.setAlignment(Qt.AlignCenter)

        # 构建信息
        self.build_info_label = QLabel("")
        self.build_info_label.setAlignment(Qt.AlignCenter)
        self.build_info_label.setStyleSheet("color: gray; font-size: 10px;")

        # 更新状态
        self.update_status_label = QLabel("正在检查更新状态...")
        self.update_status_label.setAlignment(Qt.AlignCenter)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        # 详细信息区域
        info_layout = QVBoxLayout()

        # GitHub链接
        self.github_link_label = QLabel("GitHub: chen-huai/Temu_PDF_Rename_APP")
        self.github_link_label.setStyleSheet("color: blue; text-decoration: underline;")
        self.github_link_label.setCursor(Qt.PointingHandCursor)

        # 最后检查时间
        self.last_check_label = QLabel("")

        # 配置信息
        self.config_info_label = QLabel("")

        info_layout.addWidget(self.github_link_label)
        info_layout.addWidget(self.last_check_label)
        info_layout.addWidget(self.config_info_label)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.check_update_btn = QPushButton("检查更新")
        self.check_update_btn.clicked.connect(self.check_for_updates)

        self.view_release_notes_btn = QPushButton("查看更新日志")
        self.view_release_notes_btn.clicked.connect(self.view_release_notes)

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.check_update_btn)
        button_layout.addWidget(self.view_release_notes_btn)
        button_layout.addWidget(self.close_btn)

        # 添加所有控件到布局
        layout.addWidget(title_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.build_info_label)
        layout.addWidget(self.update_status_label)
        layout.addWidget(line)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 设置事件
        self.github_link_label.mousePressEvent = self.open_github_page

    def load_version_info(self):
        """加载版本信息"""
        try:
            # 显示当前版本
            if self.auto_updater:
                local_version = self.auto_updater.version_manager.get_local_version()
                self.version_label.setText(f"版本: {local_version}")

                # 异步检查更新状态
                self.check_update_status_async()
            else:
                self.version_label.setText(f"版本: {get_version()}")
                self.update_status_label.setText("自动更新功能不可用")
                self.check_update_btn.setEnabled(False)

        except Exception as e:
            self.version_label.setText(f"版本: {get_version()}")
            self.update_status_label.setText(f"获取版本信息失败: {str(e)}")

    def check_update_status_async(self):
        """异步检查更新状态"""
        try:
            # 使用定时器延迟执行，避免阻塞UI
            QTimer.singleShot(100, self._perform_status_check)
        except Exception as e:
            self.update_status_label.setText(f"检查更新状态失败: {str(e)}")

    def _perform_status_check(self):
        """执行更新状态检查"""
        try:
            if not self.auto_updater:
                return

            has_update, remote_version, local_version, error = self.auto_updater.check_for_updates()

            if error:
                self.update_status_label.setText("无法检查更新状态")
            elif has_update:
                self.update_status_label.setText(f"🆕 发现新版本: {remote_version}")
                self.update_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.update_status_label.setText("✅ 已是最新版本")
                self.update_status_label.setStyleSheet("color: blue;")

        except Exception as e:
            self.update_status_label.setText(f"检查更新状态失败: {str(e)}")

    def check_for_updates(self):
        """检查更新"""
        try:
            if self.parent:
                self.parent.check_for_updates()
                self.accept()  # 关闭关于对话框
        except Exception as e:
            QMessageBox.warning(self, "错误", f"检查更新失败: {str(e)}")

    def open_github_page(self, event):
        """打开GitHub页面"""
        try:
            webbrowser.open("https://github.com/chen-huai/Temu_PDF_Rename_APP")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开GitHub页面: {str(e)}")

    def view_release_notes(self):
        """查看更新日志"""
        try:
            if self.auto_updater:
                has_update, remote_version, local_version, error = self.auto_updater.check_for_updates()

                if error:
                    QMessageBox.warning(self, "错误", f"获取更新日志失败: {error}")
                    return

                # 获取最新版本的发布说明
                release_notes = self.auto_updater.github_client.get_release_notes(local_version)

                # 创建发布说明对话框
                dialog = QMessageBox(self)
                dialog.setWindowTitle("更新日志")
                dialog.setText(f"版本 {local_version} 更新日志:")
                dialog.setInformativeText(release_notes)
                dialog.setStandardButtons(QMessageBox.Ok)
                dialog.exec_()
            else:
                QMessageBox.information(self, "信息", "无法获取更新日志：更新功能不可用")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"查看更新日志失败: {str(e)}")


class UpdateThread(QThread):
    """更新线程"""
    progress_signal = pyqtSignal(int, int, int)  # downloaded, total, percentage
    status_signal = pyqtSignal(str)  # 状态信息
    finished_signal = pyqtSignal(bool, str)  # 是否成功, 错误信息

    def __init__(self, auto_updater, version):
        super().__init__()
        self.auto_updater = auto_updater
        self.version = version

    def run(self):
        """执行更新过程"""
        try:
            self.status_signal.emit("正在下载更新文件...")

            # 下载更新文件
            success, download_path, error = self.auto_updater.download_update(
                self.version,
                self.progress_callback
            )

            if not success:
                self.finished_signal.emit(False, f"下载失败: {error}")
                return

            self.status_signal.emit("正在安装更新...")

            # 执行更新
            success, error = self.auto_updater.execute_update(download_path)

            if success:
                self.finished_signal.emit(True, None)
            else:
                self.finished_signal.emit(False, f"安装失败: {error}")

        except Exception as e:
            self.finished_signal.emit(False, f"更新过程异常: {str(e)}")

    def progress_callback(self, downloaded, total, percentage):
        """进度回调"""
        self.progress_signal.emit(downloaded, total, percentage)


class UpdateProgressDialog(QDialog):
    """更新进度对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正在更新")
        self.setFixedSize(400, 150)
        self.setModal(True)
        self.update_thread = None
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 状态标签
        self.status_label = QLabel("准备更新...")
        self.status_label.setAlignment(Qt.AlignCenter)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_update)
        self.cancel_btn.setEnabled(False)  # 开始后不允许取消

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)

    def start_update(self, version, auto_updater):
        """开始更新"""
        try:
            self.status_label.setText(f"正在更新到版本 {version}...")
            self.progress_bar.setValue(0)
            self.cancel_btn.setEnabled(False)

            # 创建并启动更新线程
            self.update_thread = UpdateThread(auto_updater, version)
            self.update_thread.progress_signal.connect(self.update_progress)
            self.update_thread.status_signal.connect(self.update_status)
            self.update_thread.finished_signal.connect(self.update_finished)
            self.update_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动更新失败: {str(e)}")
            self.reject()

    def update_progress(self, downloaded, total, percentage):
        """更新进度"""
        if percentage >= 0:  # 正常进度更新
            self.progress_bar.setValue(percentage)
        else:  # 等待状态
            self.progress_bar.setRange(0, 0)  # 无限进度条
            self.status_label.setText(f"等待重试，{-percentage}秒后重试...")

    def update_status(self, status):
        """更新状态"""
        self.status_label.setText(status)

    def update_finished(self, success, error):
        """更新完成"""
        if success:
            self.status_label.setText("更新完成！应用程序将重启...")
            self.progress_bar.setValue(100)

            # 2秒后关闭对话框并重启应用
            QTimer.singleShot(2000, self.restart_application)
        else:
            self.status_label.setText(f"更新失败: {error}")
            self.progress_bar.setValue(0)
            self.cancel_btn.setEnabled(True)
            QMessageBox.critical(self, "更新失败", f"更新失败：\n{error}")

    def restart_application(self):
        """重启应用程序"""
        try:
            # 关闭对话框
            self.accept()

            # 重启应用
            if getattr(sys, 'frozen', False):
                # 打包后的exe
                subprocess.Popen([sys.executable])
            else:
                # 开发环境
                subprocess.Popen([sys.executable, sys.argv[0]])

            # 退出当前应用
            QApplication.quit()

        except Exception as e:
            QMessageBox.critical(self, "重启失败", f"重启应用程序失败: {str(e)}")
            self.reject()

    def cancel_update(self):
        """取消更新"""
        if self.update_thread and self.update_thread.isRunning():
            self.update_thread.terminate()
            self.update_thread.wait()

        self.reject()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("PDF重命名工具")
    app.setOrganizationName("Temu")

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    logger.info("应用程序启动")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()