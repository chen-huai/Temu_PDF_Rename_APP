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

    def __init__(self, info_fields=None, enable_test_analysis=True):
        """
        初始化PDF处理器

        Args:
            info_fields (str, optional): 从GUI获取的信息字段配置，如"Sampling ID;Report No;结论"
            enable_test_analysis (bool): 是否启用测试方法分析，默认为True
        """
        self.test_methods = []
        self.info_fields = info_fields or "Sampling ID;Report No"  # 默认字段
        self.enable_test_analysis = enable_test_analysis

        # 新增命名规则相关属性
        self.original_naming_rule = "Sampling ID-Report No-结论"
        self.new_naming_rule = "Report No-结论-Sampling ID"

        # 预编译常用正则表达式模式（性能优化）
        self._report_no_patterns = [
            re.compile(r'Report\s*No\.?\s*:\s*(.+)', re.IGNORECASE),
            re.compile(r'Report\s*Number\s*:\s*(.+)', re.IGNORECASE)
        ]
        self._field_pattern_cache = {}  # 缓存字段模式
        self._valid_config_pattern = re.compile(r'^[a-zA-Z0-9\s\u4e00-\u9fa5:;_\-\.]+$')

        # 解析信息字段列表
        self.info_field_list = self.parse_field_config(self.info_fields)
        logger.info(f"PDFProcessor初始化完成，信息字段: {self.info_field_list}, 测试分析: {enable_test_analysis}")

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除或替换Windows文件系统中的非法字符

        Args:
            filename (str): 原始文件名

        Returns:
            str: 清理后的合法文件名
        """
        # Windows文件名非法字符: < > : " | ? * \
        illegal_chars = r'[<>:"|?*\\]'

        # 将非法字符替换为下划线
        sanitized = re.sub(illegal_chars, '_', filename)

        # 只移除多余的连续下划线，保留连字符（用于字段分隔）
        sanitized = re.sub(r'_{2,}', '_', sanitized)
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # 移除开头和结尾的空格、点、下划线
        sanitized = sanitized.strip(' ._-')

        logger.debug(f"文件名清理: '{filename}' -> '{sanitized}'")
        return sanitized

    def parse_filename_backup(self, filename: str) -> Dict[str, str]:
        """
        从文件名解析字段作为备用方案

        Args:
            filename (str): 原始文件名（不含扩展名）

        Returns:
            Dict[str, str]: 解析出的字段值
        """
        logger.debug(f"尝试从文件名解析字段: {filename}")

        # 移除扩展名
        name_without_ext = os.path.splitext(filename)[0]

        # 尝试匹配常见格式: 66.441.25.17954.01-Pass-100534192
        # 使用连字符分割
        parts = name_without_ext.split('-')

        field_values = {}

        try:
            if len(parts) >= 3:
                # 格式可能是: Report No-结论-Sampling ID
                potential_report_no = parts[0].strip()
                potential_conclusion = parts[1].strip()
                potential_sampling_id = parts[2].strip()

                # 验证字段格式
                if '.' in potential_report_no and potential_report_no.replace('.', '').replace('-', '').isdigit():
                    field_values['Report No'] = potential_report_no
                    logger.debug(f"从文件名解析出Report No: {potential_report_no}")

                if potential_sampling_id.isdigit() or (potential_sampling_id.replace('.', '').replace('-', '').isdigit() and len(potential_sampling_id) > 6):
                    field_values['Sampling ID'] = potential_sampling_id
                    logger.debug(f"从文件名解析出Sampling ID: {potential_sampling_id}")

                if potential_conclusion in ['Pass', 'Fail', 'pass', 'fail', '符合', '不符合', '合格', '不合格']:
                    field_values['结论'] = potential_conclusion
                    logger.debug(f"从文件名解析出结论: {potential_conclusion}")

        except Exception as e:
            logger.warning(f"从文件名解析字段失败: {e}")

        return field_values

    def set_test_methods(self, methods_str: str):
        """设置测试方法列表"""
        self.test_methods = [method.strip() for method in methods_str.split(';') if method.strip()]
        logger.info(f"设置测试方法: {self.test_methods}")

    def set_info_fields(self, info_fields_str: str):
        """设置信息字段列表"""
        self.info_fields = info_fields_str or "Sampling ID;Report No"
        self.info_field_list = self.parse_field_config(self.info_fields)
        logger.info(f"设置信息字段: {self.info_field_list}")

    def parse_field_config(self, config_str: str) -> List[str]:
        """
        解析字段配置字符串，支持带冒号和不带冒号的格式

        Args:
            config_str (str): 配置字符串，如"Sampling ID:;Report No:"或"Sampling ID;Report No;"

        Returns:
            List[str]: 标准化后的字段名列表
        """
        if not config_str:
            return ["Sampling ID", "Report No"]

        # 验证配置格式
        validation_result = self.validate_field_config(config_str)
        if not validation_result['is_valid']:
            logger.warning(f"字段配置格式有误: {validation_result['error']}")
            # 使用默认配置
            return ["Sampling ID", "Report No"]

        fields = []
        for field in config_str.split(';'):
            field = field.strip()
            if not field:
                continue

            # 移除末尾的冒号，统一标准化字段名
            if field.endswith(':'):
                field = field[:-1].strip()

            if field:
                fields.append(field)

        logger.debug(f"解析字段配置: '{config_str}' -> {fields}")
        return fields if fields else ["Sampling ID", "Report No"]

    def validate_field_config(self, config_str: str) -> Dict[str, any]:
        """
        验证字段配置字符串的格式（优化版本）

        Args:
            config_str (str): 配置字符串

        Returns:
            Dict[str, any]: 验证结果，包含is_valid和error信息
        """
        if not config_str or not config_str.strip():
            return {'is_valid': True, 'error': None}

        # 使用预编译的正则表达式进行字符验证
        if not self._valid_config_pattern.match(config_str):
            return {
                'is_valid': False,
                'error': "配置字符串包含无效字符，只允许字母、数字、中文、空格、冒号、分号、下划线、横线和点号"
            }

        # 合并字符和长度验证，提高效率
        fields = [f.strip().rstrip(':') for f in config_str.split(';') if f.strip()]

        # 批量验证字段长度
        invalid_fields = [f for f in fields if len(f) > 50 or len(f) < 2]
        if invalid_fields:
            field_info = ', '.join([f"'{f}'(长度:{len(f)})" for f in invalid_fields[:2]])  # 只显示前两个错误字段
            return {
                'is_valid': False,
                'error': f"字段长度不符合要求(2-50字符): {field_info}..."
            }

        return {'is_valid': True, 'error': None}

    def update_config(self, info_fields: str, original_naming_rule: str,
                    new_naming_rule: str, test_methods_str: str):
        """
        更新处理器配置（优化版本：提供更详细的错误信息和建议）

        Args:
            info_fields (str): 信息字段配置
            original_naming_rule (str): 原命名规则
            new_naming_rule (str): 新命名规则
            test_methods_str (str): 测试方法字符串

        Returns:
            Dict[str, any]: 更新结果，包含success、errors和warnings信息
        """
        result = {'success': True, 'errors': [], 'warnings': []}

        # 验证并更新信息字段
        if not info_fields or not info_fields.strip():
            self.set_info_fields("")  # 使用默认值
            result['warnings'].append("信息字段为空，已使用默认配置 'Sampling ID;Report No'")
            logger.info("信息字段为空，使用默认配置")
        else:
            validation_result = self.validate_field_config(info_fields)
            if validation_result['is_valid']:
                self.set_info_fields(info_fields)
                logger.info(f"信息字段更新成功: {self.info_field_list}")
            else:
                suggestion = self._get_config_suggestion(validation_result['error'])
                result['success'] = False
                result['errors'].append(f"信息字段配置错误: {validation_result['error']}\n建议：{suggestion}")
                logger.error(f"信息字段配置错误: {validation_result['error']}")

        # 更新命名规则（增强验证）
        if original_naming_rule and new_naming_rule:
            self.original_naming_rule = original_naming_rule
            self.new_naming_rule = new_naming_rule
            logger.info(f"命名规则更新成功: 原规则={original_naming_rule}, 新规则={new_naming_rule}")
        else:
            result['success'] = False
            result['errors'].append("命名规则不能为空，请提供原命名规则和新命名规则")

        # 更新测试方法
        if test_methods_str and test_methods_str.strip():
            self.set_test_methods(test_methods_str)
            logger.info(f"测试方法更新成功: {self.test_methods}")
        else:
            result['warnings'].append("测试方法为空，将禁用测试分析功能")
            logger.warning("测试方法为空，将禁用测试分析功能")

        # 记录最终状态
        if result['success']:
            logger.info("配置更新完成")
        else:
            logger.error(f"配置更新失败: {result['errors']}")

        return result

    def _get_config_suggestion(self, error_msg: str) -> str:
        """
        根据错误信息提供配置建议

        Args:
            error_msg (str): 错误信息

        Returns:
            str: 配置建议
        """
        if "无效字符" in error_msg:
            return "请使用以下格式：'Sampling ID:;Report No;' 或 'Product Name;Batch No;Expiry Date'"
        elif "字段长度" in error_msg:
            return "字段名长度应在2-50字符之间，例如：'Sampling ID' 或 'Report No'"
        elif "命名规则不能为空" in error_msg:
            return "请提供完整的命名规则，例如：'Sampling ID-Report No-结论'"
        else:
            return "请参考默认配置格式：'Sampling ID;Report No;结论'"

    def extract_pdf_info(self, pdf_path: str) -> Dict[str, any]:
        """
        从PDF中提取信息，支持混合信息提取（PDF+文件名解析）

        Args:
            pdf_path (str): PDF文件路径

        Returns:
            Dict[str, any]: 包含所有提取信息的字典
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(pdf_path):
                return {
                    'extracted_info': {},
                    'test_results': {},
                    'final_conclusion': None,
                    'error': f"文件不存在: {pdf_path}"
                }

            # 初始化结果字典
            result = {
                'extracted_info': {},
                'test_results': {},
                'final_conclusion': None,
                'error': None
            }

            # 第一步：尝试从PDF提取文本内容
            pdf_text = self._extract_pdf_text(pdf_path)

            # 第二步：根据配置的字段进行混合信息提取
            filename = os.path.basename(pdf_path)
            filename_info = self.parse_filename_info(filename)

            logger.info(f"开始混合信息提取，PDF文本长度: {len(pdf_text) if pdf_text else 0}")
            logger.info(f"文件名解析结果: {filename_info}")

            # 对每个配置的字段进行提取
            for field_name in self.info_field_list:
                pdf_value = None
                source = "未知"

                if pdf_text:
                    # 使用通用字段提取方法
                    if field_name == "结论" and self.enable_test_analysis:
                        # 结论字段需要特殊处理，从测试结果获取
                        pass  # 稍后处理
                    else:
                        # 使用动态字段提取方法
                        pdf_value = self._extract_field_by_keyword(pdf_text, field_name)

                # 如果PDF提取失败，尝试从文件名解析
                if pdf_value:
                    source = "PDF内容"
                elif filename_info.get(field_name):
                    pdf_value = filename_info[field_name]
                    source = "文件名解析"
                else:
                    pdf_value = None
                    source = "未找到"

                result['extracted_info'][field_name] = {
                    'value': pdf_value,
                    'source': source
                }

                logger.info(f"字段 '{field_name}': {pdf_value} (来源: {source})")

            # 第三步：处理测试方法分析（如果启用）
            if self.enable_test_analysis and self.test_methods and pdf_text:
                test_results = self._extract_test_results(pdf_text)
                result['test_results'] = test_results

                # 基于测试结果判断最终结论
                final_conclusion = self._determine_final_conclusion_from_tests(test_results)

                # 如果测试方法分析有结论，更新结论字段
                if final_conclusion and final_conclusion not in ['未找到结论', '未找到方法', '未找到结果']:
                    if '结论' in result['extracted_info']:
                        result['extracted_info']['结论'] = {
                            'value': final_conclusion,
                            'source': '测试方法分析'
                        }
                    result['final_conclusion'] = final_conclusion
                    logger.info(f"基于测试方法的最终结论: {final_conclusion}")
            elif '结论' in result['extracted_info']:
                # 如果没有启用测试分析，但有结论字段信息
                conclusion_info = result['extracted_info']['结论']
                if conclusion_info['value']:
                    result['final_conclusion'] = conclusion_info['value']
                    logger.info(f"使用提取的结论: {conclusion_info['value']} (来源: {conclusion_info['source']})")

            logger.info("PDF信息提取完成")
            return result

        except Exception as e:
            error_msg = self._handle_error(e)
            logger.error(f"处理PDF失败: {error_msg}")
            return {
                'extracted_info': {},
                'test_results': {},
                'final_conclusion': None,
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

    def _extract_field_by_keyword(self, text: str, field_name: str) -> Optional[str]:
        """
        通用字段提取方法，根据字段名动态提取PDF内容（优化版本）

        Args:
            text (str): PDF文本内容
            field_name (str): 要提取的字段名，如"Sampling ID"、"Report No"等

        Returns:
            Optional[str]: 提取到的字段值，未找到则返回None
        """
        logger.debug(f"开始提取字段 '{field_name}'")
        lines = text.split('\n')

        # 获取或创建字段模式（使用缓存优化性能）
        patterns = self._get_field_patterns(field_name)

        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 尝试所有模式
            for pattern in patterns:
                if pattern.search(line):
                    logger.debug(f"找到字段 '{field_name}' 在行 {line_num}: '{line}'")

                    # 提取匹配的值
                    match = pattern.search(line)
                    if match:
                        field_value = match.group(1).strip()

                        # 根据字段名进行特定的清理
                        field_value = self._clean_field_value(field_value, field_name)

                        if field_value:
                            logger.info(f"提取到字段 '{field_name}': '{field_value}'")
                            return field_value

        logger.warning(f"未找到字段 '{field_name}'")
        return None

    def _get_field_patterns(self, field_name: str) -> List:
        """
        获取字段对应的正则表达式模式，使用缓存提高性能

        Args:
            field_name (str): 字段名

        Returns:
            List: 编译后的正则表达式模式列表
        """
        # 检查缓存
        if field_name in self._field_pattern_cache:
            return self._field_pattern_cache[field_name]

        # 处理特殊字段：Report No 的变体
        if field_name.lower() in ["report no", "report number", "report no."]:
            patterns = self._report_no_patterns
        else:
            # 为通用字段创建正则表达式模式
            escaped_field = re.escape(field_name)
            patterns = [
                re.compile(rf'{escaped_field}\s*:\s*(.+)', re.IGNORECASE),  # 带冒号格式
                re.compile(rf'{escaped_field}\s+(.+)', re.IGNORECASE),      # 空格分隔格式
            ]

        # 缓存模式
        self._field_pattern_cache[field_name] = patterns
        return patterns

    def _clean_field_value(self, value: str, field_name: str) -> str:
        """
        根据字段类型清理提取的值（优化版本）

        Args:
            value (str): 原始提取值
            field_name (str): 字段名

        Returns:
            str: 清理后的字段值
        """
        if not value:
            return ""

        # 定义清理规则映射（优化版本：更统一的字段值清理逻辑）
        field_lower = field_name.lower()

        if 'id' in field_lower or 'no' in field_lower:
            # ID类字段：去除所有空格，只保留字母数字和常用符号
            cleaned = re.sub(r'[^\w\.\-_/]', '', re.sub(r'\s+', '', value))
        else:
            # 其他字段：标准化空格
            cleaned = re.sub(r'\s+', ' ', value.strip())

        return cleaned

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

        method_found = False  # 标记是否找到了测试方法

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 查找包含测试方法的行
            if re.search(re.escape(test_method), line, re.IGNORECASE):
                logger.debug(f"找到测试方法 '{test_method}' 在行 {i}: '{line}'")
                method_found = True

                # 从当前行开始，向下查找包含Pass/Fail的行
                for j in range(i + 1, min(i + 15, len(lines))):  # 向下查找15行
                    search_line = lines[j].strip()
                    if not search_line:
                        continue

                    logger.debug(f"检查行 {j}: '{search_line}'")

                    # 检查该行是否包含Pass/Fail关键词
                    conclusion = self._extract_conclusion_from_line(search_line)
                    if conclusion in ['Pass', 'Fail']:  # 只接受Pass或Fail
                        logger.info(f"测试方法 '{test_method}' 找到结论: {conclusion}")
                        return conclusion
                    else:
                        # 如果该行不包含结论，但有大量描述性文本，可能不是我们想要的结论
                        if len(search_line) > 50 and not any(keyword in search_line.lower()
                            for keyword in ['pass', 'fail', 'compliant', 'non-compliant', '符合', '不合格']):
                            logger.debug(f"行 {j} 包含描述性文本，跳过: '{search_line[:50]}...'")

        # 根据是否找到测试方法返回不同的结果
        if not method_found:
            logger.warning(f"未找到测试方法 '{test_method}'")
            return '未找到方法'
        else:
            logger.warning(f"找到测试方法 '{test_method}' 但未找到有效结论(Pass/Fail)")
            return '未找到结论'

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

    def _determine_final_conclusion_from_tests(self, test_results: Dict[str, str]) -> Optional[str]:
        """根据测试结果确定最终结论"""
        if not test_results:
            return None

        logger.info(f"分析测试结果: {test_results}")

        # 过滤掉未找到方法的测试结果
        found_methods_results = {method: result for method, result in test_results.items()
                                if result != '未找到方法'}

        if not found_methods_results:
            logger.warning("所有测试方法都未找到")
            return None

        # 检查是否有未找到结论
        has_no_conclusion = any(result == '未找到结论' for result in found_methods_results.values())
        # 检查是否有Fail结果
        has_fail = any(result == 'Fail' for result in found_methods_results.values())
        # 检查是否所有结果都是Pass
        all_pass = all(result == 'Pass' for result in found_methods_results.values())

        if has_no_conclusion:
            logger.info("发现测试方法结果为未找到结论")
            return '未找到结论'
        elif has_fail:
            logger.info("发现测试方法结果为Fail，最终结论为Fail")
            return 'Fail'
        elif all_pass:
            logger.info("所有找到的测试方法结果都为Pass，最终结论为Pass")
            return 'Pass'
        else:
            logger.warning("测试结果异常")
            return '未找到结论'

    def parse_filename_info(self, filename: str, rule: str = None) -> Dict[str, str]:
        """
        从文件名中解析信息

        Args:
            filename (str): 文件名（不含路径和扩展名）
            rule (str, optional): 命名规则，如"Sampling ID-Report No-结论"

        Returns:
            Dict[str, str]: 解析出的字段信息
        """
        logger.info(f"开始解析文件名: {filename}, 规则: {rule}")

        # 移除文件扩展名
        if '.' in filename:
            filename = filename[:filename.rfind('.')]

        # 如果没有提供规则，使用默认字段列表
        if not rule:
            rule = "-".join(self.info_field_list)

        # 按"-"分隔符分割规则
        rule_fields = [field.strip() for field in rule.split('-') if field.strip()]

        # 按"-"分隔符分割文件名
        filename_parts = [part.strip() for part in filename.split('-') if part.strip()]

        logger.info(f"规则字段: {rule_fields}")
        logger.info(f"文件名分割结果: {filename_parts}")

        result = {}

        # 根据规则字段和文件名部分进行映射
        for i, field_name in enumerate(rule_fields):
            if i < len(filename_parts):
                result[field_name] = filename_parts[i]
                logger.debug(f"字段映射: {field_name} = {filename_parts[i]}")
            else:
                result[field_name] = "无"
                logger.warning(f"字段 {field_name} 在文件名中未找到对应部分")

        # 特殊处理：如果规则包含结论但未解析到，尝试从文件名中查找结论关键词
        if '结论' in rule_fields and (not result.get('结论') or result['结论'] == '无'):
            conclusion = self._extract_conclusion_from_filename(filename)
            if conclusion:
                result['结论'] = conclusion
                logger.info(f"从文件名中提取到结论: {conclusion}")

        logger.info(f"文件名解析完成: {result}")
        return result

    def _extract_conclusion_from_filename(self, filename: str) -> Optional[str]:
        """从文件名中提取结论"""
        filename_lower = filename.lower()

        # 检查Fail关键词
        fail_keywords = ['fail', 'ng', '不合格', '不符合', '不通过', 'fail']
        for keyword in fail_keywords:
            if keyword in filename_lower:
                return 'Fail'

        # 检查Pass关键词
        pass_keywords = ['pass', 'ok', '合格', '符合', '通过', 'compliant']
        for keyword in pass_keywords:
            if keyword in filename_lower:
                return 'Pass'

        return None

    def rearrange_fields_by_rule(self, rule: str, field_values: Dict[str, str], extension: str = ".pdf") -> str:
        """
        根据规则重排字段值，生成文件名

        Args:
            rule (str): 字段排列规则，如"Report No-结论-Sampling ID"
            field_values (Dict[str, str]): 字段值映射
            extension (str): 文件扩展名，默认为".pdf"

        Returns:
            str: 重排后的文件名（包含扩展名）
        """
        try:
            logger.info(f"=== rearrange_fields_by_rule 调试开始 ===")
            logger.info(f"接收到的规则: '{rule}'")
            logger.info(f"接收到的扩展名: '{extension}'")
            logger.info(f"接收到的field_values: {field_values}")
            logger.info(f"field_values字典长度: {len(field_values)}")
            logger.info(f"field_values所有键: {list(field_values.keys())}")

            # 详细分析每个字段值的质量
            for key, value in field_values.items():
                if value and value != "无":
                    logger.info(f"✓ 有效字段 '{key}': '{value}' (长度: {len(value)})")
                else:
                    logger.warning(f"✗ 无效字段 '{key}': '{value}'")

            # 检查关键字段是否存在
            for key in ['Sampling ID', 'Report No', '最终结论', '结论']:
                if key in field_values and field_values[key] and field_values[key] != "无":
                    logger.info(f"✓ rearrange_fields找到关键字段 '{key}': '{field_values[key]}'")
                else:
                    logger.warning(f"✗ rearrange_fields未找到有效字段 '{key}'")
                    # 检查相似字段名
                    similar_keys = [k for k in field_values.keys() if key.lower() in k.lower() or k.lower() in key.lower()]
                    if similar_keys:
                        logger.warning(f"  找到相似字段名: {similar_keys}")
                        for similar_key in similar_keys:
                            logger.warning(f"    {similar_key}: '{field_values[similar_key]}'")

            logger.debug(f"字段重排开始: 规则='{rule}', 扩展名='{extension}'")
            logger.debug(f"可用字段值: {field_values}")

            if not rule:
                logger.warning("规则为空，使用默认文件名")
                return "RENAMED_FILE"

            # 处理单字段情况（没有"-"分隔符）
            if '-' not in rule:
                single_field = rule.strip()
                logger.debug(f"检测到单字段规则: '{single_field}'")
                result = self._validate_field_value(single_field, field_values)
                if result.startswith("UNKNOWN_"):
                    logger.warning(f"单字段 '{single_field}' 值为空，使用占位符: {result}")

                # 确保添加扩展名
                if extension and not result.lower().endswith(extension.lower()):
                    result += extension

                logger.info(f"单字段重排结果: {result}")
                return result

            # 按"-"分隔符分割规则
            rule_fields = [field.strip() for field in rule.split('-') if field.strip()]

            logger.debug(f"解析后的规则字段列表: {rule_fields}")

            # 根据规则重排字段
            filename_parts = []
            for i, field_name in enumerate(rule_fields):
                logger.debug(f"处理字段 {i+1}/{len(rule_fields)}: '{field_name}'")

                value = self._validate_field_value(field_name, field_values)
                filename_parts.append(value)

                if value.startswith("UNKNOWN_"):
                    logger.warning(f"字段 '{field_name}' 值为空，使用占位符: {value}")
                    # 尝试查找相似字段名
                    available_fields = list(field_values.keys())
                    similar_fields = [f for f in available_fields if field_name.lower() in f.lower() or f.lower() in field_name.lower()]
                    if similar_fields:
                        logger.warning(f"发现相似字段名: {similar_fields}")
                else:
                    logger.debug(f"字段 '{field_name}' 成功添加到文件名: '{value}'")

            # 用"-"连接各部分
            new_filename = "-".join(filename_parts)

            # 清理文件名，移除Windows非法字符
            new_filename = self.sanitize_filename(new_filename)

            # 确保添加扩展名
            if extension and not new_filename.lower().endswith(extension.lower()):
                new_filename += extension

            logger.info(f"字段重排完成: '{rule}' -> '{new_filename}'")
            return new_filename

        except Exception as e:
            logger.error(f"重排字段失败: {e}")
            logger.error(f"错误详情: 规则='{rule}', 字段值={field_values}")
            return "ERROR_RENAME"

    def _validate_field_value(self, field_name: str, field_values: Dict[str, str]) -> str:
        """
        验证字段值并返回有效值或占位符

        Args:
            field_name (str): 字段名称
            field_values (Dict[str, str]): 字段值字典

        Returns:
            str: 有效字段值或占位符
        """
        logger.debug(f"验证字段: '{field_name}', 可用字段: {list(field_values.keys())}")

        # 字段名映射表 - 处理常见的字段名变体
        field_mapping = {
            # 报告编号变体
            'Test Report No': 'Report No',
            'Report No': 'Report No',
            'Report Number': 'Report No',
            '报告编号': 'Report No',

            # SKU ID变体
            'SKU ID': 'Sampling ID',
            'SKU': 'Sampling ID',
            'Sku': 'Sampling ID',
            'sku': 'Sampling ID',
            'SKU No': 'Sampling ID',

            # Goods ID变体
            'Goods ID': 'Report No',
            'Goods No': 'Report No',
            'Product ID': 'Report No',
            'Product No': 'Report No',

            # 结论变体
            'Overall Conclusion': '结论',
            'Conclusion': '结论',
            'Final Conclusion': '结论',
            '最终结论': '结论',
            'Test Result': '结论',
            'Result': '结论',
        }

        # 1. 直接查找
        value = field_values.get(field_name)
        if value and value != "无":
            logger.debug(f"直接匹配成功: '{field_name}' = '{value}'")
            return value

        # 2. 使用字段映射表
        mapped_field = field_mapping.get(field_name)
        if mapped_field:
            value = field_values.get(mapped_field)
            if value and value != "无":
                logger.debug(f"映射匹配成功: '{field_name}' -> '{mapped_field}' = '{value}'")
                return value

        # 3. 尝试大小写不敏感匹配
        for key, val in field_values.items():
            if key.lower() == field_name.lower() and val and val != "无":
                logger.debug(f"大小写不敏感匹配: '{field_name}' -> '{key}' = '{val}'")
                return val

        # 4. 尝试映射表的大小写不敏感匹配
        for key, val in field_values.items():
            for original, mapped in field_mapping.items():
                if (key.lower() == mapped.lower() and
                    original.lower() == field_name.lower() and
                    val and val != "无"):
                    logger.debug(f"映射大小写匹配: '{field_name}' -> '{key}' = '{val}'")
                    return val

        # 5. 尝试包含匹配
        for key, val in field_values.items():
            if field_name.lower() in key.lower() or key.lower() in field_name.lower():
                if val and val != "无":
                    logger.debug(f"包含匹配成功: '{field_name}' -> '{key}' = '{val}'")
                    return val

        # 6. 尝试通过映射表的包含匹配
        for mapped_key, target_key in field_mapping.items():
            if field_name.lower() == mapped_key.lower():
                for key, val in field_values.items():
                    if (target_key.lower() in key.lower() or key.lower() in target_key.lower()) and val and val != "无":
                        logger.debug(f"映射包含匹配: '{field_name}' -> '{target_key}' -> '{key}' = '{val}'")
                        return val

        logger.warning(f"字段 '{field_name}' 匹配失败，使用占位符")

        # 预计算占位符字段名，避免重复字符串操作
        placeholder_name = field_name.replace(' ', '_').upper()
        return f"UNKNOWN_{placeholder_name}"

    def generate_new_filename(self, sampling_id: str, report_no: str, final_conclusion: str) -> str:
        """生成新文件名：Sampling ID-Report No-最终结论.pdf"""
        if not sampling_id:
            sampling_id = "UNKNOWN_SAMPLING_ID"
        if not report_no:
            report_no = "UNKNOWN_REPORT_NO"

        new_filename = f"{sampling_id}-{report_no}-{final_conclusion}.pdf"
        logger.info(f"生成新文件名: {new_filename}")
        return new_filename

  