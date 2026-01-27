import streamlit as st
import pandas as pd
from collections import Counter
import re

st.set_page_config(page_title="Extrator de Blockers", page_icon="🛡️", layout="wide")

st.title("🛡️ Extrator de Blockers com Sugestão de Termos")
st.markdown("Filtre intrusos e identifique padrões de peças/acessórios automaticamente.")

uploaded_file = st.file_uploader("Suba o arquivo CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        df = pd.read_csv(uploaded_file, encoding='latin1')
    
    col = st.selectbox("Selecione a coluna com o título do produto", df.columns)
    
    col1, col2 = st.columns(2)
    with col1:
        termo_alvo = st.text_input("Produto que você quer MANTER (ex: Notebook, Furadeira):", "")
    with col2:
        excecoes_input = st.text_input("Termos para BLOQUEAR (peças/acessórios), separados por vírgula:", "")

    if termo_alvo:
        # 1. Identifica o que contém o termo alvo (Potenciais acertos e peças)
        df_alvo = df[df[col].str.contains(termo_alvo, case=False, na=False)].copy()
        
        # 2. Identifica o que NÃO contém o termo alvo (Blockers óbvios)
        df_obvios = df[~df[col].str.contains(termo_alvo, case=False, na=False)].copy()

        # --- FUNÇÃO DE SUGESTÃO (INTELIGÊNCIA) ---
        # Analisa as palavras mais comuns nos produtos que contêm o termo alvo
        # para te ajudar a achar palavras como "agulha", "cabo", "carregador", etc.
        todas_as_palavras = " ".join(df_alvo[col].astype(str)).lower()
        palavras = re.findall(r'\w+', todas_as_palavras)
        
        # Filtra palavras irrelevantes (stop words simples) e o próprio termo alvo
        palavras_filtradas = [w for w in palavras if len(w) > 3 and w not in termo_alvo.lower()]
        contagem = Counter(palavras_filtradas).most_common(10)
        
        st.info("💡 **Sugestão de Termos:** As palavras abaixo aparecem muito com seu produto principal. "
                "Alguma delas indica uma peça ou acessório que deve ser bloqueado?")
        
        sugestoes_botoes = st.columns(len(contagem))
        for i, (palavra, freq) in enumerate(contagem):
            sugestoes_botoes[i].code(f"{palavra}")

        # --- EXECUÇÃO DO FILTRO ---
        if st.button("Gerar Lista Final de Blockers"):
            # Processa a lista de exceções
            lista_excecoes = [t.strip() for t in excecoes_input.split(",") if t.strip()]
            
            if lista_excecoes:
                regex_excecoes = '|'.join(lista_excecoes)
                mask_excecoes = df_alvo[col].str.contains(regex_excecoes, case=False, na=False)
                df_pecas = df_alvo[mask_excecoes]
            else:
                df_pecas = pd.DataFrame()

            # Une blockers óbvios (sem o nome) + peças (com o nome mas na lista de exceção)
            df_final = pd.concat([df_obvios, df_pecas])
            df_final['blocker'] = df_final[col].str.lower()
            resultado = df_final[['blocker']].drop_duplicates()

            st.success(f"✅ Processamento concluído: {len(resultado)} blockers únicos encontrados.")
            st.dataframe(resultado)

            csv = resultado.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV de Blockers", csv, "blockers_ia.csv", "text/csv")
