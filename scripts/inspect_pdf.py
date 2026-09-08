import sys
from pathlib import Path

import fitz

source = Path(sys.argv[1])
output = Path(sys.argv[2])
output.mkdir(parents=True, exist_ok=True)

document = fitz.open(source)
print(f"pages={document.page_count}")
for page in document:
    text = page.get_text("text")
    (output / f"page-{page.number + 1}.txt").write_text(text, encoding="utf-8")
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    pixmap.save(output / f"page-{page.number + 1}.png")
    blocks = []
    for block in page.get_text("blocks"):
        blocks.append(f"{block[0]:.1f}\t{block[1]:.1f}\t{block[2]:.1f}\t{block[3]:.1f}\t{block[4].strip()!r}")
    (output / f"page-{page.number + 1}-blocks.txt").write_text("\n".join(blocks), encoding="utf-8")
    tables = page.find_tables()
    table_lines = []
    for table_index, table in enumerate(tables.tables):
        table_lines.append(f"TABLE {table_index} rows={table.row_count} cols={table.col_count} bbox={table.bbox}")
        for row_index, row in enumerate(table.extract()):
            table_lines.append(f"ROW {row_index}: {row!r}")
    (output / f"page-{page.number + 1}-tables.txt").write_text("\n".join(table_lines), encoding="utf-8")
    print(f"page={page.number + 1} width={page.rect.width} height={page.rect.height} text_chars={len(text)}")
