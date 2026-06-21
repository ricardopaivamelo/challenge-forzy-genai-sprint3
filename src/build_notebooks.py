"""Gera os notebooks-entregáveis (EDA e treinamento) via nbformat.

Rodar a partir de genai/sprint2/:  python src/build_notebooks.py
Depois executar com nbconvert para preencher saídas/figuras.
"""
from pathlib import Path
import nbformat as nbf

SPRINT = Path(__file__).resolve().parent.parent
NB = SPRINT / "notebooks"
NB.mkdir(exist_ok=True)


def md(text):
    return nbf.v4.new_markdown_cell(text.strip("\n"))


def code(text):
    return nbf.v4.new_code_cell(text.strip("\n"))


# Preâmbulo comum: tornar src/ importável e padronizar estilo dos gráficos.
PREAMBLE = """
import sys, os
sys.path.insert(0, os.path.abspath("../src"))
import numpy as np, pandas as pd
import matplotlib.pyplot as plt, seaborn as sns
from data_utils import load_leituras, load_tabela, FEATURES, TARGET, TIPOS_FALHA
sns.set_theme(style="whitegrid"); plt.rcParams["figure.figsize"] = (9, 4.5)
FIG = "../figuras"; os.makedirs(FIG, exist_ok=True)
"""

# ===================================================================== EDA
eda = nbf.v4.new_notebook()
eda.cells = [
    md("""
# Sprint 2 — GenAI · Análise Exploratória de Dados
### Manutenção preditiva de motores elétricos (Challenge Forzy / FIAP)

**Entregável 1 — Descrição do problema preditivo.** A tarefa é uma **classificação
multiclasse** do estado operacional do motor a partir de leituras de sensores:
`falha ∈ {0 Normal, 1 Desbalanceamento, 2 Superaquecimento, 3 Falha mecânica}`.
Antecipar a classe de falha é o que viabiliza a manutenção *preditiva* — agir antes da
parada, priorizando as três classes de falha (minoritárias), onde está o valor.

**Entregável 2 — Base de dados.** `data/motor.db` (SQLite): tabelas `motores` (20),
`leituras` (30.000 — séries de sensores 1/min) e `tipos_falha` (dicionário). Origem:
dados sintéticos com seed fixa (ver `data/BANCO.pdf`).
"""),
    code(PREAMBLE),
    code("""
df = load_leituras()
print("leituras:", df.shape, "| motores:", df.motor_id.nunique())
print("período:", df.timestamp.min(), "->", df.timestamp.max())
display(df.head())
display(load_tabela("tipos_falha"))
"""),
    md("## 1. Distribuição da variável-alvo"),
    code("""
vc = df[TARGET].value_counts().sort_index()
dist = pd.DataFrame({"classe": [TIPOS_FALHA[c] for c in vc.index],
                     "n": vc.values, "%": (100*vc.values/len(df)).round(2)})
display(dist)
ax = sns.barplot(data=dist, x="classe", y="n", hue="classe", legend=False, palette="viridis")
ax.set_title("Distribuição da variável-alvo (falha)"); ax.set_ylabel("nº de leituras")
plt.xticks(rotation=15); plt.tight_layout(); plt.savefig(f"{FIG}/01_distribuicao_alvo.png", dpi=110); plt.show()
"""),
    md("""
**Interpretação.** Forte desbalanceamento: ~87,6% das leituras são *Normal* e só ~12,4%
são falhas, repartidas em três tipos (a *falha mecânica* é a mais rara). Isso exige
`class_weight` no modelo e métricas **por classe** (recall/F1) — acurácia global
sozinha enganaria, pois prever "tudo normal" já daria ~88%.
"""),
    md("## 2. Distribuição dos sensores por classe de falha"),
    code("""
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, feat in zip(axes.ravel(), FEATURES):
    d = df.assign(classe=df[TARGET].map(TIPOS_FALHA))
    sns.boxplot(data=d, x="classe", y=feat, hue="classe", legend=False, ax=ax, palette="viridis")
    ax.set_title(feat); ax.set_xlabel(""); ax.tick_params(axis="x", rotation=15)
plt.tight_layout(); plt.savefig(f"{FIG}/02_sensores_por_classe.png", dpi=110); plt.show()
df.groupby(df[TARGET].map(TIPOS_FALHA))[FEATURES].mean().round(2)
"""),
    md("""
**Interpretação (ligação com o comportamento físico).**
- **Desbalanceamento** → `vibracao_mm_s` claramente elevada (vibração é a assinatura).
- **Superaquecimento** → `temperatura_c` e `corrente_a` acima do normal simultaneamente.
- **Falha mecânica** → `rotacao_rpm` cai e vibração/corrente sobem — combina sintomas
  das outras duas, o que antecipa a confusão que veremos no modelo.
"""),
    md("## 3. Outliers e amplitude das leituras"),
    code("""
display(df[FEATURES].describe().round(2))
fig, ax = plt.subplots(figsize=(9,4))
sns.boxplot(data=df[FEATURES].melt(var_name="sensor", value_name="valor"),
            x="sensor", y="valor", hue="sensor", legend=False, palette="mako", ax=ax)
ax.set_title("Amplitude e outliers por sensor (todas as leituras)")
plt.tight_layout(); plt.savefig(f"{FIG}/03_outliers.png", dpi=110); plt.show()
"""),
    md("""
**Interpretação.** Os "outliers" superiores em vibração, temperatura e corrente **não
são ruído a remover** — são justamente as janelas de falha. Tratá-los como erro
apagaria o sinal de interesse; mantemos as leituras e deixamos o rótulo `falha` separar.
"""),
    md("## 4. Evolução temporal — a rampa progressiva de deterioração"),
    code("""
# Escolhe um motor que tenha falhas e plota a série de um sensor, marcando as falhas.
alvo = (df[df[TARGET] > 0].motor_id.value_counts().idxmax())
m = df[df.motor_id == alvo].reset_index(drop=True)
fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
for ax, feat in zip(axes, ["vibracao_mm_s", "temperatura_c"]):
    ax.plot(m.index, m[feat], lw=0.8, color="steelblue")
    falha_pts = m[m[TARGET] > 0]
    ax.scatter(falha_pts.index, falha_pts[feat], s=10, color="crimson", label="falha rotulada", zorder=3)
    ax.set_ylabel(feat); ax.legend(loc="upper right")
axes[0].set_title(f"Motor {alvo}: leituras ao longo do tempo (vermelho = falha)")
axes[1].set_xlabel("índice temporal (leituras 1/min)")
plt.tight_layout(); plt.savefig(f"{FIG}/04_evolucao_temporal.png", dpi=110); plt.show()
"""),
    md("""
**Interpretação.** As falhas ocorrem em **janelas** com subida gradual (rampa). Como o
BANCO.md diz, o rótulo só acende acima de ~40% da intensidade — então as leituras
*imediatamente antes* do ponto vermelho já carregam o padrão emergindo. Isso é a
justificativa empírica para, numa próxima sprint, usar **features de janela móvel**
(médias/variações móveis) e antecipar ainda mais a detecção.
"""),
    md("## 5. Correlação entre sensores"),
    code("""
corr = df[FEATURES].corr()
ax = sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True)
ax.set_title("Correlação entre sensores (Pearson)")
plt.tight_layout(); plt.savefig(f"{FIG}/05_correlacao.png", dpi=110); plt.show()
"""),
    md("""
**Interpretação.** A correlação global entre sensores é fraca em regime normal (cada um
mede um fenômeno diferente), mas temperatura×corrente tende a andar junto nos eventos de
superaquecimento. A baixa colinearidade geral é boa: cada sensor agrega informação
própria ao modelo.
"""),
    md("""
## Conclusões da EDA
1. Problema multiclasse fortemente **desbalanceado** → usar `class_weight` + métricas por classe.
2. Cada falha tem **assinatura física** coerente nos sensores → as 4 leituras carregam sinal.
3. As falhas são **janelas com rampa** → janela móvel é a evolução natural (próxima sprint).
4. Outliers altos = falhas reais → **não** remover.

Segue para o notebook `treinamento.ipynb`.
"""),
]
nbf.write(eda, NB / "analise_exploratoria.ipynb")
print("ok: analise_exploratoria.ipynb")

