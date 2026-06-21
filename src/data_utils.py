"""Utilidades de carga de dados do motor.db — Sprint 2 GenAI (Challenge Forzy).

Centraliza o acesso ao banco e as constantes do problema, para que os notebooks
(EDA, treinamento) e o agente compartilhem a mesma fonte de verdade.
"""
from pathlib import Path
import sqlite3
import pandas as pd

# motor.db: cópia local em genai/sprint2/data/ (pacote autônomo); este arquivo em .../src/
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "motor.db"

# Contrato de features do modelo == assinatura da tool do agente (leituras instantâneas).
FEATURES = ["rotacao_rpm", "vibracao_mm_s", "temperatura_c", "corrente_a"]
TARGET = "falha"
TIPOS_FALHA = {
    0: "Normal",
    1: "Desbalanceamento",
    2: "Superaquecimento",
    3: "Falha mecânica",
}


def load_leituras(db_path: Path = DB_PATH, join_motores: bool = True) -> pd.DataFrame:
    """Carrega a tabela `leituras` ordenada por (motor_id, timestamp).

    Com join_motores, anexa o cadastro (fabricante, modelo, potencia_kw, ano).
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"motor.db não encontrado em {db_path}")
    con = sqlite3.connect(db_path)
    try:
        if join_motores:
            query = """
                SELECT l.*, m.fabricante, m.modelo, m.potencia_kw, m.ano_instalacao
                FROM leituras l
                JOIN motores m ON m.motor_id = l.motor_id
                ORDER BY l.motor_id, l.timestamp
            """
        else:
            query = "SELECT * FROM leituras ORDER BY motor_id, timestamp"
        return pd.read_sql_query(query, con, parse_dates=["timestamp"])
    finally:
        con.close()


def load_tabela(nome: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    """Carrega uma tabela inteira (`motores`, `leituras`, `tipos_falha`)."""
    con = sqlite3.connect(Path(db_path))
    try:
        return pd.read_sql_query(f"SELECT * FROM {nome}", con)
    finally:
        con.close()
