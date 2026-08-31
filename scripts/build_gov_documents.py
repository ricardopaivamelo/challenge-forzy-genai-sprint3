"""Gera os documentos Word da Challenge Sprint 3 GOV."""

from __future__ import annotations

from pathlib import Path
import re
import sys

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DOCS_SKILL = Path(
    "/home/ricardo/.codex/plugins/cache/openai-primary-runtime/documents/"
    "26.826.12353/skills/documents"
)
sys.path.insert(0, str(DOCS_SKILL / "scripts"))
from table_geometry import (  # noqa: E402
    apply_table_geometry,
    column_widths_from_weights,
    section_content_width_dxa,
)


BLUE = "1F4E78"
LIGHT_BLUE = "D9EAF7"
LIGHT_RED = "FCE8E6"
BLACK = RGBColor(0, 0, 0)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def keep_table_row_together(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def style_table(table, *, header_fill: str = BLUE, font_size: float = 9.0) -> None:
    table.style = "Table Grid"
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if row_index == 0:
                set_cell_shading(cell, header_fill)
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.first_line_indent = Cm(0)
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Arial")
                    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Arial")
                    run.font.size = Pt(font_size)
                    if row_index == 0:
                        run.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
        if row_index == 0:
            set_repeat_table_header(row)


def add_table(
    doc,
    headers,
    rows,
    weights,
    *,
    font_size=9.0,
    narrative=False,
    keep_rows_together=False,
):
    table = doc.add_table(rows=1, cols=len(headers))
    for index, value in enumerate(headers):
        table.rows[0].cells[index].text = str(value)
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cells[index].text = str(value)
    total_width = section_content_width_dxa(doc.sections[-1])
    widths = column_widths_from_weights(weights, total_width)
    apply_table_geometry(
        table,
        widths,
        table_width_dxa=total_width,
        indent_dxa=120,
        cell_margins_dxa={
            "top": 60 if narrative else 90,
            "bottom": 60 if narrative else 90,
            "start": 120,
            "end": 120,
        },
    )
    style_table(table, font_size=font_size)
    if keep_rows_together:
        for row in table.rows[1:]:
            keep_table_row_together(row)
    if narrative:
        for row in table.rows[1:]:
            for cell in row.cells:
                cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_page_field(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, end])


def set_page_number_start(section, start: int) -> None:
    page_number_type = section._sectPr.find(qn("w:pgNumType"))
    if page_number_type is None:
        page_number_type = OxmlElement("w:pgNumType")
        section._sectPr.append(page_number_type)
    page_number_type.set(qn("w:start"), str(start))


def continue_page_numbering(section) -> None:
    page_number_type = section._sectPr.find(qn("w:pgNumType"))
    if page_number_type is not None:
        section._sectPr.remove(page_number_type)


def add_toc(doc) -> None:
    heading = doc.add_paragraph("SUMÁRIO", style="Heading 1")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    entries = [
        (0, "1 INTRODUÇÃO", 4),
        (0, "2 CONTEXTUALIZAÇÃO DA SOLUÇÃO FORZY", 4),
        (0, "3 EVOLUÇÃO DA GOVERNANÇA — SPRINT 1", 5),
        (1, "3.1 Hierarquia e controle de acesso", 5),
        (1, "3.2 Cadeia D-I-C-I", 6),
        (1, "3.3 Explainability", 7),
        (1, "3.4 Protocolo de rastreabilidade", 7),
        (1, "3.5 Dicionário de metadados", 8),
        (1, "3.6 Fairness e limitações", 8),
        (0, "4 EVOLUÇÃO DA GOVERNANÇA — SPRINT 2", 9),
        (1, "4.1 Governança visual", 9),
        (1, "4.2 Rastreabilidade de TAG e localização", 9),
        (1, "4.3 Correções aplicadas a partir do feedback", 9),
        (0, "5 INTELIGÊNCIA OPERACIONAL E GOVERNANÇA DA DECISÃO — SPRINT 3", 10),
        (1, "5.1 Metric Contracts", 10),
        (1, "5.2 Definição operacional de anomalia", 10),
        (1, "5.3 Ações automáticas permitidas", 11),
        (1, "5.4 Circuit Breaker", 11),
        (1, "5.5 Protocolo de handoff humano", 11),
        (1, "5.6 Informação explícita e informação tácita", 12),
        (0, "6 EVIDÊNCIAS DE FUNCIONAMENTO", 13),
        (0, "7 CONSIDERAÇÕES FINAIS", 18),
    ]
    for level, title, page in entries:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.6 * level)
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(f"{title} {'.' * max(4, 72 - len(title))} {page}")
        run.font.name = "Times New Roman"
        run.font.size = Pt(10.5)
        run.bold = level == 0


