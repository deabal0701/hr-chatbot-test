"""MUREUM 소개서 - 1장짜리 PPT (텍스트 중심, 단색 배경)"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# 색상 (단색 기조)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG_DARK = RGBColor(0x1E, 0x29, 0x3B)       # 진한 남색
ACCENT = RGBColor(0x3B, 0x9E, 0xD6)         # 포인트 블루
TEXT_PRIMARY = RGBColor(0x22, 0x22, 0x22)
TEXT_SECONDARY = RGBColor(0x4A, 0x4A, 0x4A)
TEXT_MUTED = RGBColor(0x77, 0x77, 0x77)
HIGHLIGHT_BG = RGBColor(0xEE, 0xF5, 0xFB)   # 연한 파란 박스
QUOTE_BG = RGBColor(0xF7, 0xF8, 0xFA)       # 인용 배경
TABLE_HEADER = RGBColor(0x2C, 0x3E, 0x6B)
TABLE_ALT = RGBColor(0xF4, 0xF7, 0xFB)
BORDER_LIGHT = RGBColor(0xD8, 0xDE, 0xE8)
BULLET_ORANGE = RGBColor(0xE8, 0x6B, 0x30)


def set_cell_border(cell, color=BORDER_LIGHT):
    """셀 테두리 설정"""
    from pptx.oxml.ns import qn
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for edge in ['a:lnL', 'a:lnR', 'a:lnT', 'a:lnB']:
        ln = tcPr.find(qn(edge))
        if ln is not None:
            tcPr.remove(ln)


def add_textbox(slide, left, top, width, height, text, font_size=10,
                color=TEXT_PRIMARY, bold=False, italic=False, align=PP_ALIGN.LEFT,
                line_spacing=None):
    """텍스트 박스 추가"""
    shape = slide.shapes.add_textbox(left, top, width, height)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(0)
    tf.margin_right = Pt(0)
    tf.margin_top = Pt(0)
    tf.margin_bottom = Pt(0)
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.italic = italic
    p.alignment = align
    if line_spacing:
        p.line_spacing = Pt(line_spacing)
    return shape


def add_rich_textbox(slide, left, top, width, height, runs_list, line_spacing=None, align=PP_ALIGN.LEFT):
    """여러 스타일의 run으로 구성된 텍스트박스"""
    shape = slide.shapes.add_textbox(left, top, width, height)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(0)
    tf.margin_right = Pt(0)
    tf.margin_top = Pt(0)
    tf.margin_bottom = Pt(0)

    for p_idx, para_runs in enumerate(runs_list):
        if p_idx > 0:
            p = tf.add_paragraph()
        else:
            p = tf.paragraphs[0]
        p.alignment = align
        if line_spacing:
            p.line_spacing = Pt(line_spacing)

        for run_data in para_runs:
            run = p.add_run()
            run.text = run_data.get("text", "")
            run.font.size = Pt(run_data.get("size", 10))
            run.font.color.rgb = run_data.get("color", TEXT_PRIMARY)
            run.font.bold = run_data.get("bold", False)
            run.font.italic = run_data.get("italic", False)

    return shape


def add_rounded_box(slide, left, top, width, height, fill_color, text="", font_size=10,
                    font_color=WHITE, bold=True):
    """둥근 박스"""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    shape.adjustments[0] = 0.15
    if text:
        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Pt(10)
        tf.margin_right = Pt(10)
        tf.margin_top = Pt(4)
        tf.margin_bottom = Pt(4)
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_size)
        p.font.color.rgb = font_color
        p.font.bold = bold
        p.alignment = PP_ALIGN.CENTER
    return shape


def create_ppt():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # ─── 배경: 흰색 (기본) ───

    # ─── 상단 헤더 바 ───
    header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Pt(50))
    header.fill.solid()
    header.fill.fore_color.rgb = BG_DARK
    header.line.fill.background()

    # 헤더 제목
    add_rich_textbox(slide, Pt(50), Pt(8), Inches(10), Pt(36), [
        [
            {"text": "01  ", "size": 22, "color": ACCENT, "bold": True},
            {"text": "MUREUM 소개", "size": 22, "color": WHITE, "bold": True},
        ]
    ])

    # ─── 좌측 세로 악센트 라인 ───
    accent_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Pt(42), Pt(62), Pt(4), Pt(420))
    accent_line.fill.solid()
    accent_line.fill.fore_color.rgb = ACCENT
    accent_line.line.fill.background()

    # ═══════════════════════════════════════════════════════
    # 섹션 1: MUREUM이란?
    # ═══════════════════════════════════════════════════════
    y = Pt(65)
    content_left = Pt(60)
    content_width = Inches(12.2)

    # 섹션 제목
    add_textbox(slide, content_left, y, content_width, Pt(22),
                "1. MUREUM이란?", font_size=16, color=BG_DARK, bold=True)
    y += Pt(28)

    # 도입 질문
    add_textbox(slide, content_left, y, content_width, Pt(16),
                "회사에 쌓여 있는 데이터와 문서, 활용하고 싶지만 이런 어려움이 있지 않으셨나요?",
                font_size=10.5, color=TEXT_SECONDARY, line_spacing=16)
    y += Pt(22)

    # 문제점 3가지 - 하이라이트 박스
    problem_box = add_rounded_box(slide, content_left, y, content_width, Pt(56),
                                  HIGHLIGHT_BG, font_color=TEXT_PRIMARY, bold=False)
    problem_box.line.color.rgb = BORDER_LIGHT
    problem_box.line.width = Pt(0.5)

    add_rich_textbox(slide, content_left + Pt(14), y + Pt(6), content_width - Pt(28), Pt(48), [
        [{"text": "●  ", "size": 9, "color": BULLET_ORANGE, "bold": True},
         {"text": '"데이터를 보려면 IT팀에 요청해야 해서 며칠씩 걸린다"', "size": 10, "color": TEXT_SECONDARY}],
        [{"text": "●  ", "size": 9, "color": BULLET_ORANGE, "bold": True},
         {"text": '"BI 도구는 너무 복잡해서 교육 없이는 사용이 어렵다"', "size": 10, "color": TEXT_SECONDARY}],
        [{"text": "●  ", "size": 9, "color": BULLET_ORANGE, "bold": True},
         {"text": '"사내 매뉴얼이 어디 있는지 찾기가 힘들다"', "size": 10, "color": TEXT_SECONDARY}],
    ], line_spacing=16)
    y += Pt(64)

    # 해결 설명
    add_rich_textbox(slide, content_left, y, content_width, Pt(38), [
        [{"text": "MUREUM", "size": 11, "color": ACCENT, "bold": True},
         {"text": "은 이런 문제를 해결합니다. 대화창에 ", "size": 10.5, "color": TEXT_PRIMARY},
         {"text": '"이번 달 부서별 매출 현황 보여줘"', "size": 10.5, "color": ACCENT, "bold": True},
         {"text": " 라고 입력하면,", "size": 10.5, "color": TEXT_PRIMARY}],
        [{"text": "AI가 자동으로 데이터를 찾아서 표와 차트로 보여주고, 마음에 드는 결과는 ", "size": 10.5, "color": TEXT_PRIMARY},
         {"text": "나만의 대시보드에 저장", "size": 10.5, "color": ACCENT, "bold": True},
         {"text": "까지 할 수 있습니다.", "size": 10.5, "color": TEXT_PRIMARY}],
    ], line_spacing=17)
    y += Pt(40)

    # 강조 문구
    emphasis_box = add_rounded_box(slide, content_left, y, Inches(7), Pt(24),
                                   BG_DARK)
    tf = emphasis_box.text_frame
    tf.paragraphs[0].text = ""
    tf.margin_left = Pt(14)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = "프로그래밍 지식도, 복잡한 도구 사용법도 필요 없습니다. 그냥 말로 물어보세요."
    run.font.size = Pt(10)
    run.font.color.rgb = WHITE
    run.font.bold = True
    y += Pt(36)

    # ═══════════════════════════════════════════════════════
    # 구분선
    # ═══════════════════════════════════════════════════════
    sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, content_left, y, content_width, Pt(1))
    sep.fill.solid()
    sep.fill.fore_color.rgb = BORDER_LIGHT
    sep.line.fill.background()
    y += Pt(10)

    # ═══════════════════════════════════════════════════════
    # 섹션 2: 핵심 기능 - 데이터베이스에 말로 질문하기
    # ═══════════════════════════════════════════════════════
    add_textbox(slide, content_left, y, content_width, Pt(22),
                "2. 핵심 기능 — 데이터베이스에 말로 질문하기", font_size=16, color=BG_DARK, bold=True)
    y += Pt(26)

    add_rich_textbox(slide, content_left, y, content_width, Pt(18), [
        [{"text": "기존에는 전문가가 프로그래밍 언어로 질의문을 작성해야 했습니다. MUREUM은 ", "size": 10, "color": TEXT_SECONDARY},
         {"text": "일상 언어를 자동으로 데이터 질의문으로 변환", "size": 10, "color": ACCENT, "bold": True},
         {"text": "하여 실시간으로 결과를 보여줍니다.", "size": 10, "color": TEXT_SECONDARY}],
    ], line_spacing=16)
    y += Pt(22)

    # ─── 좌: 대화 예시 / 우: 비교 테이블 ───
    left_w = Inches(6.5)
    right_x = content_left + left_w + Pt(20)
    right_w = Inches(5.4)

    # 대화 예시 제목
    add_textbox(slide, content_left, y, left_w, Pt(16),
                "이렇게 사용합니다:", font_size=10, color=TEXT_PRIMARY, bold=True)

    # 비교 테이블 제목
    add_textbox(slide, right_x, y, right_w, Pt(16),
                "무엇이 다른가요?", font_size=10, color=TEXT_PRIMARY, bold=True)
    y += Pt(20)

    # 대화 예시 박스
    chat_box = add_rounded_box(slide, content_left, y, left_w, Pt(90), QUOTE_BG,
                               font_color=TEXT_PRIMARY, bold=False)
    chat_box.line.color.rgb = BORDER_LIGHT
    chat_box.line.width = Pt(0.5)

    add_rich_textbox(slide, content_left + Pt(14), y + Pt(8), left_w - Pt(28), Pt(80), [
        [{"text": "나: ", "size": 10, "color": ACCENT, "bold": True},
         {"text": '"부서별 인원수 알려줘"', "size": 10, "color": TEXT_PRIMARY}],
        [{"text": "MUREUM: ", "size": 10, "color": BG_DARK, "bold": True},
         {"text": "영업부 25명, 개발팀 32명, 마케팅부 18명... (표 형태로 표시)", "size": 9.5, "color": TEXT_SECONDARY}],
        [{"text": "", "size": 6, "color": TEXT_PRIMARY}],
        [{"text": "나: ", "size": 10, "color": ACCENT, "bold": True},
         {"text": '"그 중에서 개발팀만 연봉 순으로 보여줘"', "size": 10, "color": TEXT_PRIMARY}],
        [{"text": "MUREUM: ", "size": 10, "color": BG_DARK, "bold": True},
         {"text": "(이전 대화를 기억하고) 개발팀 32명의 연봉 순위표를 표시", "size": 9.5, "color": TEXT_SECONDARY}],
    ], line_spacing=15)

    # 비교 테이블
    table_rows = 4
    table_cols = 2
    tbl_shape = slide.shapes.add_table(table_rows, table_cols, right_x, y, right_w, Pt(90))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(2.5)
    tbl.columns[1].width = Inches(2.9)

    data = [
        ["기존 방식", "MUREUM"],
        ["IT팀에 데이터 요청 → 며칠 대기", "직접 질문 → 즉시 결과"],
        ["전문 질의문 작성 필요", "일상 언어로 질문"],
        ["매번 새로 요청", "이전 대화를 기억하는 연속 질문"],
    ]

    for r in range(table_rows):
        for c in range(table_cols):
            cell = tbl.cell(r, c)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.text = data[r][c]
            p.font.size = Pt(9.5)
            cell.margin_left = Pt(8)
            cell.margin_right = Pt(6)
            cell.margin_top = Pt(6)
            cell.margin_bottom = Pt(6)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE

            if r == 0:
                p.font.bold = True
                p.font.color.rgb = WHITE
                cell.fill.solid()
                cell.fill.fore_color.rgb = TABLE_HEADER
            else:
                cell.fill.solid()
                if c == 0:
                    p.font.color.rgb = TEXT_MUTED
                    cell.fill.fore_color.rgb = TABLE_ALT if r % 2 == 1 else WHITE
                else:
                    p.font.color.rgb = ACCENT
                    p.font.bold = True
                    cell.fill.fore_color.rgb = TABLE_ALT if r % 2 == 1 else WHITE

    # ─── 하단 푸터 ───
    footer = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, prs.slide_height - Pt(20), prs.slide_width, Pt(20))
    footer.fill.solid()
    footer.fill.fore_color.rgb = BG_DARK
    footer.line.fill.background()

    add_textbox(slide, Pt(50), prs.slide_height - Pt(18), Inches(5), Pt(16),
                "MUREUM — 물어보세요, 데이터가 답합니다.", font_size=8,
                color=RGBColor(0x88, 0x99, 0xBB), italic=True)

    # 저장
    output = "docs/MUREUM_소개_1page.pptx"
    prs.save(output)
    print(f"PPT 생성 완료: {output}")


if __name__ == "__main__":
    create_ppt()