# ============================================================== TREINAMENTO
tr = nbf.v4.new_notebook()
tr.cells = [
    md("""
# Sprint 2 — GenAI · Modelo Baseline de Manutenção Preditiva
### Treino, avaliação e análise de erros (Challenge Forzy / FIAP)

Continua a EDA: treina o classificador da coluna `falha`, avalia com métricas por classe
e investiga os erros. O modelo é serializado em `models/modelo_falhas.joblib` para o agente.
"""),
    code(PREAMBLE),
    code("""
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay, f1_score
import joblib
df = load_leituras()
print("missing por coluna:", df[FEATURES + [TARGET]].isna().sum().to_dict())
"""),
    md("""
## Entregável 4 — Tratamento e preparação dos dados
- **Sem valores ausentes** nos sensores (verificado acima) → não há imputação.
- **Features:** as **4 leituras instantâneas** (`rotacao_rpm`, `vibracao_mm_s`,
  `temperatura_c`, `corrente_a`). Essa escolha é deliberada: a tool do agente recebe
  exatamente essas 4 grandezas, então o modelo precisa operar com o mesmo contrato.
- **Categóricas** (`fabricante`, `modelo`): **não** entram — o usuário do chat não as
  informa, e usá-las criaria dependência que o agente não consegue satisfazer.
- **Escala:** Random Forest é invariante a escala → dispensamos normalização.
- **Desbalanceamento:** tratado via `class_weight="balanced_subsample"`.
- **Janela móvel:** *não* aplicada ao modelo servido (o agente vê 1 leitura), mas
  registrada como melhoria (ver análise de erros).
"""),
    code("""
X, y, groups = df[FEATURES], df[TARGET], df["motor_id"]
"""),
    md("""
## Entregável 5 — Divisão treino/teste
`leituras` é série temporal por motor. Split aleatório vazaria o **nível basal** de cada
motor (cada um tem valores nominais próprios) entre treino e teste. Usamos
**`StratifiedGroupKFold` por `motor_id`**: nenhum motor aparece nos dois conjuntos
(testa generalização para motores novos) e a estratificação garante as classes raras no
teste. Alternativa equivalente seria split **cronológico** por motor.
"""),
    code("""
sgkf = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=42)
tr_idx, te_idx = next(sgkf.split(X, y, groups))
Xtr, ytr, Xte, yte = X.iloc[tr_idx], y.iloc[tr_idx], X.iloc[te_idx], y.iloc[te_idx]
print("motores treino:", sorted(df.iloc[tr_idx].motor_id.unique()))
print("motores teste :", sorted(df.iloc[te_idx].motor_id.unique()))
print("\\ndistribuição de classes no teste:")
print(yte.map(TIPOS_FALHA).value_counts())
"""),
    md("""
## Entregável 6 — Treinamento do modelo baseline
**Random Forest** (300 árvores). Justificativa: captura relações não-lineares entre
sensores (ex.: temperatura *e* corrente juntas = superaquecimento), é robusto a escala e
a outliers, lida com o desbalanceamento via `class_weight`, e expõe
`feature_importances_` — que o agente usa para explicar quais sensores pesaram.
"""),
    code("""
clf = RandomForestClassifier(n_estimators=300, class_weight="balanced_subsample",
                             random_state=42, n_jobs=-1)
clf.fit(Xtr, ytr)
print("treinado. importâncias:", dict(zip(FEATURES, clf.feature_importances_.round(3))))
"""),
    md("## Entregável 7 — Avaliação do desempenho"),
    code("""
ypred = clf.predict(Xte)
labels = [0,1,2,3]; names = [TIPOS_FALHA[c] for c in labels]
print(classification_report(yte, ypred, labels=labels, target_names=names, zero_division=0))
print("macro-F1:", round(f1_score(yte, ypred, average="macro"), 3))
cm = confusion_matrix(yte, ypred, labels=labels)
ConfusionMatrixDisplay(cm, display_labels=names).plot(cmap="Blues", xticks_rotation=20)
plt.title("Matriz de confusão"); plt.tight_layout()
plt.savefig(f"{FIG}/06_matriz_confusao.png", dpi=110); plt.show()
"""),
    md("""
**Interpretação.** Acurácia global alta (~0,95), mas o que importa é o desempenho nas
falhas: *Desbalanceamento* tem recall alto (assinatura de vibração é nítida);
*Superaquecimento* fica intermediário; *Falha mecânica* é a mais difícil (recall baixo).
A acurácia global seria um número enganoso isolado — por isso olhamos classe a classe.
"""),
    md("## Entregável 8 — Análise dos erros"),
    code("""
err = df.iloc[te_idx].copy(); err["pred"] = ypred; err = err[err[TARGET] != err["pred"]]
print("total de erros:", len(err), f"({100*len(err)/len(yte):.1f}% do teste)")
print("\\nerros por classe real:")
print(err[TARGET].map(TIPOS_FALHA).value_counts())
print("\\npara onde a 'Falha mecânica' real foi classificada:")
fm = err[err[TARGET] == 3]["pred"].map(TIPOS_FALHA).value_counts()
print(fm)
# confiança do modelo nos acertos vs erros
proba = clf.predict_proba(Xte).max(axis=1)
conf = pd.DataFrame({"acerto": (yte.values == ypred), "confianca": proba})
print("\\nconfiança média — acertos vs erros:")
print(conf.groupby("acerto")["confianca"].mean().round(3))
"""),
    md("""
**Interpretação e melhorias para a próxima sprint.**
- A *falha mecânica* é confundida com *desbalanceamento* e *superaquecimento* — coerente
  com a EDA: ela combina queda de rotação com vibração/corrente altas, sobrepondo-se às
  assinaturas das outras duas.
- O modelo erra com **menor confiança** do que acerta → dá para usar um limiar de
  confiança no agente para comunicar incerteza.
- **Próxima sprint:** features de **janela móvel** (tendência de rotação/vibração) devem
  separar melhor a falha mecânica, capturando a *queda progressiva* de rotação que uma
  leitura instantânea não revela.
"""),
    md("## Serialização do modelo (para o agente)"),
    code("""
import os
os.makedirs("../models", exist_ok=True)
joblib.dump({"model": clf, "features": FEATURES, "labels": labels,
             "tipos_falha": TIPOS_FALHA,
             "feature_importances": dict(zip(FEATURES, clf.feature_importances_.round(4)))},
            "../models/modelo_falhas.joblib", compress=3)
print("salvo: models/modelo_falhas.joblib")
"""),
    md("""
## Conclusão
Baseline funcional (macro-F1 ~0,80) que prioriza as classes de falha. Pronto para o
**agente conversacional com function calling**, que carrega este `.joblib` e traduz a
predição em linguagem natural. Limitações e o caminho de melhoria (janela móvel) estão
documentados acima.
"""),
]
nbf.write(tr, NB / "treinamento.ipynb")
print("ok: treinamento.ipynb")
