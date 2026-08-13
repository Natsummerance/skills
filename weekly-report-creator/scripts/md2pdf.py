#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 转 PDF 工具（基于 ReportLab）
支持中文字体（微软雅黑）、表格、粗体、斜体、列表

依赖：pip install reportlab
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import re
import sys
import io
import argparse

# 设置 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def _first_existing(*paths):
    """返回第一个存在的字体路径（多平台候选）"""
    for p in paths:
        if Path(p).exists():
            return p
    return paths[0]


def register_chinese_fonts():
    """注册中文字体，支持粗体"""
    print('[1/5] 注册中文字体...')

    # 优先使用微软雅黑（Windows）/ Noto Sans CJK（Linux/macOS）
    font_path = _first_existing(
        r'C:\Windows\Fonts\msyh.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/System/Library/Fonts/PingFang.ttc',
    )
    font_bold_path = _first_existing(
        r'C:\Windows\Fonts\msyhbd.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/System/Library/Fonts/PingFang.ttc',
    )

    if Path(font_path).exists():
        try:
            pdfmetrics.registerFont(TTFont('MicrosoftYaHei', font_path, subfontIndex=0))
            print(f'[OK] 注册字体: MicrosoftYaHei')

            if Path(font_bold_path).exists():
                pdfmetrics.registerFont(TTFont('MicrosoftYaHei-Bold', font_bold_path, subfontIndex=0))
                print(f'[OK] 注册字体: MicrosoftYaHei-Bold')

                from reportlab.pdfbase.pdfmetrics import registerFontFamily
                registerFontFamily('MicrosoftYaHei', normal='MicrosoftYaHei', bold='MicrosoftYaHei-Bold')
                print(f'[OK] 注册字体族（含粗体）')

            return 'MicrosoftYaHei'
        except Exception as e:
            print(f'[ERROR] 字体注册失败: {e}')

    # 备用：黑体
    font_path = _first_existing(
        r'C:\Windows\Fonts\simhei.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    )
    if Path(font_path).exists():
        try:
            pdfmetrics.registerFont(TTFont('SimHei', font_path))
            print(f'[OK] 注册字体: SimHei')
            return 'SimHei'
        except Exception as e:
            print(f'[ERROR] 字体注册失败: {e}')

    return None


def parse_markdown_table(lines, start_idx):
    """解析 Markdown 表格"""
    table_lines = []
    idx = start_idx

    while idx < len(lines) and '|' in lines[idx]:
        line = lines[idx].strip()
        if line.startswith('|') and line.endswith('|'):
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            # 跳过分隔行（如 ---:---）
            if not all(re.match(r'^[-:]+$', cell) for cell in cells):
                table_lines.append(cells)
        idx += 1

    return table_lines, idx - start_idx


def create_styles(font_name='SimHei'):
    """创建段落样式"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ChineseBody',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=11,
        leading=16,
        spaceAfter=8,
        alignment=TA_JUSTIFY
    ))

    styles.add(ParagraphStyle(
        name='ChineseTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=20,
        spaceAfter=20,
        spaceBefore=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a1a1a')
    ))

    styles.add(ParagraphStyle(
        name='ChineseHeading2',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=16,
        textColor=colors.HexColor('#2a2a2a')
    ))

    styles.add(ParagraphStyle(
        name='ChineseHeading3',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=14,
        spaceAfter=10,
        spaceBefore=12,
        textColor=colors.HexColor('#3a3a3a')
    ))

    styles.add(ParagraphStyle(
        name='ChineseHeading4',
        parent=styles['Heading4'],
        fontName=font_name,
        fontSize=12,
        spaceAfter=8,
        spaceBefore=10,
        textColor=colors.HexColor('#4a4a4a')
    ))

    styles.add(ParagraphStyle(
        name='ChineseListItem',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=11,
        leading=16,
        leftIndent=20,
        spaceAfter=6,
        bulletFontName=font_name,
        bulletFontSize=11,
        bulletIndent=0
    ))

    styles.add(ParagraphStyle(
        name='ChineseCode',
        parent=styles['BodyText'],
        fontName='Courier',
        fontSize=9,
        leading=13,
        leftIndent=20,
        spaceAfter=4,
        backColor=colors.HexColor('#f4f4f4')
    ))

    return styles


def convert_md_to_reportlab(text, font_name='MicrosoftYaHei'):
    """将 Markdown 格式转换为 ReportLab XML 标签"""
    # **text** → <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # *text* → <i>text</i>
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # `text` → 中文字体 + 小字号（Courier 不含中文字形，会产生黑框）
    text = re.sub(r'`(.+?)`', rf'<font face="{font_name}" size="9">\1</font>', text)
    return text


def md_to_pdf(input_path: str, output_path: str = None) -> str:
    """将 Markdown 文件转换为 PDF"""
    if not Path(input_path).exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    if output_path is None:
        output_path = str(Path(input_path).with_suffix('.pdf'))

    # 注册字体
    font_name = register_chinese_fonts()
    if not font_name:
        raise RuntimeError("无法找到中文字体，请确保系统安装了微软雅黑或黑体字体")

    # 读取 Markdown 文件
    print('[2/5] 读取 Markdown 文件...')
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f'[OK] 读取 {len(lines)} 行')

    # 创建样式
    print('[3/5] 创建样式...')
    styles = create_styles(font_name)

    # 创建 PDF 文档
    print('[4/5] 生成 PDF...')
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=25*mm,
        leftMargin=25*mm,
        topMargin=25*mm,
        bottomMargin=25*mm
    )

    story = []
    idx = 0
    in_code_block = False
    code_lines = []

    while idx < len(lines):
        line = lines[idx].rstrip()

        # 代码块开始/结束
        if line.strip().startswith('```'):
            if in_code_block:
                # 代码块结束，用 Table 包裹（灰底 + 边框）
                code_text = '<br/>'.join(
                    l.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    for l in code_lines
                )
                code_para = Paragraph(
                    code_text,
                    ParagraphStyle(
                        'CodeContent',
                        parent=styles['BodyText'],
                        fontName=font_name,
                        fontSize=9,
                        leading=12,
                        leftIndent=10,
                        rightIndent=10,
                        spaceBefore=6,
                        spaceAfter=6
                    )
                )
                code_table = Table([[code_para]], colWidths=[doc.width - 20])
                code_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                ]))
                story.append(code_table)
                story.append(Spacer(1, 8))
                in_code_block = False
                code_lines = []
            else:
                # 代码块开始
                in_code_block = True
            idx += 1
            continue

        if in_code_block:
            code_lines.append(line)
            idx += 1
            continue

        # 空行
        if not line:
            story.append(Spacer(1, 6))
            idx += 1
            continue

        # 水平线
        if line.strip() == '---':
            story.append(Spacer(1, 12))
            idx += 1
            continue

        # 标题
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            text = convert_md_to_reportlab(text)

            style_map = {
                1: 'ChineseTitle',
                2: 'ChineseHeading2',
                3: 'ChineseHeading3',
                4: 'ChineseHeading4'
            }
            style_name = style_map.get(min(level, 4), 'ChineseHeading4')
            story.append(Paragraph(text, styles[style_name]))
            idx += 1
            continue

        # 表格
        if '|' in line and line.strip().startswith('|'):
            table_lines, rows_consumed = parse_markdown_table(lines, idx)

            if table_lines:
                converted_table = []
                for row in table_lines:
                    converted_row = [convert_md_to_reportlab(cell) for cell in row]
                    converted_table.append(converted_row)

                table = Table(converted_table)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5dade2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fdfefe')),
                    ('FONTNAME', (0, 1), (-1, -1), font_name),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9f9')]),
                ]))
                story.append(table)
                story.append(Spacer(1, 12))

            idx += rows_consumed
            continue

        # 无序列表
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            text = line.strip()[2:].strip()
            text = convert_md_to_reportlab(text)
            story.append(Paragraph(f'- {text}', styles['ChineseListItem']))
            idx += 1
            continue

        # 有序列表
        ol_match = re.match(r'^(\d+)\.\s+(.+)', line.strip())
        if ol_match:
            num = ol_match.group(1)
            text = ol_match.group(2)
            text = convert_md_to_reportlab(text)
            story.append(Paragraph(f'{num}. {text}', styles['ChineseListItem']))
            idx += 1
            continue

        # 普通段落
        text = line.strip()
        if text:
            text = convert_md_to_reportlab(text)
            story.append(Paragraph(text, styles['ChineseBody']))

        idx += 1

    # 构建 PDF
    print('[5/5] 构建 PDF 文件...')
    doc.build(story)

    pdf_path = Path(output_path)
    size = pdf_path.stat().st_size
    print(f'[OK] PDF 生成成功: {output_path}')
    print(f'[SIZE] {size:,} bytes ({size/1024:.1f} KB)')

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Markdown 转 PDF 工具（支持中文）")
    parser.add_argument("input", help="输入的 Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出的 PDF 文件路径（默认与输入同名）")
    args = parser.parse_args()

    try:
        result = md_to_pdf(args.input, args.output)
        print(f'\n[SUCCESS] 转换完成: {result}')
    except Exception as e:
        print(f'\n[FAILED] 转换失败: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
