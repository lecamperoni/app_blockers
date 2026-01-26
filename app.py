import streamlit as st
import pandas as pd

st.set_page_config(page_title="Blockers", page_icon="🛡️")

st.title("🛡️ Extrator de Blockers")
st.markdown("Transforme descrições de produtos em listas de blockers formatadas.")

uploaded_file = st.file_uploader("CSV nomes", type=["csv"])

if uploaded_file:
    # Tenta ler o CSV (tratando possíveis problemas de encoding comuns em Excel)
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        df = pd.read_csv(uploaded_file, encoding='latin1')
    
    coluna = st.selectbox("Qual coluna contém a descrição do produto?", df.columns)
    termo_bom = st.text_input("Manter produtos que contenham:", "Costura")

    if st.button("Processar e Gerar Lista"):
        # Filtra o que NÃO contém o termo correto (ex: máquinas de gelo, lavar, etc)
        mask = ~df[coluna].str.contains(termo_bom, case=False, na=False)
        intrusos = df[mask].copy()

        # Aplica suas regras: minúsculas e remoção de duplicatas
        intrusos['blocker'] = intrusos[coluna].str.lower()
        lista_final = intrusos[['blocker']].drop_duplicates()

        st.success(f"✅ {len(lista_final)} blockers identificados!")
        st.dataframe(lista_final)

        # Prepara o download
        csv = lista_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV", csv, "blockers_prontos.csv", "text/csv")