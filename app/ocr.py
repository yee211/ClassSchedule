import re
import zipfile
from xml.etree import ElementTree as ET
from pathlib import Path

import fitz


WEEKDAYS = {f"星期{day}": index for index, day in enumerate("一二三四五六日", 1)}


def parse_xlsx_schedule(path: Path) -> dict | None:
    """Read the explicit course-detail sheet without requiring Excel itself."""
    if path.suffix.lower() not in {".xlsx", ".xlsm"}:
        return None
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall(f"{namespace}si"):
                strings.append("".join(node.text or "" for node in item.iter(f"{namespace}t")))

        def cell_value(cell):
            value = cell.find(f"{namespace}v")
            if value is None:
                value = cell.find(f"{namespace}is/{namespace}t")
            if value is None or value.text is None:
                return ""
            return strings[int(value.text)] if cell.get("t") == "s" else value.text

        target_rows = None
        for sheet_name in sorted(name for name in archive.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", name)):
            root = ET.fromstring(archive.read(sheet_name))
            rows = []
            for row in root.findall(f".//{namespace}row"):
                values = {}
                for cell in row.findall(f"{namespace}c"):
                    reference = cell.get("r", "")
                    column = re.match(r"([A-Z]+)", reference)
                    if column:
                        index = 0
                        for letter in column.group(1):
                            index = index * 26 + ord(letter) - 64
                        values[index] = cell_value(cell)
                rows.append(values)
            if any("课程明细" in str(row.get(1, "")) for row in rows):
                target_rows = rows
                break
    if not target_rows:
        return None
    title = str(target_rows[0].get(1) or "导入课表")
    term_match = re.search(r"\d{4}-\d{4}学年第\d学期", title)
    courses = []
    colors = ["#5579E8", "#EF5B78", "#F18745", "#8B6AD8", "#42A5C9", "#55AD72", "#D79D39"]
    for row in target_rows[2:]:
        if not row.get(1) or not row.get(2) or not row.get(3):
            continue
        day_match = re.search(r"星期([一二三四五六日])", str(row.get(1)))
        section_match = re.search(r"(\d+)\s*-\s*(\d+)", str(row.get(2)))
        if not day_match or not section_match:
            continue
        weeks = parse_weeks(str(row.get(5) or ""))
        weekday = "一二三四五六日".index(day_match.group(1)) + 1
        start, end = int(section_match.group(1)), int(section_match.group(2))
        courses.append({
            "name": str(row.get(3)).strip(), "teacher": str(row.get(4) or "").strip(),
            "room": str(row.get(6) or "").strip(), "weekday": weekday,
            "start_section": start, "end_section": end, "weeks": weeks,
            "color": colors[(weekday + start - 2) % len(colors)],
        })
    return {"name": "我的课表", "term": term_match.group(0) if term_match else "导入课表", "courses": courses} if courses else None


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


def _parse_cell_records(text: str, weekday: int, start_section: int, end_section: int) -> list[dict]:
    colors = ["#5579E8", "#EF5B78", "#F18745", "#8B6AD8", "#42A5C9", "#55AD72", "#D79D39"]
    records = []
    for raw_record in re.split(r"(?:考试|考查)", text):
        lines = [line.strip().replace(" ", "") for line in raw_record.splitlines() if line.strip()]
        lines = [line for line in lines if line != "本校区"]
        if not lines:
            continue
        room_index = next((index for index, line in enumerate(lines) if re.match(r"^\d+-", line) or "教室" in line), None)
        if room_index is None:
            continue
        before_room = lines[:room_index]
        week_index = next((index for index, line in enumerate(before_room) if re.search(r"\d", line)), None)
        if week_index is None:
            continue
        name = "".join(before_room[:week_index])
        teacher_and_weeks = "".join(before_room[week_index:])
        match = re.match(r"([^\d]+)(.+?)周$", teacher_and_weeks)
        if not name or not match:
            continue
        records.append({
            "name": name,
            "teacher": match.group(1),
            "room": lines[room_index],
            "weekday": weekday,
            "start_section": start_section,
            "end_section": end_section,
            "weeks": parse_weeks(match.group(2)),
            "color": colors[(weekday + start_section - 2) % len(colors)],
        })
    return records


def _parse_paginated_table(document) -> dict | None:
    pages = []
    for page in document:
        found = page.find_tables().tables
        if not found or found[0].col_count != 9:
            return None
        table = found[0]
        extracted = table.extract()
        page_rows = []
        for row_index, values in enumerate(extracted):
            section_match = re.match(r"\s*(\d+)\b", values[1] or "")
            section = int(section_match.group(1)) if section_match else None
            page_rows.append({"index": row_index, "section": section, "values": values, "cells": table.rows[row_index].cells})
        pages.append(page_rows)

    # The first row of a continuation page can finish a cell split by pagination.
    for page_index in range(1, len(pages)):
        continuation = pages[page_index][0]
        if continuation["section"] is not None:
            continue
        previous_rows = [row for row in pages[page_index - 1] if row["section"] is not None]
        if not previous_rows:
            continue
        previous = previous_rows[-1]
        for column in range(2, 9):
            if continuation["values"][column]:
                previous["values"][column] = (previous["values"][column] or "") + "\n" + continuation["values"][column]

    courses = []
    for page_rows in pages:
        section_rows = [row for row in page_rows if row["section"] is not None]
        for row in section_rows:
            for column in range(2, 9):
                text = row["values"][column]
                cell = row["cells"][column]
                if not text or not cell:
                    continue
                end_section = row["section"]
                for candidate in section_rows:
                    section_cell = candidate["cells"][1]
                    if section_cell and section_cell[1] < cell[3] - 1 and candidate["section"] >= row["section"]:
                        end_section = max(end_section, candidate["section"])
                courses.extend(_parse_cell_records(text, column - 1, row["section"], end_section))

    if not courses:
        return None
    merged = []
    for course in sorted(courses, key=lambda item: (item["weekday"], item["start_section"], item["end_section"], item["name"])):
        previous = next((item for item in reversed(merged)
                         if item["end_section"] + 1 == course["start_section"]
                         and all(item[key] == course[key] for key in ("name", "teacher", "room", "weekday", "weeks"))), None)
        if previous:
            previous["end_section"] = course["end_section"]
        else:
            merged.append(course)
    return {"name": "我的课表", "term": "导入课表", "courses": merged}


def parse_structured_schedule(path: Path) -> dict | None:
    """Parse coordinate-based timetable PDFs exported by the school system."""
    if path.suffix.lower() != ".pdf":
        return None
    document = fitz.open(path)
    paginated = _parse_paginated_table(document)
    if paginated:
        return paginated
    if document.page_count != 1:
        return None
    page = document[0]
    lines = []
    for block in page.get_text("dict").get("blocks", []):
        if "lines" not in block:
            continue
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"]).strip()
            if text:
                x0, y0, x1, y1 = line["bbox"]
                lines.append({"text": text, "x": (x0 + x1) / 2, "y0": y0, "y1": y1})

    headers = {}
    for line in lines:
        if line["text"] in WEEKDAYS:
            headers[WEEKDAYS[line["text"]]] = line["x"]
    if len(headers) != 7:
        return None

    title_line = next((line["text"] for line in lines if "学年第" in line["text"] and "课表" in line["text"]), "我的课表")
    term_match = re.search(r"(\d{4}-\d{4}学年第\d学期)", title_line)
    term = term_match.group(1) if term_match else title_line.replace("课表", "").strip()
    owner = title_line.replace(term, "").replace("课表", "").strip()

    centers = [headers[index] for index in range(1, 8)]
    boundaries = [(centers[i] + centers[i + 1]) / 2 for i in range(6)]
    colors = ["#5579E8", "#EF5B78", "#F18745", "#8B6AD8", "#42A5C9", "#55AD72", "#D79D39"]
    courses = []
    body_top, row_height = 102.0, 34.0

    for weekday in range(1, 8):
        left = centers[0] - (centers[1] - centers[0]) / 2 if weekday == 1 else boundaries[weekday - 2]
        right = float("inf") if weekday == 7 else boundaries[weekday - 1]
        column = [line for line in lines if left < line["x"] < right and body_top <= line["y0"] < body_top + row_height * 10]
        column.sort(key=lambda item: (item["y0"], item["x"]))
        consumed = 0
        for index, line in enumerate(column):
            match = re.match(r"(.+?)【(.+?)周】", line["text"])
            if not match:
                continue
            title_parts = [item["text"] for item in column[consumed:index] if not re.match(r"^\d+-", item["text"]) and "教室" not in item["text"]]
            title_parts = [part for position, part in enumerate(title_parts) if position == 0 or part != title_parts[position - 1]]
            name = "".join(title_parts).strip()
            if not name:
                continue
            room_line = column[index + 1] if index + 1 < len(column) else None
            room = room_line["text"] if room_line and (re.match(r"^\d+-", room_line["text"]) or "教室" in room_line["text"]) else ""
            bottom = room_line["y1"] if room else line["y1"]
            start_section = max(1, min(10, int((column[consumed]["y0"] - body_top) // row_height) + 1))
            end_section = max(start_section, min(10, int((bottom - body_top) // row_height) + 1))
            courses.append({
                "name": name,
                "teacher": match.group(1).strip(),
                "room": room,
                "weekday": weekday,
                "start_section": start_section,
                "end_section": end_section,
                "weeks": parse_weeks(match.group(2)),
                "color": colors[(weekday + start_section - 2) % len(colors)],
            })
            consumed = index + (2 if room else 1)

    if not courses:
        return None
    return {"name": f"{owner}的课表" if owner else "我的课表", "term": term, "courses": courses}


def extract_text(path: Path) -> tuple[str, str]:
    """Return OCR text and engine status. PaddleOCR is intentionally optional."""
    images = []
    if path.suffix.lower() == ".pdf":
        import fitz
        doc = fitz.open(path)
        direct = "\n".join(page.get_text() for page in doc).strip()
        if len(direct) > 80:
            return direct, "pdf-text"
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            target = path.with_name(f"{path.stem}-{page.number}.png")
            pix.save(target)
            images.append(target)
    else:
        images.append(path)

    try:
        from paddleocr import PaddleOCR
    except ImportError:
        return "", "ocr-not-installed"

    ocr = PaddleOCR(lang="ch", use_doc_orientation_classify=False, use_doc_unwarping=False)
    lines = []
    for image in images:
        result = ocr.predict(str(image))
        for item in result:
            data = getattr(item, "json", {})
            if callable(data):
                data = data()
            rec = data.get("res", data) if isinstance(data, dict) else {}
            lines.extend(rec.get("rec_texts", []))
    return "\n".join(lines), "paddleocr"


def suggest_courses(text: str) -> list[dict]:
    """Conservative suggestions; user confirms positions in the editor."""
    skip = re.compile(r"^(星期|周[一二三四五六日]|节次|课程表|时间|教室|教师|备注)")
    candidates = []
    seen = set()
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip(" |,，;；")
        if len(line) < 3 or len(line) > 40 or skip.search(line) or line in seen:
            continue
        if re.search(r"[\u4e00-\u9fff]{2,}", line):
            seen.add(line)
            candidates.append({"name": line, "teacher": "", "room": "", "weekday": 1,
                               "start_section": 1, "end_section": 2, "weeks": [], "color": "#6C8CFF"})
        if len(candidates) >= 30:
            break
    return candidates
