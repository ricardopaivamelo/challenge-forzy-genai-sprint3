from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn

from scripts.build_gov_documents import build_main_document


def test_main_document_builder_creates_valid_docx(tmp_path):
    output = tmp_path / "challenge_sprint3_gov.docx"

    build_main_document(output)

    assert output.stat().st_size > 100_000
    with ZipFile(output) as package:
        assert "word/document.xml" in package.namelist()
        document_xml = package.read("word/document.xml").decode("utf-8")

    forbidden_markers = (
        "PREENCHIMENTO OBRIGATÓRIO PELO GRUPO",
        "SEÇÃO AUTORAL — NÃO PREENCHIDA POR IA",
        "[PREENCHER]",
        "[ESCREVER AQUI]",
    )
    assert all(marker not in document_xml for marker in forbidden_markers)


def test_supervision_matrix_uses_landscape_and_keeps_scenarios_together(tmp_path):
    output = tmp_path / "challenge_sprint3_gov.docx"

    build_main_document(output)

    document = Document(output)
    assert any(section.page_width > section.page_height for section in document.sections)

    matrix = next(table for table in document.tables if len(table.columns) == 7)
    assert all(
        cell._tc.get_or_add_tcPr().find(qn("w:noWrap")) is None
        for cell in matrix.rows[0].cells
    )
    assert all(
        row._tr.get_or_add_trPr().find(qn("w:cantSplit")) is not None
        for row in matrix.rows[1:]
    )
    assert all(
        paragraph.paragraph_format.first_line_indent == 0
        for row in matrix.rows
        for cell in row.cells
        for paragraph in cell.paragraphs
    )


def test_final_considerations_start_on_a_new_page(tmp_path):
    output = tmp_path / "challenge_sprint3_gov.docx"

    build_main_document(output)

    document = Document(output)
    heading_index = next(
        index
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.text == "7 CONSIDERAÇÕES FINAIS"
    )
    previous_paragraph_xml = document.paragraphs[heading_index - 1]._p.xml
    assert 'w:type="page"' in previous_paragraph_xml


def test_living_document_preserves_detailed_sprint_1_controls(tmp_path):
    output = tmp_path / "challenge_sprint3_gov.docx"

    build_main_document(output)

    document = Document(output)
    text = "\n".join(
        [paragraph.text for paragraph in document.paragraphs]
        + [cell.text for table in document.tables for row in table.rows for cell in row.cells]
    )

    for required_control in (
        "Técnico de Operação",
        "photo_file_hash",
        "cv_model_version",
        "fields_low_confidence",
        "Viés de Marca",
        "Model Card",
    ):
        assert required_control in text


def test_page_number_is_hidden_from_cover_and_pretextual_pages(tmp_path):
    output = tmp_path / "challenge_sprint3_gov.docx"

    build_main_document(output)

    document = Document(output)
    assert "PAGE" not in document.sections[0].footer._element.xml
    assert "PAGE" not in document.sections[1].footer._element.xml

    textual_section = document.sections[2]
    assert "PAGE" in textual_section.footer._element.xml
    page_number_type = textual_section._sectPr.find(qn("w:pgNumType"))
    assert page_number_type is not None
    assert page_number_type.get(qn("w:start")) == "4"
    assert all(
        section._sectPr.find(qn("w:pgNumType")) is None
        for section in document.sections[3:]
    )
