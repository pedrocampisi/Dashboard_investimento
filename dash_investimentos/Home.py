import streamlit as st

st.set_page_config(
    page_title="Início | Simulador de Investimentos",
    page_icon="🏠",
    layout="wide"
)

st.title("Bem-vindo ao Simulador de Investimentos Imobiliários 🏡")
st.markdown("---")

st.markdown("""
Esta ferramenta foi projetada para ajudar você a tomar uma das decisões financeiras mais importantes: **onde alocar seu capital?**

Com este dashboard, você poderá comparar de forma clara e objetiva o rendimento financeiro entre duas estratégias principais:

1.  **🏗️ Construir um Imóvel:** Investir seu dinheiro na compra de um terreno e na construção de uma casa para venda futura.
2.  **💹 Investir em Renda Fixa:** Alocar o mesmo montante em uma aplicação financeira e deixá-lo render juros ao longo do tempo.

Analisamos essa comparação em **dois cenários de origem do capital**, pois os custos e benefícios mudam completamente em cada caso:
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 Cenário 1: Capital Próprio")
    st.markdown("""
    Nesta simulação, você utilizará seus próprios recursos para financiar todo o projeto de construção. 
    Analisaremos o retorno líquido, considerando os custos da obra e os impostos sobre o ganho de capital na venda do imóvel. Além disso, calcularemos o **importante benefício fiscal** que sua empresa obtém ao tratar o investimento como custo.
    
    *Use o menu na barra lateral para navegar até a página **"Capital Próprio"** e iniciar sua simulação.*
    """)

with col2:
    st.subheader("📄 Cenário 2: Dinheiro de Consórcio")
    st.markdown("""
    Aqui, o investimento inicial provém de uma carta de consórcio. O cálculo é diferente, pois precisamos considerar os **juros e as taxas administrativas** do consórcio como um custo adicional, que impacta diretamente a rentabilidade final do projeto.

    *(Página em desenvolvimento)*
    """)

st.markdown("---")
st.info("💡 **Dica:** Preencha os parâmetros com atenção em cada página para obter uma comparação precisa e que reflita sua realidade. Os resultados de cada simulação poderão ser comparados na página de **Resumo**.", icon="💡")