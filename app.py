import streamlit as st
import pandas as pd
from collections import Counter
import re

st.set_page_config(page_title="Extrator de Blockers", page_icon="🛡️", layout="wide")

st.title("🛡️ Extrator de Blockers com SKUs")

uploaded_file = st.file_uploader("Suba o arquivo CSV original", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        df = pd.read_csv(uploaded_file, encoding='latin1')
    
    # Seleção de colunas baseada nas suas imagens
    col_id = st.selectbox("Selecione a coluna do navigation_id (SKU do produto):", df.columns, index=0)
    col_desc = st.selectbox("Selecione a coluna com o título do produto:", df.columns, index=1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        termo_alvo = st.text_input("Termo Principal (ex: Máquina de Costura):", "")
    with col2:
        sinonimos_input = st.text_input("Sinônimos/Validadores (ex: doméstica, overlock):", "")
    with col3:
        excecoes_input = st.text_input("Bloquear se for peça (ex: agulha, cabo):", "")

    if termo_alvo:
        lista_validos = [termo_alvo.strip()] + [s.strip() for s in sinonimos_input.split(",") if s.strip()]
        regex_validos = '|'.join(lista_validos)
        
        # 1. Filtra o que é blocker direto por não ter o nome/sinônimo
        mask_validos = df[col_desc].str.contains(regex_validos, case=False, na=False)
        df_obvios = df[~mask_validos].copy()
        
        # 2. Itens válidos que podem ser peças (exceções)
        df_potenciais_acertos = df[mask_validos].copy()

        # --- INTELIGÊNCIA DE SUGESTÃO (OPCIONAL NO FLUXO) ---
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
            'azul', 'verde', 'amarelo', 'cinza'
        ]
        palavras_filtradas = [w for w in palavras if len(w) > 3 and w not in stop_words and not any(v.lower() in w for v in lista_validos)]
        contagem = Counter(palavras_filtradas).most_common(10)
        
        st.info("💡 **Análise de Padrões:** Palavras que podem indicar peças/acessórios")
        sugestoes = st.columns(len(contagem))
        for i, (palavra, freq) in enumerate(contagem):
            sugestoes[i].code(palavra)

        if st.button("☑️ Gerar Lista de Reprocessamento"):
            lista_excecoes = [t.strip() for t in excecoes_input.split(",") if t.strip()]
            
            if lista_excecoes:
                regex_excecoes = '|'.join(lista_excecoes)
                mask_excecoes = df_potenciais_acertos[col_desc].str.contains(regex_excecoes, case=False, na=False)
                df_pecas = df_potenciais_acertos[mask_excecoes]
            else:
                df_pecas = pd.DataFrame()

            # Unindo os resultados mantendo o ID
            df_final = pd.concat([df_obvios, df_pecas])
            
            # Formatação solicitada: minúsculas e mapeamento de colunas
            df_final['blocker'] = df_final[col_desc].str.lower()
            
            # Selecionamos apenas as colunas necessárias para o reprocessamento
            resultado = df_final[[col_id, 'blocker']].drop_duplicates()

            st.success(f"✅ {len(resultado)} itens prontos para reprocessamento!")
            st.dataframe(resultado)

            csv = resultado.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV de Reprocessamento", csv, "lista_reprocessar.csv", "text/csv")

            csv = resultado.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV de Blockers", csv, "blockers_ia_v3.csv", "text/csv")




