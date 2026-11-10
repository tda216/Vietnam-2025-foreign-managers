"""Markdown -> .docx for the handover report (real Word tables, Heading styles, numbered / bulleted nested lists, code
blocks); Python stdlib only (no pandoc / node / python-docx on this machine; macOS textutil flattens tables).
Run from the project root after editing the .md:
  .venv/bin/python -I indonesia/pipeline/id_md2docx.py indonesia/output/HANDOVER_REPORT.md \
      indonesia/output/HANDOVER_REPORT.docx "Handover report – Indonesia FY2025"
"""
import datetime as dt, re, sys, zipfile
from xml.sax.saxutils import escape

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" ' \
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
NAVY, TEXT, CODE, GRID, HEAD, CODEBG = "13284B", "181E26", "1D2B42", "9AA5B5", "DDEBF7", "F3F5F8"
PAGE_W, MARGIN = 11906, 1134            # A4, 2 cm margins
TEXT_W = PAGE_W - 2 * MARGIN            # 9638 DXA


# ---------- markdown parsing ----------
LI = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")


def parse(md):
    lines, blocks, i, para = md.split("\n"), [], 0, []

    def flush():
        if para:
            blocks.append(("p", " ".join(x.strip() for x in para))); para.clear()
    n = len(lines)
    while i < n:
        ln = lines[i]
        if ln.startswith("```"):
            flush(); j, buf = i + 1, []
            while j < n and not lines[j].startswith("```"):
                buf.append(lines[j]); j += 1
            blocks.append(("code", buf)); i = j + 1; continue
        m = re.match(r"^(#{1,3})\s+(.*)$", ln)
        if m:
            flush(); blocks.append(("h", len(m.group(1)), m.group(2))); i += 1; continue
        if ln.strip() == "---":
            flush(); blocks.append(("hr",)); i += 1; continue
        if ln.startswith("|"):
            flush(); rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            blocks.append(("table", rows[0], [a.endswith(":") for a in rows[1]], rows[2:])); continue
        if LI.match(ln):
            flush(); items, base = [], None
            while i < n and (LI.match(lines[i]) or (re.match(r"^\s{2,}\S", lines[i]) and items)):
                m = LI.match(lines[i])
                if not m:
                    items[-1][2] += " " + lines[i].strip(); i += 1; continue
                ind = len(m.group(1))
                if base is None:
                    base = ind
                lvl = 0 if ind <= base else (1 if ind <= base + 4 else 2)
                items.append([lvl, m.group(2)[0].isdigit(), m.group(3)]); i += 1
            blocks.append(("list", items)); continue
        if not ln.strip():
            flush(); i += 1; continue
        para.append(ln); i += 1
    flush()
    return blocks


# ---------- runs ----------
def runs(text, bold=False, size=None):
    out = []
    for part in re.split(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))", text):
        if not part:
            continue
        b, code = bold, False
        if part.startswith("**") and part.endswith("**"):
            part, b = part[2:-2], True
        if part.startswith("`") and part.endswith("`"):
            part, code = part[1:-1], True
        m = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", part)
        if m:
            part = m.group(1)
        # nested `code` inside **bold**
        for sub in re.split(r"(`[^`]+`)", part):
            if not sub:
                continue
            c = code or (sub.startswith("`") and sub.endswith("`") and len(sub) > 1)
            s = sub[1:-1] if (not code and c) else sub
            rpr = ('<w:rFonts w:ascii="Menlo" w:hAnsi="Menlo" w:cs="Menlo"/>' if c else "") + ("<w:b/>" if b else "")
            if c:
                rpr += f'<w:color w:val="{CODE}"/><w:sz w:val="{(size or 22) - 3}"/>'
            elif size:
                rpr += f'<w:sz w:val="{size}"/>'
            out.append(f'<w:r>{"<w:rPr>" + rpr + "</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{escape(s)}</w:t></w:r>')
    return "".join(out)


def p(content, style=None, extra=""):
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + extra
    return f'<w:p>{"<w:pPr>" + ppr + "</w:pPr>" if ppr else ""}{content}</w:p>'


# ---------- blocks ----------
def table(head, right, rows):
    ncol = len(head)
    longest = [max([len(re.sub(r"[`*]", "", r[k])) if k < len(r) else 0 for r in [head] + rows]) for k in range(ncol)]
    weight = [min(max(x, 6), 60) for x in longest]
    widths = [int(TEXT_W * w / sum(weight)) for w in weight]
    floor = [len(re.sub(r"[`*]", "", h)) * 115 + 260 for h in head]  # the header word must fit on one line
    short = sum(max(0, f - w) for f, w in zip(floor, widths))
    if short:
        spare = [max(0, w - f) for f, w in zip(floor, widths)]
        widths = [max(w, f) - (int(short * sp / sum(spare)) if sum(spare) else 0) for w, f, sp in zip(widths, floor, spare)]
    widths[-1] = TEXT_W - sum(widths[:-1])
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="{GRID}"/>' for s in
                     ("top", "left", "bottom", "right", "insideH", "insideV"))
    x = [f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_W}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>'
         f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
         f'<w:bottom w:w="40" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>'
         + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"]
    for ri, r in enumerate([head] + rows):
        hdr = ri == 0
        x.append("<w:tr>" + ('<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' if hdr else '<w:trPr><w:cantSplit/></w:trPr>'))
        for k in range(ncol):
            cell = r[k] if k < len(r) else ""
            shade = f'<w:shd w:val="clear" w:color="auto" w:fill="{HEAD}"/>' if hdr else ""
            jc = '<w:jc w:val="right"/>' if (right[k] and not hdr) else ""
            x.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[k]}" w:type="dxa"/>{shade}</w:tcPr>'
                     + p(runs(cell, bold=hdr, size=19), "TableText", jc) + "</w:tc>")
        x.append("</w:tr>")
    x.append("</w:tbl>")
    return "".join(x) + p("", "Spacer")


