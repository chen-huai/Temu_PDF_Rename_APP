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
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PDF_Rename_UI import Ui_MainWindow

# 导入自定义模块
from pdf_processor import PDFProcessor

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow, Ui_MainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pdf_files = []
        self.processor = PDFProcessor()

        # 连接信号和槽
        self.pushButton_2.clicked.connect(self.select_files)
        self.pushButton_3.clicked.connect(self.rename_files)
        self.pushButton.clicked.connect(self.test_method)  # 添加测试方法按钮连接

        # 输出目录将根据用户选择的文件动态确定
        self.output_dir = None

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
