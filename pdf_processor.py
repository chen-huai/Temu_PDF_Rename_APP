# -*- coding: utf-8 -*-
"""
PDF处理器模块
负责PDF文本提取、信息分析和重命名处理
重新设计为简洁的单线程处理模式
"""
import os
import re
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional
import PyPDF2

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF处理类，负责提取PDF信息和重命名"""

    def __init__(self):
        self.test_methods = []

    def set_test_methods(self, methods_str: str):
        """设置测试方法列表"""
        self.test_methods = [method.strip() for method in methods_str.split(';') if method.strip()]
        logger.info(f"设置测试方法: {self.test_methods}")

    def extract_pdf_info(self, pdf_path: str) -> Dict[str, any]:
        """从PDF中提取信息：Sampling ID, Report No, 测试方法和结论"""
        try:
            # 检查文件是否存在
            if not os.path.exists(pdf_path):
                return {
                    'sampling_id': None,
                    'report_no': None,
                    'test_results': {},
                    'final_conclusion': 'Fail',
                    'error': f"文件不存在: {pdf_path}"
                }

            # 提取PDF文本内容
            text = self._extract_pdf_text(pdf_path)
            if not text:
                return {
                    'sampling_id': None,
                    'report_no': None,
                    'test_results': {},
                    'final_conclusion': 'Fail',
                    'error': "PDF文本为空，可能是扫描版PDF或受保护的PDF"
                }

            # 提取各项信息
            sampling_id = self._extract_sampling_id(text)
            report_no = self._extract_report_no(text)
            test_results = self._extract_test_results(text)

            # 判断最终结论 - 详细逻辑
            logger.info(f"测试结果详情: {test_results}")

            if not test_results:
                # 如果没有找到任何测试结果
                final_conclusion = 'Fail'
                logger.warning("未找到任何测试结果，默认为Fail")
            else:
                # 检查是否有明确的Fail结果
                has_fail = any(result == 'Fail' for result in test_results.values())
                # 检查是否所有结果都是Pass
                all_pass = all(result == 'Pass' for result in test_results.values())

                if has_fail:
                    final_conclusion = 'Fail'
                    logger.info("发现测试方法结果为Fail，最终结论为Fail")
                elif all_pass:
                    final_conclusion = 'Pass'
                    logger.info("所有测试方法结果都为Pass，最终结论为Pass")
                else:
                    # 有未找到的测试方法，保守处理为Fail
                    final_conclusion = 'Fail'
                    logger.warning("部分测试方法未找到明确结论，保守处理为Fail")

            logger.info(f"提取完成: Sampling ID={sampling_id}, Report No={report_no}, 最终结论={final_conclusion}")

            return {
                'sampling_id': sampling_id,
                'report_no': report_no,
                'test_results': test_results,
                'final_conclusion': final_conclusion,
                'error': None
            }

        except Exception as e:
            error_msg = self._handle_error(e)
            logger.error(f"处理PDF失败: {error_msg}")
            return {
                'sampling_id': None,
                'report_no': None,
                'test_results': {},
                'final_conclusion': 'Fail',
                'error': error_msg
            }

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """提取PDF所有页面的文本内容"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # 提取所有页面的文本
                text = ""
                page_count = len(pdf_reader.pages)
                logger.info(f"PDF总页数: {page_count}")

                for i in range(page_count):
                    try:
                        page_text = pdf_reader.pages[i].extract_text()
                        if page_text:
                            text += page_text + " "
                            logger.debug(f"第 {i+1} 页提取成功，文本长度: {len(page_text)}")
                        else:
                            logger.warning(f"第 {i+1} 页文本为空")
                    except Exception as e:
                        logger.warning(f"提取第 {i+1} 页文本失败: {e}")
                        continue

                total_length = len(text.strip())
                logger.info(f"PDF文本提取完成，总文本长度: {total_length} 字符")

                if total_length == 0:
                    logger.warning("PDF所有页面文本均为空")
                else:
                    logger.debug(f"提取的文本前100个字符: {text[:100]}")

                return text.strip()

        except Exception as e:
            # 检查是否是加密相关的错误
            error_msg = str(e)
            if "encrypted" in error_msg.lower() or "password" in error_msg.lower():
                logger.warning(f"PDF可能已加密，尝试直接读取: {error_msg}")
                # 对于加密PDF，我们仍然尝试提取所有页面的文本
                try:
                    with open(pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        text = ""
                        page_count = len(pdf_reader.pages)

                        for i in range(page_count):
                            try:
                                page_text = pdf_reader.pages[i].extract_text()
                                if page_text:
                                    text += page_text + " "
                            except:
                                continue

                        if text:
                            logger.info(f"成功从可能的加密PDF中提取到文本: {len(text)} 字符")
                            return text.strip()
                except Exception as retry_e:
                    logger.error(f"从加密PDF提取文本也失败: {retry_e}")

            raise Exception(f"提取PDF文本失败: {str(e)}")

    def _handle_error(self, error: Exception) -> str:
        """处理错误信息"""
        error_msg = str(error)

        if "PyCryptodome" in error_msg:
            return "PDF文件需要PyCryptodome库来处理加密，请运行: pip install PyCryptodome"
        elif "encrypted" in error_msg.lower():
            return "PDF文件已加密，请提供无密码的PDF文件"
        elif "Empty" in error_msg or "no pages" in error_msg.lower():
            return "PDF文件为空或无页面，请检查文件完整性"
        else:
            return error_msg

    def _extract_sampling_id(self, text: str) -> Optional[str]:
        """提取Sampling ID - 从同一行中提取关键词后的值"""
        lines = text.split('\n')
        logger.debug(f"开始提取Sampling ID，总行数: {len(lines)}")
        logger.debug(f"前10行内容: {lines[:10]}")

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 查找包含 "Sampling ID:" 的行
            if re.search(r'Sampling\s*ID\s*:', line, re.IGNORECASE):
                logger.debug(f"找到Sampling ID行 {line_num}: '{line}'")

                # 提取冒号后面的所有内容
                match = re.search(r'Sampling\s*ID\s*:\s*(.+)', line, re.IGNORECASE)
                if match:
                    sampling_id = match.group(1).strip()
                    # 清理掉多余的空格和特殊字符，但保留点、横线、下划线
                    sampling_id = re.sub(r'\s+', '', sampling_id)  # 去除所有空格
                    sampling_id = re.sub(r'[^\w\.\-_/]', '', sampling_id)  # 只保留字母数字和常用符号

                    if sampling_id:
                        logger.info(f"提取到Sampling ID: '{sampling_id}'")
                        return sampling_id

        logger.warning("未找到Sampling ID")
        return None

    def _extract_report_no(self, text: str) -> Optional[str]:
        """提取Report No - 从同一行中提取关键词后的值"""
        lines = text.split('\n')
        logger.debug(f"开始提取Report No，总行数: {len(lines)}")

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 查找包含 "Report No.:" 的行
            if re.search(r'Report\s*No\.?\s*:', line, re.IGNORECASE):
                logger.debug(f"找到Report No行 {line_num}: '{line}'")

                # 提取冒号后面的所有内容
                match = re.search(r'Report\s*No\.?\s*:\s*(.+)', line, re.IGNORECASE)
                if match:
                    report_no = match.group(1).strip()
                    # 清理掉多余的空格和特殊字符，但保留点、横线、下划线
                    report_no = re.sub(r'\s+', '', report_no)  # 去除所有空格
                    report_no = re.sub(r'[^\w\.\-_/]', '', report_no)  # 只保留字母数字和常用符号

                    if report_no:
                        logger.info(f"提取到Report No: '{report_no}'")
                        return report_no

        logger.warning("未找到Report No")
        return None

    def _extract_test_results(self, text: str) -> Dict[str, str]:
        """提取测试方法和结论 - 按行处理"""
        test_results = {}
        lines = text.split('\n')

        logger.debug(f"开始提取测试结果，总行数: {len(lines)}")
        logger.debug(f"前20行内容: {lines[:20]}")

        for test_method in self.test_methods:
            logger.debug(f"查找测试方法: {test_method}")
            conclusion = self._find_conclusion_for_method_lines(lines, test_method)
            test_results[test_method] = conclusion
            logger.debug(f"测试方法 '{test_method}' 结论: {conclusion}")

        return test_results

    def _find_conclusion_for_method_lines(self, lines: List[str], test_method: str) -> str:
        """为特定测试方法查找结论 - 按行处理版本"""
        logger.debug(f"正在按行查找测试方法 '{test_method}' 的结论...")

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 查找包含测试方法的行
            if re.search(re.escape(test_method), line, re.IGNORECASE):
                logger.debug(f"找到测试方法 '{test_method}' 在行 {i}: '{line}'")

                # 从当前行开始，向下查找包含Pass/Fail的行
                conclusion_count = 0
                for j in range(i + 1, min(i + 15, len(lines))):  # 向下查找15行
                    search_line = lines[j].strip()
                    if not search_line:
                        continue

                    logger.debug(f"检查行 {j}: '{search_line}'")

                    # 检查该行是否包含Pass/Fail关键词
                    conclusion = self._extract_conclusion_from_line(search_line)
                    if conclusion:
                        conclusion_count += 1
                        logger.debug(f"找到第 {conclusion_count} 个结论 '{conclusion}' 在行 {j}: '{search_line}'")

                        # 如果是第二个结论，则返回
                        if conclusion_count == 2:
                            logger.info(f"测试方法 '{test_method}' 找到第二个结论: {conclusion}")
                            return conclusion
                    else:
                        # 如果该行不包含结论，但有大量描述性文本，可能不是我们想要的结论
                        if len(search_line) > 50 and not any(keyword in search_line.lower()
                            for keyword in ['pass', 'fail', 'compliant', 'non-compliant', '符合', '不合格']):
                            logger.debug(f"行 {j} 包含描述性文本，跳过: '{search_line[:50]}...'")

        logger.warning(f"未找到测试方法 '{test_method}' 的第二个结论，默认为Fail")
        return 'Fail'

    def _extract_conclusion_from_line(self, line: str) -> Optional[str]:
        """从行中提取结论"""
        pass_keywords = ['pass', 'compliant', '符合', '合格', '通过', 'ok', 'yes']
        fail_keywords = ['fail', 'non-compliant', '不符合', '不合格', '不通过', 'failed', 'no', 'ng']

        line_lower = line.lower()

        # 先检查Fail关键词（优先级更高）
        for keyword in fail_keywords:
            if keyword in line_lower:
                return 'Fail'

        # 再检查Pass关键词
        for keyword in pass_keywords:
            if keyword in line_lower:
                return 'Pass'

        return None

    def _find_conclusion_for_method(self, words: List[str], test_method: str) -> str:
        """为特定测试方法查找结论 - 保留兼容性"""
        logger.debug(f"正在查找测试方法 '{test_method}' 的结论...")

        for i, word in enumerate(words):
            if re.search(re.escape(test_method), word, re.IGNORECASE):
                logger.debug(f"找到测试方法 '{test_method}' 在位置 {i}: '{word}'")

                # 跳过测试方法名称后的空白和标点符号
                # 查找后面第一个有效的结论词（Pass/Fail）
                for j in range(i + 1, min(i + 20, len(words))):  # 扩大搜索范围到20个词
                    # 跳过纯数字、标点符号和空词
                    candidate_word = words[j].strip()

                    # 跳过编号（如 "1.", "2." 等）
                    if re.match(r'^\d+\.$', candidate_word):
                        logger.debug(f"跳过编号: '{candidate_word}'")
                        continue

                    # 跳过空词和标点符号
                    if len(candidate_word) < 2 or re.match(r'^[^\w]+$', candidate_word):
                        logger.debug(f"跳过空词或标点: '{candidate_word}'")
                        continue

                    # 检查是否是结论词
                    conclusion = self._extract_conclusion_from_word(candidate_word)
                    if conclusion:
                        logger.debug(f"在位置 {j} 找到结论 '{conclusion}': '{candidate_word}'")
                        return conclusion
                    else:
                        logger.debug(f"位置 {j} 的词 '{candidate_word}' 不是结论关键词")

        logger.warning(f"未找到测试方法 '{test_method}' 的明确结论，默认为Fail")
        return 'Fail'

    def _extract_conclusion_from_word(self, word: str) -> Optional[str]:
        """从词中提取结论"""
        pass_keywords = ['pass', 'compliant', '符合', '合格', '通过', 'ok', 'yes']
        fail_keywords = ['fail', 'non-compliant', '不符合', '不合格', '不通过', 'failed', 'no', 'ng']

        word_clean = re.sub(r'[^\w]', '', word.lower())

        # 优先检查Fail关键词
        for keyword in fail_keywords:
            if keyword in word_clean:
                return 'Fail'

        # 再检查Pass关键词
        for keyword in pass_keywords:
            if keyword in word_clean:
                return 'Pass'

        return None

  
    def generate_new_filename(self, sampling_id: str, report_no: str, final_conclusion: str) -> str:
        """生成新文件名：Sampling ID-Report No-最终结论.pdf"""
        if not sampling_id:
            sampling_id = "UNKNOWN_SAMPLING_ID"
        if not report_no:
            report_no = "UNKNOWN_REPORT_NO"

        new_filename = f"{sampling_id}-{report_no}-{final_conclusion}.pdf"
        logger.info(f"生成新文件名: {new_filename}")
        return new_filename

  