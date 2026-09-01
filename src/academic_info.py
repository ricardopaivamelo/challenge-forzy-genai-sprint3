"""Identificação acadêmica compartilhada pelos artefatos da Sprint 3."""

from __future__ import annotations


DISCIPLINE = "Generative AI & Advanced Nets"
PROFESSOR = "Mateus Azevedo Dalbone"
TEAM = (
    ("Nicolas Lemos Ribeiro", "553273"),
    ("Ricardo de Paiva Melo", "565522"),
    ("Luís Fernando de Oliveira Salgado", "561401"),
    ("Pedro Leal Murad", "565460"),
    ("Murilo Benhossi", "562358"),
    ("Jonas Alaf", "566479"),
)


def academic_markdown(heading_level: int = 2) -> str:
    """Renderiza professor e integrantes em Markdown acadêmico."""

    heading = "#" * heading_level
    members = "\n".join(f"- {name} — RM {rm}" for name, rm in TEAM)
    return (
        f"{heading} Identificação acadêmica\n\n"
        f"**Disciplina:** {DISCIPLINE}\n\n"
        f"**Professor:** {PROFESSOR}\n\n"
        f"{heading}# Integrantes\n\n"
        f"{members}"
    )
