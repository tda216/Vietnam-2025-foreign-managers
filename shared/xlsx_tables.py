"""Workbook table helper shared by all countries: one sheet per table, styled header, frozen panes, filter."""
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEAD_FILL = PatternFill("solid", fgColor="1F3864")
HEAD_FONT = Font(bold=True, color="FFFFFF")
NUMERIC = {"Foreign_Ownership_Pct", "CafeF_FO_Pct", "Diff_PP", "Market_Cap_LCL", "Mcap_Rank", "FO_Page",
           "In_Scope", "Manager_Search", "Deep_Prelim", "Qty_Issued", "Qty_Foreign_Held", "Max_Foreign_Ratio_Pct", "Page",
           "Bloomberg_Row"}


def cell_value(col, v):
    if isinstance(v, str):
        v = ILLEGAL_CHARACTERS_RE.sub("", v)  # control characters Excel cannot store (display copy only; CSVs keep them)
    if col in NUMERIC and v not in ("", None):
        try:
            f = float(v)
            return int(f) if f.is_integer() and col not in ("Foreign_Ownership_Pct", "CafeF_FO_Pct", "Diff_PP") else f
        except ValueError:
            return v
    return v


def add_table(wb, title, rows, cols, widths=None):
    ws = wb.create_sheet(title)
    ws.append(cols)
    for c in ws[1]:
        c.fill, c.font, c.alignment = HEAD_FILL, HEAD_FONT, Alignment(wrap_text=True, vertical="top")
    for r in rows:
        ws.append([cell_value(c, r.get(c, "")) for c in cols])
    ws.freeze_panes = "C2" if len(cols) > 3 else "A2"
    ws.auto_filter.ref = ws.dimensions
    for i, c in enumerate(cols, start=1):
        w = (widths or {}).get(c) or min(max(len(c) + 2, *(len(str(r.get(c, ""))) + 1 for r in rows[:300]), 10), 60) if rows else len(c) + 2
        ws.column_dimensions[get_column_letter(i)].width = w
        if c in ("Foreign_Ownership_Pct", "CafeF_FO_Pct"):
            for cell in ws[get_column_letter(i)][1:]:
                cell.number_format = "0.00"
    return ws