def enable_field_updates(doc) -> None:
    settings = doc.settings._element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")


def configure_main_styles(doc) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(12)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.first_line_indent = Cm(1.25)

    for style_name, size in (("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 12)):
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = BLACK
        style.paragraph_format.first_line_indent = Cm(0)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True

    for style_name in ("List Bullet", "List Number"):
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(12)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.space_after = Pt(0)


def configure_main_section(section, *, landscape: bool) -> None:
    section.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    section.page_width = Cm(29.7 if landscape else 21.0)
    section.page_height = Cm(21.0 if landscape else 29.7)
    section.top_margin = Cm(3.0)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)


def add_inline_markdown(paragraph, text: str) -> None:
    tokens = re.split(r"(\*\*.*?\*\*|`.*?`)", text)
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith("`") and token.endswith("`"):
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(10)
        else:
            paragraph.add_run(token)


def add_markdown_table(doc, lines: list[str]) -> None:
    parsed = [
        [cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")]
        for line in lines
    ]
    headers = parsed[0]
    rows = parsed[2:]
    if headers == ["Métrica", "Unidade", "Normal", "Atenção", "Crítico"]:
        weights = [1.45, 0.90, 1.0, 1.40, 1.0]
    elif headers == ["Métrica", "Unidade", "Normal", "Atenção", "Crítico", "Origem do limite"]:
        weights = [1.45, 0.75, 1.0, 1.35, 1.0, 2.45]
    elif len(headers) == 7:
        weights = [1.10, 1.25, 1.25, 1.10, 1.10, 1.0, 1.40]
    else:
        weights = []
        for column in range(len(headers)):
            longest = max(len(str(row[column])) for row in [headers, *rows])
            weights.append(max(1.0, min(float(longest), 35.0)))
    add_table(
        doc,
        headers,
        rows,
        weights,
        font_size=7.5 if len(headers) == 7 else (8.5 if len(headers) > 4 else 9.0),
        narrative=len(headers) == 7,
        keep_rows_together=len(headers) == 7,
    )


def parse_main_markdown(doc, markdown_path: Path) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line == "## RESUMO")
    lines = lines[start:]
    index = 0
    toc_added = False
    figure_count = 0
    matrix_landscape = False
    while index < len(lines):
        raw = lines[index]
        line = raw.strip()
        if not line:
            index += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            add_markdown_table(doc, table_lines)
            continue
        if line.startswith("!["):
            match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            if match:
                image_path = (markdown_path.parent / match.group(2)).resolve()
                paragraph = doc.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.keep_with_next = True
                picture = paragraph.add_run().add_picture(str(image_path), width=Inches(6.25))
                picture._inline.docPr.set("descr", match.group(1))
                picture._inline.docPr.set("title", match.group(1))
            index += 1
            continue
        if line.startswith("## 5.6"):
            landscape_section = doc.add_section(WD_SECTION.NEW_PAGE)
            configure_main_section(landscape_section, landscape=True)
            continue_page_numbering(landscape_section)
            doc.add_paragraph(line[3:], style="Heading 2")
            matrix_landscape = True
            index += 1
            continue
        if line.startswith("**Quadro 8"):
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.keep_with_next = True
            add_inline_markdown(paragraph, line)
            index += 1
            continue
        if line.startswith("# 1 INTRODUÇÃO") and not toc_added:
            doc.add_page_break()
            add_toc(doc)
            content_section = doc.add_section(WD_SECTION.NEW_PAGE)
            configure_main_section(content_section, landscape=False)
            content_section.footer.is_linked_to_previous = False
            add_page_field(content_section.footer.paragraphs[0])
            set_page_number_start(content_section, 4)
            toc_added = True
        if line == "# 7 CONSIDERAÇÕES FINAIS":
            doc.add_page_break()
        if line.startswith("# "):
            doc.add_paragraph(line[2:], style="Heading 1")
            index += 1
            continue
        if line.startswith("## "):
            doc.add_paragraph(line[3:], style="Heading 2" if re.match(r"\d+\.\d+", line[3:]) else "Heading 1")
            index += 1
            continue
        if line.startswith("### "):
            doc.add_paragraph(line[4:], style="Heading 3")
            index += 1
            continue
        if line.startswith(">"):
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.left_indent = Cm(0.5)
            paragraph.paragraph_format.right_indent = Cm(0.5)
            paragraph.paragraph_format.first_line_indent = Cm(0)
            set_cell_like = OxmlElement("w:shd")
            set_cell_like.set(qn("w:fill"), LIGHT_RED)
            paragraph._p.get_or_add_pPr().append(set_cell_like)
            text = line.lstrip("> ")
            index += 1
            while index < len(lines) and lines[index].strip().startswith(">"):
                text += " " + lines[index].strip().lstrip("> ")
                index += 1
            add_inline_markdown(paragraph, text)
            continue
        if line.startswith("- "):
            paragraph = doc.add_paragraph(style="List Bullet")
            paragraph.paragraph_format.first_line_indent = None
            add_inline_markdown(paragraph, line[2:])
            if line[2:].startswith("Figura "):
                for run in paragraph.runs:
                    run.font.size = Pt(10)
            index += 1
            continue
        if re.match(r"\d+\. ", line):
            paragraph = doc.add_paragraph(style="List Number")
            paragraph.paragraph_format.first_line_indent = None
            add_inline_markdown(paragraph, re.sub(r"^\d+\. ", "", line))
            index += 1
            continue
        if line.startswith("**Figura"):
            figure_count += 1
            if figure_count > 1:
                doc.add_page_break()
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.keep_with_next = True
            add_inline_markdown(paragraph, line)
            index += 1
            continue

        paragraph_lines = [line]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate.startswith(("#", "|", "- ", ">", "![")):
                break
            if re.match(r"\d+\. ", candidate) or candidate.startswith("**Figura"):
                break
            paragraph_lines.append(candidate)
            index += 1
        text = " ".join(paragraph_lines)
        paragraph = doc.add_paragraph()
        if text.startswith("Fonte:"):
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.space_before = Pt(4)
            paragraph.paragraph_format.space_after = Pt(6)
        add_inline_markdown(paragraph, text)
        if text.startswith("Fonte:"):
            for run in paragraph.runs:
                run.italic = True
                run.font.size = Pt(10)
            if matrix_landscape:
                portrait_section = doc.add_section(WD_SECTION.NEW_PAGE)
                configure_main_section(portrait_section, landscape=False)
                continue_page_numbering(portrait_section)
                matrix_landscape = False


def build_main_document(output: Path) -> None:
    doc = Document()
    section = doc.sections[0]
    configure_main_section(section, landscape=False)
    configure_main_styles(doc)

    for text, size, bold, after in [
        ("FACULDADE DE INFORMÁTICA E TECNOLOGIA — FIAP", 12, True, 6),
        ("TECNÓLOGO EM INTELIGÊNCIA ARTIFICIAL", 12, True, 70),
        ("GOVERNANÇA EM IA E BUSINESS ANALYTICS", 14, True, 18),
        ("INTELIGÊNCIA OPERACIONAL E GOVERNANÇA DA DECISÃO", 14, True, 6),
        ("Solução Digital Twin Forzy — Challenge Sprint 3", 12, False, 42),
    ]:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_after = Pt(after)
        run = paragraph.add_run(text)
        run.font.name = "Times New Roman"
        run.font.size = Pt(size)
        run.bold = bold

    members = [
        "RM566479 — Jonas Alaf da Silva",
        "RM562358 — Murilo Benhossi",
        "RM565460 — Pedro Leal Murad",
        "RM561401 — Luís Fernando de Oliveira Salgado",
        "RM565522 — Ricardo de Paiva Melo",
        "RM553273 — Nicolas Lemos Ribeiro",
    ]
    for member in members:
        paragraph = doc.add_paragraph(member)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.0
    professor = doc.add_paragraph("Professor: Marco Fontoura")
    professor.alignment = WD_ALIGN_PARAGRAPH.CENTER
    professor.paragraph_format.first_line_indent = Cm(0)
    professor.paragraph_format.space_before = Pt(18)
    city = doc.add_paragraph("São Paulo\n2026")
    city.alignment = WD_ALIGN_PARAGRAPH.CENTER
    city.paragraph_format.first_line_indent = Cm(0)
    city.paragraph_format.space_before = Pt(38)

    body_section = doc.add_section(WD_SECTION.NEW_PAGE)
    configure_main_section(body_section, landscape=False)
    parse_main_markdown(doc, ROOT / "docs" / "gov" / "sprint3_documento_vivo.md")
    enable_field_updates(doc)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)


