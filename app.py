import streamlit as st
import pandas as pd
from collections import Counter
import re

st.set_page_config(page_title="Curadoria & Reprocessamento", page_icon="🛡️", layout="wide")

st.title("🛡️ Extrator de Blockers e SKUs")

uploaded_file = st.file_uploader("Suba o arquivo CSV original", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        df = pd.read_csv(uploaded_file, encoding='latin1')
    
    col_id = st.selectbox("Selecione a coluna do navigation_id:", df.columns, index=0)
    col_desc = st.selectbox("Selecione a coluna do título do produto:", df.columns, index=1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        termo_alvo = st.text_input("Termo Principal (ex: Máquina de Costura):", "")
    with col2:
        sinonimos_input = st.text_input("Sinônimos/Validadores (ex: doméstica):", "")
    with col3:
        excecoes_input = st.text_input("Bloquear se for peça (ex: agulha):", "")

    if termo_alvo:
        # Lógica de Filtragem
        lista_validos = [termo_alvo.strip()] + [s.strip() for s in sinonimos_input.split(",") if s.strip()]
        regex_validos = '|'.join(lista_validos)
        
        mask_validos = df[col_desc].str.contains(regex_validos, case=False, na=False)
        df_obvios = df[~mask_validos].copy()
        df_potenciais_acertos = df[mask_validos].copy()

        # Inteligência de Sugestão
        todas_as_palavras = " ".join(df_potenciais_acertos[col_desc].astype(str)).lower()
        palavras = re.findall(r'\w+', todas_as_palavras)
        stop_words = [
            'para', 'com', 'pelo', 'pela', 'mais', 'esta', 'essa', 'este', 'esse',
            'sem', 'nos', 'nas', 'dos', 'das', 'uma', 'uns', 'umas', 'sob', 'sobre',
            'entre', 'através', 'cada', 'qual', 'quais', 'quem', 'cujo', 'cuja',
            'tudo', 'nada', 'algum', 'alguma', 'alguns', 'algumas', 'toda', 'todo',
            'todas', 'todos', 'outra', 'outro', 'outras', 'outros', 'muito', 'muita',
            'pode', 'ponto', 'item', 'peca', 'peça', 'unidade', 'unidades',
            'cm', 'mm', 'litros', 'volts', '110v', '220v', 'bivolt', 'preta', 'branco',
            'azul', 'verde', 'amarelo', 'cinza']
        palavras_filtradas = [w for w in palavras if len(w) > 3 and w not in stop_words and not any(v.lower() in w for v in lista_validos)]
        contagem = Counter(palavras_filtradas).most_common(10)
        
        st.info("💡 **Análise de Padrões:** Palavras que podem indicar blockers (peças/acessórios).")
        sugestoes = st.columns(len(contagem))
        for i, (palavra, freq) in enumerate(contagem):
            sugestoes[i].code(palavra)

        if st.button("☑️ Processar Dados"):
            lista_excecoes = [t.strip() for t in excecoes_input.split(",") if t.strip()]
            
            if lista_excecoes:
                regex_excecoes = '|'.join(lista_excecoes)
                mask_excecoes = df_potenciais_acertos[col_desc].str.contains(regex_excecoes, case=False, na=False)
                df_pecas = df_potenciais_acertos[mask_excecoes]
            else:
                df_pecas = pd.DataFrame()

            # Base completa de itens capturados (mantendo duplicados e IDs)
            df_raw_blockers = pd.concat([df_obvios, df_pecas])
            df_raw_blockers['blocker'] = df_raw_blockers[col_desc].str.lower()

            # --- 1. VISUALIZAÇÃO RÁPIDA (Apenas os termos únicos, sem ID e sem índice) ---
            st.subheader("Visualização dos Blockers Encontrados")
            
            # .unique() preserva a ordem de aparição original
            termos_unicos_lista = df_raw_blockers['blocker'].unique()
            df_visualizacao = pd.DataFrame(termos_unicos_lista, columns=['blocker'])
            
            # Exibe o dataframe ocultando a coluna de índice (o número da linha)
            st.dataframe(df_visualizacao, use_container_width=True, hide_index=True)

            # --- 2. ÁREA DE DOWNLOADS---
            st.divider()
            st.subheader("📥 Baixar Resultados")
            d_col1, d_col2 = st.columns(2)

            with d_col1:
                st.write("**Para Reprocessamento:**")
                st.caption("Contém navigation_id + termo")
                df_reprocessar = df_raw_blockers[[col_id, 'blocker']]
                csv_repro = df_reprocessar.to_csv(index=False).encode('utf-8')
                st.download_button("Download Reprocessamento", csv_repro, "lista_reprocessamento.csv", "text/csv")

            with d_col2:
                st.write("**Blockers:**")
                st.caption("Apenas termos únicos (sem SKU)")
                csv_blockers = termos_unicos.to_csv(index=False).encode('utf-8')
                st.download_button("Download Blockers (Únicos)", csv_blockers, "lista_blockers_ia.csv", "text/csv")