def build(blocks):
    body, nums = [], []
    for b in blocks:
        if b[0] == "h":
            body.append(p(runs(b[2]), {1: "Title", 2: "Heading1", 3: "Heading2"}[b[1]]))
        elif b[0] == "p":
            body.append(p(runs(b[1])))
        elif b[0] == "hr":
            body.append(p("", None, f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="C8CFD9"/></w:pBdr>'))
        elif b[0] == "code":
            for ln in b[1] or [""]:
                body.append(p(f'<w:r><w:t xml:space="preserve">{escape(ln)}</w:t></w:r>', "Code"))
            body.append(p("", "Spacer"))
        elif b[0] == "table":
            body.append(table(b[1], b[2], b[3]))
        elif b[0] == "list":
            ordered = b[1][0][1]
            nid = len(nums) + 1
            nums.append(2 if ordered else 1)
            for lvl, _o, text in b[1]:
                body.append(p(runs(text), "ListParagraph",
                              f'<w:numPr><w:ilvl w:val="{lvl}"/><w:numId w:val="{nid}"/></w:numPr>'))
    sect = (f'<w:sectPr><w:pgSz w:w="{PAGE_W}" w:h="16838"/><w:pgMar w:top="{MARGIN}" w:right="{MARGIN}" '
            f'w:bottom="{MARGIN}" w:left="{MARGIN}" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>')
    doc = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>{"".join(body)}{sect}</w:body></w:document>'
    return doc, nums


def numbering(nums):
    def lvl(i, fmt, txt, ind):
        return (f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:lvlText w:val="{txt}"/>'
                f'<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="{ind}" w:hanging="360"/></w:pPr>'
                + ('<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr>' if fmt == "bullet" else "") + "</w:lvl>")
    bullets = lvl(0, "bullet", "•", 720) + lvl(1, "bullet", "◦", 1440) + lvl(2, "bullet", "▪", 2160)
    ordered = lvl(0, "decimal", "%1.", 720) + lvl(1, "bullet", "◦", 1440) + lvl(2, "bullet", "▪", 2160)
    x = [f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering {W}>',
         f'<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>{bullets}</w:abstractNum>',
         f'<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="hybridMultilevel"/>{ordered}</w:abstractNum>']
    for i, a in enumerate(nums, 1):
        x.append(f'<w:num w:numId="{i}"><w:abstractNumId w:val="{a}"/>'
                 '<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>')
    return "".join(x) + "</w:numbering>"


def styles():
    font = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial"/>'

    def ps(sid, name, size, color, before, after, bold=False, keep=False, outline=None, shd="", ind="", rfonts=None):
        ol = f'<w:outlineLvl w:val="{outline}"/>' if outline is not None else ""
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/>'
                f'<w:next w:val="Normal"/><w:qFormat/><w:pPr>{"<w:keepNext/>" if keep else ""}{shd}'
                f'<w:spacing w:before="{before}" w:after="{after}"/>{ind}{ol}</w:pPr>'
                f'<w:rPr>{rfonts or font}{"<w:b/>" if bold else ""}<w:color w:val="{color}"/><w:sz w:val="{size}"/></w:rPr></w:style>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:styles {W}><w:docDefaults><w:rPrDefault><w:rPr>{font}<w:color w:val="{TEXT}"/><w:sz w:val="21"/>'
            '<w:lang w:val="en-GB"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="100" w:line="264" '
            'w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
            f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
            f'<w:rPr>{font}<w:sz w:val="21"/></w:rPr></w:style>'
            + ps("Title", "Title", 40, NAVY, 0, 160, bold=True, keep=True, outline=0)
            + ps("Heading1", "heading 1", 30, NAVY, 320, 120, bold=True, keep=True, outline=1)
            + ps("Heading2", "heading 2", 24, NAVY, 220, 80, bold=True, keep=True, outline=2)
            + ps("ListParagraph", "List Paragraph", 21, TEXT, 0, 60)
            + ps("TableText", "Table Text", 19, TEXT, 0, 0)
            + ps("Spacer", "Spacer", 10, TEXT, 0, 80)
            + ps("Code", "Code", 17, CODE, 0, 0, shd=f'<w:shd w:val="clear" w:color="auto" w:fill="{CODEBG}"/>',
                 ind='<w:ind w:left="113" w:right="113"/>', rfonts='<w:rFonts w:ascii="Menlo" w:hAnsi="Menlo" w:cs="Menlo"/>')
            + "</w:styles>")


def main():
    src, dst, title = sys.argv[1], sys.argv[2], sys.argv[3]
    doc, nums = build(parse(open(src, encoding="utf-8").read()))
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>',
        "word/_rels/document.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/></Relationships>',
        "word/document.xml": doc, "word/styles.xml": styles(), "word/numbering.xml": numbering(nums),
        "docProps/core.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{escape(title)}</dc:title><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>',
        "docProps/app.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>md2docx</Application></Properties>',
    }
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:  # files only, no folder entries
        for name, data in files.items():
            z.writestr(name, data)
    print("wrote", dst, "| blocks", len(doc), "| lists", len(nums))


if __name__ == "__main__":
    main()
