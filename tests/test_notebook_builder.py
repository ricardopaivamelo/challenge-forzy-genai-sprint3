from pathlib import Path
import shutil
import subprocess
import sys

from src.build_sprint3_notebook import build_notebook


ROOT = Path(__file__).resolve().parents[1]
ACADEMIC_IDENTIFICATION = (
    "Mateus Azevedo Dalbone",
    "Nicolas Lemos Ribeiro — RM 553273",
    "Ricardo de Paiva Melo — RM 565522",
    "Luís Fernando de Oliveira Salgado — RM 561401",
    "Pedro Leal Murad — RM 565460",
    "Murilo Benhossi — RM 562358",
    "Jonas Alaf — RM 566479",
)


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


def test_notebook_identifies_professor_and_team():
    notebook = build_notebook()
    markdown = "\n".join(
        cell.source for cell in notebook.cells if cell.cell_type == "markdown"
    )

    for expected in ACADEMIC_IDENTIFICATION:
        assert expected in markdown


def test_every_code_cell_is_valid_python():
    notebook = build_notebook()

    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            compile(cell.source, f"notebook-cell-{index}", "exec")


def test_notebook_builder_runs_as_documented_script(tmp_path):
    shutil.copytree(ROOT / "src", tmp_path / "src")
    completed = subprocess.run(
        [sys.executable, "src/build_sprint3_notebook.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Notebook gerado em" in completed.stdout
    assert (tmp_path / "notebooks" / "sprint3_anomalias.ipynb").exists()
