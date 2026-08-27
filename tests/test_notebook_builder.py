from src.build_sprint3_notebook import build_notebook


def test_notebook_covers_all_deliverables_and_executes_real_pipeline():
    notebook = build_notebook()
    markdown = "\n".join(
        cell.source for cell in notebook.cells if cell.cell_type == "markdown"
    )
    code = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code")

    for number in range(1, 13):
        assert f"## {number}." in markdown
    assert "run_pipeline(save_artifacts=False)" in code
    assert "build_agent_payload" in code
    assert len([cell for cell in notebook.cells if cell.cell_type == "code"]) >= 8


def test_every_code_cell_is_valid_python():
    notebook = build_notebook()

    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            compile(cell.source, f"notebook-cell-{index}", "exec")
