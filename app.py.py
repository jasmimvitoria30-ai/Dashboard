#importar bibliotecas
from pathlib import Path
import streamlit as st
import pandas as pd

#Ler os arquivos Excel da pasta e concatenar em um único DataFrame
pasta = Path("dados")

arquivos = pasta.glob("*.xlsx")

#Extrair o códigodo projeto do nome do arquivo e criar uma coluna "Projeto" no DataFrame
dataframes = []

for arquivo in arquivos:
    df = pd.read_excel(arquivo)
    
    # Aqui entra a lógica do projeto
    df["Projeto"] = arquivo.stem  # ex: "Projeto 308"
    
    dataframes.append(df)

tabela = pd.concat(dataframes, ignore_index=True)


# título
st.title("Acompanhamento de Projetos de Arrecadação")

# Garantir que a coluna é datetime
tabela["Data Pag."] = pd.to_datetime(tabela["Data Pag."], dayfirst=True)

# Criar colunas auxiliares
tabela["Ano"] = tabela["Data Pag."].dt.year
tabela["Mes"] = tabela["Data Pag."].dt.month

# campo de seleção PROJETO (novo)
projeto = st.multiselect(
    "Selecione o projeto:",
    options=sorted(tabela["Projeto"].unique()),
    default=sorted(tabela["Projeto"].unique())
)

# campo de seleção ANO
ano = st.multiselect(
    "Selecione o ano:",
    options=sorted(tabela["Ano"].unique()),
    default=sorted(tabela["Ano"].unique())
)

# campo de seleção MES
mes = st.multiselect(
    "Selecione o mês:",
    options=sorted(tabela["Mes"].unique()),
    default=sorted(tabela["Mes"].unique())
)

# aplicar filtros
tabela_filtrada = tabela[
    (tabela["Projeto"].isin(projeto)) &
    (tabela["Ano"].isin(ano)) &
    (tabela["Mes"].isin(mes))
]

