import streamlit as st
import pandas as pd
from collections import Counter
import re

st.set_page_config(page_title="Extrator de Blockers", page_icon="🛡️", layout="wide")

st.title("🛡️ Extrator de Blockers")

uploaded_file = st.file_uploader("Suba o arquivo CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        df = pd.read_csv(uploaded_file, encoding='latin1')
    
    col = st.selectbox("Selecione a coluna com o título do produto", df.columns)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        termo_alvo = st.text_input("Termo Principal (ex: Máquina de Costura):", "")
    with col2:
        sinonimos_input = st.text_input("Sinônimos/Validadores (ex: doméstica, overlock):", "")
    with col3:
        excecoes_input = st.text_input("Bloquear se for peça (ex: agulha, cabo):", "")

    if termo_alvo:
        # Prepara a lista de termos que "Validam" o produto (Principal + Sinônimos)
        lista_validos = [termo_alvo.strip()] + [s.strip() for s in sinonimos_input.split(",") if s.strip()]
        regex_validos = '|'.join(lista_validos)
        
        # 1. Tudo que NÃO contém nenhum dos termos válidos é BLOCKER DIRETO
        mask_validos = df[col].str.contains(regex_validos, case=False, na=False)
        df_obvios = df[~mask_validos].copy()
        
        # 2. Itens que são válidos, mas podem ser PEÇAS (falsos positivos)
        df_potenciais_acertos = df[mask_validos].copy()

        # --- SUGESTÃO DE TERMOS (Inteligência de Dados) ---
        todas_as_palavras = " ".join(df_potenciais_acertos[col].astype(str)).lower()
        palavras = re.findall(r'\w+', todas_as_palavras)
        # Lista de Stop Words (Palavras que não agregam valor à análise)
        stop_words = [
            'para', 'com', 'pelo', 'pela', 'mais', 'esta', 'essa', 'este', 'esse',
            'sem', 'nos', 'nas', 'dos', 'das', 'uma', 'uns', 'umas', 'sob', 'sobre',
            'entre', 'através', 'cada', 'qual', 'quais', 'quem', 'cujo', 'cuja',
            'tudo', 'nada', 'algum', 'alguma', 'alguns', 'algumas', 'toda', 'todo',
            'todas', 'todos', 'outra', 'outro', 'outras', 'outros', 'muito', 'muita',
            'pode']
        palavras_filtradas = [w for w in palavras if len(w) > 3 and w not in stop_words and not any(v.lower() in w for v in lista_validos)]
        
        contagem = Counter(palavras_filtradas).most_common(10)
        
        st.info("💡 **Análise de Padrões:** Palavras frequentes nos itens validados. Alguma indica uma peça?")
        sugestoes_botoes = st.columns(len(contagem))
        for i, (palavra, freq) in enumerate(contagem):
            sugestoes_botoes[i].code(f"{palavra}")

        if st.button("🚀 Gerar Lista de Blockers"):
            # Filtra peças dentro dos itens que seriam "bons"
            lista_excecoes = [t.strip() for t in excecoes_input.split(",") if t.strip()]
            
            if lista_excecoes:
                regex_excecoes = '|'.join(lista_excecoes)
                mask_excecoes = df_potenciais_acertos[col].str.contains(regex_excecoes, case=False, na=False)
                df_pecas = df_potenciais_acertos[mask_excecoes]
            else:
                df_pecas = pd.DataFrame()

            # Resultado Final: O que não tinha o nome + o que tinha o nome mas era peça
            df_final = pd.concat([df_obvios, df_pecas])
            df_final['blocker'] = df_final[col].str.lower()
            resultado = df_final[['blocker']].drop_duplicates()

            st.success(f"✅ {len(resultado)} blockers únicos identificados.")
            st.dataframe(resultado)

            csv = resultado.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV de Blockers", csv, "blockers_ia_v3.csv", "text/csv")