def clear_document_body(doc) -> None:
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def add_contract_metric(doc, number, name, description, values):
    doc.add_paragraph(f"2.3.{number} {name}", style="Heading 4")
    doc.add_paragraph(description)
    add_table(doc, ["Indicador", "Valores"], values, [0.30, 0.70], font_size=10)


def build_metric_contract(reference: Path, output: Path) -> None:
    doc = Document(reference)
    for section in doc.sections:
        for table in section.footer.tables:
            if len(table.rows) >= 2 and len(table.columns) >= 2:
                table.cell(0, 1).text = "Forzy Digital Twin — Governança da Decisão"
                table.cell(1, 1).text = "1.0"
                set_repeat_table_header(table.rows[0])
    clear_document_body(doc)
    doc.add_paragraph("Metric Contract", style="Heading 1")
    doc.add_paragraph("1. Descrição do Caso", style="Heading 2")
    doc.add_paragraph(
        "Formalização dos limites de temperatura, vibração e aceleração usados pela "
        "plataforma Forzy. O contrato define unidade, qualidade mínima, thresholds, ações "
        "automáticas permitidas e condições de bloqueio antes do handoff humano."
    )
    doc.add_paragraph("2. Metric Contract", style="Heading 2")
    doc.add_paragraph("2.1 Informações Gerais", style="Heading 3")
    add_table(
        doc,
        ["Campo", "Definição"],
        [
            ["Nome do Projeto", "Forzy Digital Twin — Governança da Decisão"],
            ["Responsável de Negócio", "Gestor de Planta"],
            ["Responsável Técnico", "Engenharia de Dados/IA e Manutenção"],
            ["Data de Criação", "31/08/2026"],
            ["Versão", "1.0"],
            ["Revisão", "Obrigatória após mudança de sensor, planta ou modelo"],
        ],
        [0.29, 0.71],
        font_size=10,
    )
    doc.add_paragraph("2.2 Objetivo de Negócio", style="Heading 3")
    doc.add_paragraph(
        "Reduzir alertas indevidos e impedir que dados inconsistentes ou previsões incertas "
        "gerem decisões automáticas de manutenção na planta."
    )
    doc.add_paragraph("2.3 Métricas", style="Heading 3")
    add_contract_metric(
        doc,
        1,
        "Temperatura",
        "Temperatura da carcaça do motor no protótipo, recebida em graus Celsius.",
        [
            ["Campo / Unidade", "temperatura_c / °C"],
            ["Domínio físico", "0 a 200 °C"],
            ["Normal", "< 90 °C"],
            ["Atenção", "≥ 90 °C e < 100 °C"],
            ["Crítico", "≥ 100 °C"],
            ["Fonte", "Faixas empíricas do protótipo; requer validação industrial"],
        ],
    )
    add_contract_metric(
        doc,
        2,
        "Vibração RMS",
        "Velocidade RMS da vibração do motor, recebida em milímetros por segundo.",
        [
            ["Campo / Unidade", "vibracao_mm_s / mm/s"],
            ["Domínio físico", "0 a 50 mm/s"],
            ["Normal", "< 6 mm/s"],
            ["Atenção", "≥ 6 mm/s e < 9 mm/s"],
            ["Crítico", "≥ 9 mm/s"],
            ["Fonte", "Faixas empíricas do protótipo; requer validação industrial"],
        ],
    )
    add_contract_metric(
        doc,
        3,
        "Aceleração",
        "Aceleração equivalente simulada a partir da vibração RMS e componente de 60 Hz. "
        "Não representa leitura de acelerômetro industrial.",
        [
            ["Campo / Unidade", "aceleracao_g / g"],
            ["Domínio físico", "0 a 5 g"],
            ["Normal", "< 0,1487 g"],
            ["Atenção", "≥ 0,1487 g e < 0,1813 g"],
            ["Crítico", "≥ 0,1813 g"],
            ["Fonte", "Quantis 95% e 99% de 26.291 leituras normais simuladas"],
        ],
    )
    doc.add_paragraph("2.4 Métricas de Qualidade", style="Heading 3")
    add_table(
        doc,
        ["Métrica", "Indicador mínimo"],
        [
            ["Completude da janela", "≥ 90%"],
            ["Atualidade", "Leitura com até 5 minutos"],
            ["Unicidade", "Sem timestamp duplicado por motor"],
            ["Validade", "100% dentro do domínio físico"],
            ["Unidade", "100% compatível com o contrato"],
        ],
        [0.50, 0.50],
        font_size=10,
    )
    doc.add_paragraph("2.5 Thresholds e Alertas", style="Heading 3")
    add_table(
        doc,
        ["Threshold/Alerta", "Gatilho", "Incidente/Ação"],
        [
            ["Atenção física", "Sensor na faixa de atenção", "Destacar e monitorar"],
            ["Anomalia do modelo", "Score ≥ 0,9513", "Exigir 3 janelas persistentes"],
            ["Alerta confirmado", "Modelo persistente + evidência física", "Solicitar inspeção humana"],
            ["Circuit Breaker", "Falha de dados, incerteza ou divergência", "Bloquear decisão e registrar motivo"],
            ["Handoff", "Confiança < 85% ou situação contextual", "Encaminhar ao Engenheiro de Manutenção"],
        ],
        [0.28, 0.30, 0.42],
        font_size=9.5,
    )
    doc.add_paragraph("2.6 Plano de Monitoramento", style="Heading 3")
    doc.add_paragraph(
        "Registrar versão do contrato, leituras, score, persistência, estado do Circuit "
        "Breaker, justificativa e decisão humana. Revisar limites quando houver troca de "
        "sensor, alteração de regime operacional ou mudança relevante na distribuição dos "
        "dados. Nenhum contrato autoriza parada automática do motor ou da planta."
    )
    enable_field_updates(doc)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)


if __name__ == "__main__":
    reference = Path("/home/ricardo/Downloads/Aula_01_Metric_Contract_Modelo - Exemplo.docx")
    build_metric_contract(reference, ROOT / "docs" / "gov" / "metric_contracts.docx")
    build_main_document(ROOT / "docs" / "gov" / "challenge_sprint3_gov.docx")
    print("Documentos GOV gerados.")