######### Métricas
# 1 - Entradas
# filtra apenas a rubrica de entradas
filtro_entradas = tabela_filtrada[tabela_filtrada["Rubrica"].isin(["Receitas","Rendimentos de Aplicações Financeiras"])]
# calcula o valor total de entradas
entradas = filtro_entradas["Crédito"].sum() + filtro_entradas["Débito"].sum()
# exibe no dashboard
st.metric("Entrada de Recursos", f"R$ {entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 2- Saídas
st.metric("Saída de Recursos", f"R$ {-tabela_filtrada['Débito'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 3 - Rendimentos
# filtra apenas a rubrica de rendimento
filtro_rendimento = tabela_filtrada[tabela_filtrada["Rubrica"] == "Rendimentos de Aplicações Financeiras"]
# calcula o valor
rendimento = filtro_rendimento["Crédito"].sum() + filtro_rendimento["Débito"].sum()
# exibe no dashboard
st.metric("Rendimentos", f"R$ {rendimento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 4 - Bolsas
# filtra apenas a rubrica de bolsa
bolsas = tabela_filtrada[tabela_filtrada["Rubrica"] == "Bolsas"]
# calcula o valor
bolsas = -bolsas["Débito"].sum()
# exibe no dashboard
st.metric("Bolsas", f"R$ {bolsas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 5 - Serviços de terceiros
# filtra apenas a rubrica de serviços de terceiros
servicos = tabela_filtrada[tabela_filtrada["Rubrica"] == "Serviços de Terceiros Pessoa Jurídica"]
# calcula o valor
servicos_valor = -servicos["Débito"].sum()
# exibe no dashboard
st.metric("Serviços de Terceiros – Pessoa Jurídica", f"R$ {servicos_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 6 - DESPESAS OPERACIONAIS ADMINISTRATIVAS

# Passo 1: Padronização
tabela_filtrada["Projeto"] = (
    tabela_filtrada["Projeto"]
    .astype(str)
    .str.replace("Projeto", "", regex=False)
    .str.replace(".0", "", regex=False)
    .str.strip()
)

tabela_filtrada["Rubrica"] = (
    tabela_filtrada["Rubrica"]
    .astype(str)
    .str.strip()
    .str.lower()
)

tabela_filtrada["Tipo"] = (
    tabela_filtrada["Tipo"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Passo 2: Padronizar seleção do multiselect
projeto = [str(p).replace("Projeto", "").replace(".0", "").strip() for p in projeto]

# Psso 3: Definir o percentual de despesas operacionais administrativas
percentual = {
    "308": 0.15,
    "318": 0.10,
    "331": 0.10,
    "335": 0.15,
    "339": 0.15,
    "363": 0.10,
    "374": 0.15,
    "456": 0.15,
    "457": 0.15,
    "458": 0.13,
    "459": 0.12,
    "494": 0.15,
    "518": 0.15,
    "570": 0.13,
    "571": 0.15,
    "595": 0.15,
    "598": 0.15
}

# Passo 4: Calcular
doas_total = 0

for proj in projeto:
    
    df_proj = tabela_filtrada[tabela_filtrada["Projeto"] == proj]
    
    # -------- streamlit run Codigos.pytado (por projeto) --------
    filtro_receitas = df_proj["Rubrica"].str.contains("receit", na=False)
    filtro_transferencia = df_proj["Tipo"].str.contains("transfer", na=False)
    
    executado_proj = (
        df_proj.loc[filtro_receitas, "Crédito"].sum()
        + df_proj.loc[filtro_receitas, "Débito"].sum()
        - df_proj.loc[filtro_transferencia, "Crédito"].sum()
    )
    
    # -------- Taxa --------
    taxa = percentual.get(proj, 0)
    
    # -------- Cálculo DOA --------
    doas_total += executado_proj * taxa

#Passo 5: Exibir
st.metric("DOA's",f"R$ {doas_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 7 - RESSARCIMENTO UFMS
# Passo 1: Bolsas alunos ###### melhorar depois, pois pode ser que o valor seja diferente de -700, ou seja, pode variar conforme o projeto
bolsas_alunos = tabela_filtrada[tabela_filtrada["Débito"] == -700]["Débito"].sum()

# Passo 2: Calcular o ressarcimento
ressarcimento = (bolsas + servicos_valor + bolsas_alunos) * 0.1

# exibe no dashboard
st.metric("Ressarcimento UFMS", f"R$ {ressarcimento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 8 - Material Permanente
# filtra apenas a rubrica de material permanente
material_permanente = tabela_filtrada[tabela_filtrada["Rubrica"] == "Equipamento e Material Permanente"]
# calcula o valor
material_permanente = material_permanente["Débito"].sum()
# exibe no dashboard
st.metric("Equipamento e Material Permanente", f"R$ {material_permanente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 9 - Saldo
# Calcular mensalidade
mensalidades_total = 0

for proj in projeto:
    
    df_proj = tabela_filtrada[tabela_filtrada["Projeto"] == proj]
    
    filtro_receitas = df_proj["Rubrica"].str.contains("receit", na=False)
    filtro_transferencia = df_proj["Tipo"].str.contains("transfer", na=False)
    
    mensal_proj = (
        df_proj.loc[filtro_receitas, "Crédito"].sum()
        + df_proj.loc[filtro_receitas, "Débito"].sum()
        - df_proj.loc[filtro_transferencia, "Crédito"].sum()
    )
    
    mensalidades_total += mensal_proj

#Calcular o saldo
saldo = (
    mensalidades_total
    - doas_total
    - servicos_valor
    - bolsas
    - ressarcimento
    - material_permanente
)
st.metric("Saldo", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# Gráfico entradas
#st.bar_chart(tabela_filtrada.groupby("Mes")["Crédito"].sum())

# Gráfico saídas
#st.bar_chart(tabela_filtrada.groupby("Mes")["Débito"].sum())

## GRÁFICOS
# criar coluna Ano-Mês
tabela_filtrada["AnoMes"] = tabela_filtrada["Data Pag."].dt.to_period("M").astype(str)

# agrupar
entradasg = (
    tabela_filtrada
    .groupby("AnoMes")["Crédito"]
    .sum()
    .sort_index()
)
# gráfico entradas
st.bar_chart(entradasg)

# agrupar
saidasg = (
    tabela_filtrada
    .groupby("AnoMes")["Débito"]
    .sum()
    .sort_index()
)
# gráfico saídas
st.bar_chart(saidasg)
