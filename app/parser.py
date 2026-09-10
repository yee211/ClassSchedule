"""确定性 Excel 课表解析：直接读取工作簿，不依赖 Excel 本体。

AI 解析（app/ai.py）不可用或识别失败时，本模块作为兜底链路保证导入功能不中断。
"""
import re
from pathlib import Path

from .excel import read_sheets

COLORS = ["#5579E8", "#EF5B78", "#F18745", "#8B6AD8", "#42A5C9", "#55AD72", "#D79D39"]


def course_color(weekday: int, start_section: int) -> str:
    """按星期与起始节次确定性取色，保证同一时段每次导入颜色一致。"""
    return COLORS[(weekday + start_section - 2) % len(COLORS)]


def _find_term(*candidates: str) -> str | None:
    """Return the first 'YYYY-YYYY学年第N学期' match among the candidates."""
    for text in candidates:
        match = re.search(r"\d{4}-\d{4}学年第\d学期", text or "")
        if match:
            return match.group(0)
    return None


def _detail_columns(header_row: dict) -> dict:
    """Map logical course fields to sheet column indexes using header text."""
    columns = {}
    for index, value in header_row.items():
        text = str(value or "").strip()
        if not text:
            continue
        if "星期" in text:
            columns.setdefault("weekday", index)
        elif "节次" in text:
            columns.setdefault("section", index)
        elif "课程" in text:
            columns.setdefault("name", index)
        elif "教师" in text or "授课" in text:
            columns.setdefault("teacher", index)
        elif "周次" in text:
            columns.setdefault("weeks", index)
        elif "教室" in text or "地点" in text:
            columns.setdefault("room", index)
    return columns


def _find_detail_header(rows: list[dict]) -> tuple[int | None, dict]:
    """Locate the header row of a course-detail table, skipping title rows that merely mention keywords."""
    for index, row in enumerate(rows):
        joined = "".join(str(value or "") for value in row.values())
        if "星期" in joined and ("节次" in joined or "课程" in joined):
            # 标题行也可能含“星期/节次”字样，需用列映射确认该行确实是表头
            candidate = _detail_columns(row)
            if candidate.get("weekday") and candidate.get("name"):
                return index, candidate
    return None, {}


def _detail_courses(rows: list[dict], header_index: int, columns: dict) -> list[dict]:
    """Turn detail-table rows below the header into course records."""
    courses = []
    for row in rows[header_index + 1:]:
        weekday_text = str(row.get(columns.get("weekday", 1)) or "")
        day_match = re.search(r"星期([一二三四五六日])", weekday_text) or re.search(r"([一二三四五六日])", weekday_text)
        section_match = re.search(r"(\d+)\s*-\s*(\d+)", str(row.get(columns.get("section", 2)) or ""))
        name = str(row.get(columns.get("name", 3)) or "").strip()
        if not day_match or not section_match or not name:
            continue
        weeks = parse_weeks(str(row.get(columns.get("weeks", 5)) or ""))
        weekday = "一二三四五六日".index(day_match.group(1)) + 1
        start, end = int(section_match.group(1)), int(section_match.group(2))
        courses.append({
            "name": name, "teacher": str(row.get(columns.get("teacher", 4)) or "").strip(),
            "room": str(row.get(columns.get("room", 6)) or "").strip(), "weekday": weekday,
            "start_section": start, "end_section": end, "weeks": weeks,
            "color": course_color(weekday, start),
        })
    return courses


def parse_weeks(expression: str) -> list[int]:
    """Parse ranges such as 1-5(单),9-16(双),18."""
    weeks: set[int] = set()
    for part in re.split(r"[,，]", expression.replace("周", "")):
        part = part.strip()
        if not part:
            continue
        parity = None
        parity_match = re.search(r"[（(](单|双)[）)]", part)
        if parity_match:
            parity = parity_match.group(1)
            part = re.sub(r"[（(](单|双)[）)]", "", part)
        numbers = [int(value) for value in re.findall(r"\d+", part)]
        if not numbers:
            continue
        candidates = range(numbers[0], numbers[-1] + 1) if len(numbers) > 1 else numbers
        for week in candidates:
            if parity == "单" and week % 2 == 0:
                continue
            if parity == "双" and week % 2 == 1:
                continue
            weeks.add(week)
    return sorted(weeks)


def merge_section_courses(courses: list[dict]) -> list[dict]:
    """Merge identical courses sitting in consecutive section slots (e.g. 1-2 + 3-4)."""
    merged = []
    for course in sorted(courses, key=lambda item: (item["weekday"], item["start_section"], item["end_section"], item["name"])):
        previous = next((item for item in reversed(merged)
                         if item["end_section"] + 1 == course["start_section"]
                         and all(item[key] == course[key] for key in ("name", "teacher", "room", "weekday", "weeks"))), None)
        if previous:
            previous["end_section"] = course["end_section"]
        else:
            merged.append(course)
    return merged


def parse_excel_schedule(path: Path) -> dict | None:
    """Read the course-detail sheet from Excel/HTML/CSV without requiring Excel itself."""
    sheets = read_sheets(path)
    if not sheets:
        return None

    target_rows = None
    sheet_titles = [sheet.title for sheet in sheets]

    # 优先找明确标明“课程明细”或“明细”的工作表
    for sheet in sheets:
        dict_rows = [cells for _, cells in sheet.rows]
        if any("明细" in str(row.get(1, "")) for row in dict_rows):
            target_rows = dict_rows
            break

    # 若无专门标明“明细”的表，则按表头特征匹配（必须包含“星期”和“课程”列）
    if not target_rows:
        for sheet in sheets:
            dict_rows = [cells for _, cells in sheet.rows]
            header_idx, cols = _find_detail_header(dict_rows)
            if header_idx is not None and cols.get("name"):
                target_rows = dict_rows
                break

    if not target_rows:
        return None

    title = str(target_rows[0].get(1) or "")
    term = _find_term(title, *sheet_titles, path.stem) or "导入课表"
    header_index, columns = _find_detail_header(target_rows)
    if header_index is None or not columns.get("name"):
        header_index, columns = 1, {"weekday": 1, "section": 2, "name": 3, "teacher": 4, "weeks": 5, "room": 6}
    # 明细表里连堂课是拆成多行的（1-2 节与 3-4 节各一行），需合并后才与 AI 结果同形
    courses = merge_section_courses(_detail_courses(target_rows, header_index, columns))
    # 标题只是明细表自己的 sheet 名（如“课程明细速查表(某某)”），模板差异大无法可靠剥出姓名，
    # 因此兜底路径统一用“我的课表”；真实课表名交由 AI 主链路从首页大标题提取
    return {"name": "我的课表", "term": term, "courses": courses} if courses else None


parse_xlsx_schedule = parse_excel_schedule

