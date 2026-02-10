"""Excel 내보내기 서비스

위치: app/api/services/export_service.py
- NL2SQL 조회 결과를 보고서 형태의 Excel(.xlsx)로 생성
- openpyxl 사용: 서식, 차트, 자동 열너비 지원
"""
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 스타일 상수
HEADER_FILL = PatternFill(start_color="2B579A", end_color="2B579A", fill_type="solid")
HEADER_FONT = Font(name="맑은 고딕", bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(name="맑은 고딕", bold=True, size=14, color="2B579A")
SUBTITLE_FONT = Font(name="맑은 고딕", size=10, color="666666", italic=True)
DATA_FONT = Font(name="맑은 고딕", size=10)
SUMMARY_FONT = Font(name="맑은 고딕", size=9, color="888888")
THIN_BORDER = Border(
    left=Side(style="thin", color="D0D0D0"),
    right=Side(style="thin", color="D0D0D0"),
    top=Side(style="thin", color="D0D0D0"),
    bottom=Side(style="thin", color="D0D0D0"),
)
ALT_ROW_FILL = PatternFill(start_color="F5F7FA", end_color="F5F7FA", fill_type="solid")


class ExportService:
    """Excel 내보내기 서비스"""

    def generate_excel(
        self,
        columns: List[str],
        rows: List[Dict[str, Any]],
        question: str = "",
        sql: str = "",
        answer: str = "",
        execution_time_ms: int = 0,
    ) -> BytesIO:
        """보고서 형태의 Excel 파일 생성"""
        wb = Workbook()
        ws = wb.active
        ws.title = "조회결과"

        col_count = max(len(columns), 1)
        current_row = 1

        # 1) 제목: 질문
        if question:
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=col_count)
            cell = ws.cell(row=current_row, column=1, value=question)
            cell.font = TITLE_FONT
            cell.alignment = Alignment(vertical="center")
            current_row += 1

        # 2) 부제: 생성 일시
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=col_count)
        cell = ws.cell(row=current_row, column=1, value=f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        cell.font = SUBTITLE_FONT
        current_row += 2  # 빈 행

        # 3) 데이터 테이블 - 헤더
        header_row = current_row
        for col_idx, col_name in enumerate(columns, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=col_name)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="center", vertical="center")
        current_row += 1

        # 4) 데이터 행
        numeric_columns = set()
        for row_idx, row_data in enumerate(rows):
            for col_idx, col_name in enumerate(columns, 1):
                value = row_data.get(col_name, "")
                cell = ws.cell(row=current_row, column=col_idx, value=value)
                cell.font = DATA_FONT
                cell.border = THIN_BORDER
                # 숫자 감지
                if isinstance(value, (int, float)):
                    numeric_columns.add(col_idx)
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '#,##0' if isinstance(value, int) else '#,##0.00'
                else:
                    cell.alignment = Alignment(horizontal="left")
                # 줄무늬 행
                if row_idx % 2 == 1:
                    cell.fill = ALT_ROW_FILL
            current_row += 1

        data_end_row = current_row - 1

        # 5) 자동 열너비
        for col_idx, col_name in enumerate(columns, 1):
            max_len = len(str(col_name))
            for row_data in rows[:100]:
                val = row_data.get(col_name, "")
                max_len = max(max_len, len(str(val)))
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 4, 40)

        current_row += 1  # 빈 행

        # 6) 차트 생성 (숫자 컬럼이 있고 데이터가 2행 이상일 때)
        if numeric_columns and len(rows) >= 2 and len(rows) <= 50:
            # 첫 번째 비숫자 컬럼을 카테고리(라벨)로, 첫 번째 숫자 컬럼을 데이터로 사용
            label_col = None
            for ci, cn in enumerate(columns, 1):
                if ci not in numeric_columns:
                    label_col = ci
                    break

            for num_col in sorted(numeric_columns):
                chart = BarChart()
                chart.type = "col"
                chart.style = 10
                chart.title = columns[num_col - 1]
                chart.y_axis.title = columns[num_col - 1]
                chart.width = 18
                chart.height = 12

                data_ref = Reference(ws, min_col=num_col, min_row=header_row, max_row=data_end_row)
                chart.add_data(data_ref, titles_from_data=True)

                if label_col:
                    cats = Reference(ws, min_col=label_col, min_row=header_row + 1, max_row=data_end_row)
                    chart.set_categories(cats)
                    chart.x_axis.title = columns[label_col - 1]

                ws.add_chart(chart, f"A{current_row}")
                current_row += 16  # 차트 높이만큼 이동
                break  # 첫 번째 숫자 컬럼만 차트 생성

        # 7) 하단 요약
        summary_lines = [f"조회 건수: {len(rows)}건"]
        if execution_time_ms:
            summary_lines.append(f"실행 시간: {execution_time_ms}ms")
        if sql:
            summary_lines.append(f"SQL: {sql[:200]}")

        for line in summary_lines:
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=col_count)
            cell = ws.cell(row=current_row, column=1, value=line)
            cell.font = SUMMARY_FONT
            current_row += 1

        # 파일 저장
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        logger.info(f"Excel 파일 생성 완료 | rows={len(rows)}, columns={len(columns)}")
        return output


export_service = ExportService()
