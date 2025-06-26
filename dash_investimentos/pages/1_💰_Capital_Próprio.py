import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Simulador de Investimentos",
    page_icon="🏡",
    layout="wide"
)

# --- FUNÇÕES DE CÁLCULO ---

def format_currency(value):
    """Formata um valor numérico como moeda brasileira (R$)."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calculate_progressive_tax(profit):
    """
    Calcula o imposto sobre ganho de capital com base na tabela progressiva.
    """
    if profit <= 0:
        return 0

    tax = 0
    # Faixa 1: Até 5 milhões
    first_tier_profit = min(profit, 5_000_000)
    tax += first_tier_profit * 0.15

    # Faixa 2: De 5 a 10 milhões
    if profit > 5_000_000:
        second_tier_profit = min(profit, 10_000_000) - 5_000_000
        tax += second_tier_profit * 0.175

    # Faixa 3: De 10 a 30 milhões
    if profit > 10_000_000:
        third_tier_profit = min(profit, 30_000_000) - 10_000_000
        tax += third_tier_profit * 0.20

    # Faixa 4: Acima de 30 milhões
    if profit > 30_000_000:
        fourth_tier_profit = profit - 30_000_000
        tax += fourth_tier_profit * 0.225
        
    return tax

def calculate_scenario_1(initial_investment, monthly_rate, months):
    """
    Calcula o resultado do Cenário 1: Aplicação Financeira, incluindo o imposto de renda.
    """
    history = []
    balance = initial_investment
    
    for month in range(months + 1):
        history.append({'Mês': month, 'Saldo (R$)': balance})
        if month < months:
                balance *= (1 + monthly_rate)
            
    history_df = pd.DataFrame(history)
    final_amount_gross = history_df.iloc[-1]['Saldo (R$)']
    
    profit = final_amount_gross - initial_investment
    income_tax = profit * 0.15 if profit > 0 else 0
    
    final_amount_net = final_amount_gross - income_tax
    
    return final_amount_net, income_tax, history_df

def calculate_scenario_2(params):
    """
    Calcula o resultado do Cenário 2: Investimento em Construção, usando um dicionário de parâmetros.
    """
    # === ETAPA 0: VERIFICAR E CALCULAR INVESTIMENTO EXCEDENTE ===
    total_project_cost = params['land_cost'] + params['construction_cost_input']
    surplus_investment = 0
    final_surplus_value = 0 

    if params['initial_investment'] > total_project_cost:
        surplus_investment = params['initial_investment'] - total_project_cost
        if params['months'] > 0:
            final_surplus_value = surplus_investment * ((1 + params['monthly_rate']) ** params['months'])
        else:
            final_surplus_value = surplus_investment

    # === ETAPA 1: APLICAR VARIAÇÕES DE SENSIBILIDADE ===
    effective_sale_price = params['sale_price'] * (1 + params['sale_price_variation'] / 100)
    
    # === ETAPA 2: DEFINIR FUNDO DE INVESTIMENTO PARA A OBRA ===
    construction_fund_from_investment = params['construction_cost_input']
    
    # === ETAPA 3: CALCULAR CUSTO EFETIVO DA OBRA ===
    effective_construction_cost = params['construction_cost_input'] * (1 + params['construction_cost_variation'] / 100)

    # === ETAPA 4: SIMULAR EVOLUÇÃO DO FUNDO DURANTE A CONSTRUÇÃO E CALCULAR IR MENSAL ===
    final_investment_balance = 0
    history_df = pd.DataFrame([{'Mês': m, 'Saldo do Fundo (R$)': 0} for m in range(params['months'] + 1)])
    ir_from_fund_yields = 0 

    if construction_fund_from_investment > 0 and params['months'] > 0:
        monthly_withdrawal = effective_construction_cost / params['months']
        history = []
        balance = construction_fund_from_investment
        
        for month in range(params['months'] + 1):
            history.append({'Mês': month, 'Saldo do Fundo (R$)': balance})
            
            if month < params['months']:
                monthly_yield = balance * params['monthly_rate']
                
                ir_on_yield = monthly_yield * 0.15
                ir_from_fund_yields += ir_on_yield
                
                balance += monthly_yield
                balance -= monthly_withdrawal
        
        history_df = pd.DataFrame(history)
        history_df['Saldo do Fundo (R$)'] = history_df['Saldo do Fundo (R$)'].clip(lower=0)
        final_investment_balance = history_df.iloc[-1]['Saldo do Fundo (R$)']

    # === ETAPA 5: CALCULAR IMPOSTO DE RENDA TOTAL DO CENÁRIO 2 ===
    profit_surplus = final_surplus_value - surplus_investment
    ir_surplus = profit_surplus * 0.15 if profit_surplus > 0 else 0
    
    total_income_tax_s2 = ir_from_fund_yields + ir_surplus

    # === ETAPA 6: CALCULAR CUSTOS E LUCROS DO IMÓVEL ===
    house_total_cost = params['land_cost'] + effective_construction_cost
    house_sale_profit = effective_sale_price - house_total_cost
    
    # === ETAPA 7: CALCULAR IMPOSTO SOBRE GANHO DE CAPITAL DA VENDA ===
    real_estate_tax_paid = 0
    if params['apply_sale_tax']:
        real_estate_tax_paid = calculate_progressive_tax(house_sale_profit)
    
    # === ETAPA 8: CALCULAR RESULTADO FINAL LÍQUIDO ===
    final_total = (final_investment_balance + final_surplus_value + effective_sale_price) - (real_estate_tax_paid + total_income_tax_s2)
    
    # === ETAPA 9: CALCULAR ECONOMIA FISCAL DA EMPRESA ===
    tax_saving = params['initial_investment'] * (params['corporate_tax_rate'] / 100)
    
    # === ETAPA 10: ORGANIZAR DETALHES FISCAIS PARA RETORNO ===
    tax_details = {
        "Custo Total do Imóvel": house_total_cost,
        "Lucro da Venda": house_sale_profit,
        "Imposto Pago (Ganho de Capital)": real_estate_tax_paid,
        "Economia de Imposto (Empresa)": tax_saving
    }
    
    return final_total, history_df, tax_details, effective_sale_price, final_surplus_value, total_income_tax_s2

# --- INTERFACE DA APLICAÇÃO ---

st.title("🏡 Simulador de Investimentos com Análise Fiscal")
st.markdown("Compare o retorno financeiro entre investir em uma construção e uma aplicação de renda fixa.")

# ##################################################################
# ### INÍCIO DA ALTERAÇÃO - BARRA LATERAL REESTRUTURADA ###
# ##################################################################

with st.sidebar:
    # --- PARTE 1: INVESTIMENTO INICIAL (SEM TÍTULO) ---
    initial_investment_input = st.number_input(
        "Qual o seu Investimento inicial?",
        min_value=10000, value=3300000, step=50000,
        help="O capital total que você tem disponível para investir."
    )
    st.caption(f"Valor: {format_currency(initial_investment_input)}")
    st.markdown("---")

    # --- PARTE 2: PARÂMETROS DA CONSTRUÇÃO (MINIMIZÁVEL) ---
    with st.expander("Parâmetros da Construção", expanded=True):
        use_m2_pricing = st.checkbox("Calcular custos por m²?", value=True)
    
        if use_m2_pricing:
            area_terreno_m2 = st.number_input("Área do Terreno (m²)", min_value=1.0, value=1003.0, step=10.0)
            area_construcao_m2 = st.number_input("Área de Construção (m²)", min_value=1.0, value=456.0, step=10.0)
            st.markdown("---")
            
            land_cost_per_m2 = st.number_input("Valor do m² do Terreno (R$)", min_value=0, value=1100, step=50)
            construction_cost_per_m2 = st.number_input("Valor do m² da Construção (R$)", min_value=0, value=4800, step=100)
            sale_price_per_m2 = st.number_input("Valor do m² de Venda (R$)", min_value=0, value=11000, step=100)

            land_cost_input = land_cost_per_m2 * area_terreno_m2
            construction_cost_input = construction_cost_per_m2 * area_construcao_m2
            sale_price_input = sale_price_per_m2 * area_construcao_m2

            st.info(f"""
            **Custos Totais Calculados:**
            - **Terreno:** {format_currency(land_cost_input)}
            - **Construção:** {format_currency(construction_cost_input)}
            - **Venda:** {format_currency(sale_price_input)}
            """)
        else:
            land_cost_input = st.number_input(
                "Custo do Terreno (R$)",
                min_value=0, value=1100000, step=10000,
                help="O valor a ser pago pelo terreno."
            )
            construction_cost_input = st.number_input(
                "Custo da Construção (R$)",
                min_value=0, value=2200000, step=10000,
                help="Custo total estimado da obra, sem o terreno."
            )
            sale_price_input = st.number_input(
                "Valor de Venda da Casa (R$)",
                min_value=10000, value=4500000, step=50000,
                help="O valor estimado pelo qual a casa será vendida."
            )
        
        st.markdown("---")

        months_input = st.number_input(
            "Tempo de Construção (meses)",
            min_value=1, value=18, step=1,
            help="Insira o período total em meses para a construção e venda da casa."
        )

        apply_sale_tax_input = st.checkbox(
            "Deduzir imposto sobre ganho de capital da venda?",
            value=True,
            help="Marque esta opção para subtrair o imposto da venda do resultado final da construção."
        )

    # --- PARTE 3: PARÂMETROS FISCAIS E DA APLICAÇÃO (MINIMIZÁVEL) ---
    with st.expander("Parâmetros Fiscais e da Aplicação", expanded=True):
        corporate_tax_rate_input = st.number_input(
            "Imposto sobre Lucro da Empresa (%)",
            min_value=0.0, max_value=100.0, value=25.0, step=0.5,
            format="%.1f",
            help="Alíquota de imposto que a empresa do cliente paga sobre seu lucro."
        )
        
        monthly_rate_input = st.slider(
            "Taxa de Rendimento Mensal (%)",
            min_value=0.5, max_value=3.0, value=1.176, step=0.001,
            format="%.3f%%",
            help="A taxa de juros mensal para a aplicação financeira."
        )
        
        MONTHLY_RATE = monthly_rate_input / 100
        annual_rate = ((1 + MONTHLY_RATE)**12 - 1) * 100
        st.info(f"**Taxa Anual Equivalente:** {annual_rate:.2f}%")

        with st.expander("🔬 Extras (Análise de Sensibilidade)"):
            st.markdown("Simule o impacto de variações de mercado e de custos no resultado final.")
            sale_price_variation_input = st.slider("Variação no Valor de Venda (%)", -20, 20, 0)
            construction_cost_variation_input = st.slider("Variação no Custo da Obra (%)", -20, 20, 0)

# ################################################################
# ### FIM DA ALTERAÇÃO - BARRA LATERAL REESTRUTURADA ###
# ################################################################


# --- EXECUÇÃO DOS CÁLCULOS ---
final_s1, tax_s1, history_s1 = calculate_scenario_1(initial_investment_input, MONTHLY_RATE, months_input)

params_s2 = {
    'initial_investment': initial_investment_input, 'land_cost': land_cost_input,
    'construction_cost_input': construction_cost_input,
    'sale_price': sale_price_input, 'monthly_rate': MONTHLY_RATE, 'months': months_input,
    'corporate_tax_rate': corporate_tax_rate_input, 'apply_sale_tax': apply_sale_tax_input,
    'sale_price_variation': sale_price_variation_input,
    'construction_cost_variation': construction_cost_variation_input
}
final_s2, history_s2, tax_details, effective_sale_price, final_surplus_s2, tax_s2_income = calculate_scenario_2(params_s2)


# --- LAYOUT PRINCIPAL ---

# --- PARTE 1: EVOLUÇÃO DO INVESTIMENTO EM RENDA FIXA ---
st.markdown("---")
st.header("📈 Cenário 1: Aplicação Financeira")
col_rf1, col_rf2 = st.columns([2, 1])
with col_rf1:
    fig_rf = go.Figure()
    fig_rf.add_trace(go.Scatter(x=history_s1['Mês'], y=history_s1['Saldo (R$)'], mode='lines', name='Saldo', fill='tozeroy', line=dict(color='#1f77b4', width=4), fillcolor='rgba(31, 119, 180, 0.3)', hovertemplate='<b>Mês %{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>'))
    marco_meses = sorted(list(set([0, months_input//4, months_input//2, 3*months_input//4, months_input])))
    marco_valores = [history_s1.iloc[m]['Saldo (R$)'] for m in marco_meses]
    fig_rf.add_trace(go.Scatter(x=marco_meses, y=marco_valores, mode='markers', marker=dict(size=10, color='#ff7f0e', symbol='circle'), name='Marcos', hovertemplate='<b>Mês %{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>'))
    fig_rf.update_layout(title='<b>Crescimento do Investimento (Bruto)</b>', xaxis_title='Período (Meses)', yaxis_title='Valor Acumulado (R$)', height=450, showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(size=12), title_font=dict(size=16, color='#2c3e50'), xaxis=dict(gridcolor='rgba(128,128,128,0.2)'), yaxis=dict(gridcolor='rgba(128,128,128,0.2)', tickformat='$,.0f'))
    st.plotly_chart(fig_rf, use_container_width=True)
with col_rf2:
    st.metric("💰 Investimento Inicial", format_currency(initial_investment_input))
    st.metric("📅 Período Total", f"{months_input} meses")
    st.metric("📊 Taxa Mensal", f"{monthly_rate_input:.3f}%")
    st.metric("💸 Imposto de Renda Sobre o Lucro (15%)", format_currency(tax_s1), help="15% sobre o lucro da aplicação.")
    st.metric("🎯 Valor Final (Líquido)", format_currency(final_s1))
    lucro_rf = final_s1 - initial_investment_input
    rentabilidade_rf = (lucro_rf / initial_investment_input) * 100 if initial_investment_input > 0 else 0
    st.success(f"**Lucro Líquido: {format_currency(lucro_rf)}**")
    st.success(f"**Rentabilidade Líquida: {rentabilidade_rf:.2f}%**")

# --- PARTE 2: FUNDO DA OBRA COM VENDA FINAL (NOVA ESTRUTURA) ---
st.markdown("---")
st.header("🏗️ Cenário 2: Investimento em Construção")

st.subheader("Custos e Impostos da Operação")
effective_construction_cost = construction_cost_input * (1 + construction_cost_variation_input / 100)
monthly_withdrawal = effective_construction_cost / months_input if months_input > 0 else 0

# Linha 1: Custos principais
cols_costs_1 = st.columns(3)
with cols_costs_1[0]:
    st.metric("Custo do Terreno", format_currency(land_cost_input))
with cols_costs_1[1]:
    st.metric("Custo da Construção", format_currency(effective_construction_cost), help="Custo total estimado da obra, considerando a variação de sensibilidade.")
with cols_costs_1[2]:
    st.metric("Retirada Mensal para Obra", format_currency(monthly_withdrawal), help=f"Custo total da obra dividido por {months_input} meses.")

# Linha 2: Impostos
cols_costs_2 = st.columns(3)
with cols_costs_2[0]:
    st.metric("Imposto Sobre a Venda da Casa", format_currency(tax_details['Imposto Pago (Ganho de Capital)']), help="Calculado sobre o lucro da venda do imóvel.")
with cols_costs_2[1]:
    st.metric("IR sobre o Lucro do Rendimento (15%)", format_currency(tax_s2_income), help="15% sobre o lucro do fundo da obra e do capital excedente.")

# --- Gráfico Comparativo de Crescimento Bruto ---
final_fund_balance_s2 = history_s2.iloc[-1]['Saldo do Fundo (R$)']
gross_final_s2 = final_fund_balance_s2 + effective_sale_price + final_surplus_s2

s2_timeline = history_s2.copy()
s2_timeline.rename(columns={'Saldo do Fundo (R$)': 'Evolução Construção (R$)'}, inplace=True)
if months_input > 0:
    s2_timeline.loc[s2_timeline['Mês'] == months_input, 'Evolução Construção (R$)'] = gross_final_s2

fig_comp_evolucao = go.Figure()
fig_comp_evolucao.add_trace(go.Scatter(
    x=history_s1['Mês'], y=history_s1['Saldo (R$)'], mode='lines', name='Aplicação Financeira (Bruto)',
    line=dict(color='royalblue', width=4), hovertemplate='Mês %{x}:<br>R$ %{y:,.2f}<extra></extra>'
))
fig_comp_evolucao.add_trace(go.Scatter(
    x=s2_timeline['Mês'], y=s2_timeline['Evolução Construção (R$)'], mode='lines', name='Construção (Bruto)',
    line=dict(color='darkorange', width=4, dash='dash'), hovertemplate='Mês %{x}:<br>R$ %{y:,.2f}<extra></extra>'
))
fig_comp_evolucao.update_layout(
    height=500, title='<b>Crescimento Bruto do Capital: Aplicação vs. Construção</b>',
    xaxis_title='Período (Meses)', yaxis_title='Valor Total (R$)',
    showlegend=True, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font=dict(size=12, color='#333'), title_font=dict(size=18, color='#2c3e50'),
    xaxis=dict(gridcolor='rgba(128,128,128,0.2)'), yaxis=dict(gridcolor='rgba(128,128,128,0.2)', tickformat='$,.0f'),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_comp_evolucao, use_container_width=True)

st.subheader("Receitas e Resultado")
receita_liquida_s2 = gross_final_s2 - (tax_details['Imposto Pago (Ganho de Capital)'] + tax_s2_income)
num_cols = 4 if final_surplus_s2 > 0 else 3
cols_rev = st.columns(num_cols)

with cols_rev[0]:
    st.metric("Saldo Restante do Fundo da Obra", format_currency(final_fund_balance_s2))
with cols_rev[1]:
    st.metric("Valor de Venda do Imóvel", format_currency(effective_sale_price))
if final_surplus_s2 > 0:
    with cols_rev[2]:
        st.metric("Rendimento do Capital Excedente", format_currency(final_surplus_s2),
        help=f"Rendimento sobre os {format_currency(params_s2['initial_investment'] - (params_s2['land_cost'] + params_s2['construction_cost_input']))} que excederam o custo do projeto.")
    with cols_rev[3]:
        st.metric("Receita Total Líquida", format_currency(receita_liquida_s2), help="Receita bruta menos os impostos sobre ganho de capital e rendimentos.")
else:
    with cols_rev[2]:
        st.metric("Receita Total Líquida", format_currency(receita_liquida_s2), help="Receita bruta menos os impostos sobre ganho de capital e rendimentos.")

# --- PARTE 3: BENEFÍCIO FISCAL ---
st.markdown("---")
st.header("💸 Análise do Benefício Fiscal")
col_fiscal1, col_fiscal2 = st.columns([1, 1])
with col_fiscal1:
    st.markdown("""
    Ao direcionar o capital para a construção, este valor é tratado como um **custo de investimento**, e não como lucro na sua empresa.
    Isso resulta em uma **economia direta no imposto de renda** que você pagaria sobre esse montante se ele ficasse no caixa da empresa.
    """)
    st.metric(
        "Economia de Imposto Gerada na Empresa",
        format_currency(tax_details['Economia de Imposto (Empresa)']),
        help=f"Cálculo: {format_currency(initial_investment_input)} (Investimento) * {corporate_tax_rate_input}% (Alíquota da Empresa)"
    )
with col_fiscal2:
    economia = tax_details['Economia de Imposto (Empresa)']
    if initial_investment_input > 0 :
        investimento_liquido = initial_investment_input - economia
    else:
        investimento_liquido = 0
    
    fig_fiscal = go.Figure(data=[go.Pie(
        labels=['Economia Fiscal Gerada', 'Custo Efetivo do Investimento'],
        values=[economia, investimento_liquido],
        hole=.4,
        marker_colors=['#27ae60', '#34495e'],
        textinfo='percent+label',
        insidetextorientation='radial'
    )])
    
    fig_fiscal.update_layout(
        title_text="<b>Proporção do Benefício Fiscal sobre o Investimento</b>",
        height=350,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_fiscal, use_container_width=True)


# --- PARTE 4: VEREDITO FINAL ---
final_s2_total_benefit = final_s2 + tax_details["Economia de Imposto (Empresa)"]

profit_s1 = final_s1 - initial_investment_input
profit_s2_total_benefit = final_s2_total_benefit - initial_investment_input
difference_total_benefit = final_s2_total_benefit - final_s1
if initial_investment_input > 0:
    profit_s1_percent = (profit_s1 / initial_investment_input) * 100
    profit_s2_total_benefit_percent = (profit_s2_total_benefit / initial_investment_input) * 100
    difference_total_benefit_percent = (difference_total_benefit / initial_investment_input) * 100
else:
    profit_s1_percent = profit_s2_total_benefit_percent = difference_total_benefit_percent = 0
    
st.markdown("---")
st.header("🏆 Veredito: O Grande Final")
col_summary1, col_summary2 = st.columns([1, 1.5], gap="large")
with col_summary1:
    st.subheader("Resumo dos Resultados")
    st.metric("Resultado Final: Aplicação", format_currency(final_s1), delta=f"Lucro: {format_currency(profit_s1)} ({profit_s1_percent:.2f}%)")
    st.metric("Resultado Final: Construção (Total)", format_currency(final_s2_total_benefit), delta=f"Lucro: {format_currency(profit_s2_total_benefit)} ({profit_s2_total_benefit_percent:.2f}%)")
    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Diferença Final (a favor da Construção)", format_currency(difference_total_benefit), delta=f"{difference_total_benefit_percent:.2f}%")
with col_summary2:
    st.subheader("Comparativo Visual")
    if difference_total_benefit > 0:
        st.success(f"**Construir foi mais rentável!** A construção gerou **{format_currency(difference_total_benefit)}** a mais que a aplicação.")
    else:
        st.warning(f"**A aplicação foi mais rentável.**")
    fig_comp_bar = go.Figure(data=[
        go.Bar(name='Aplicação', x=['Resultado Final'], y=[final_s1], text=format_currency(final_s1), textposition='auto', marker_color='royalblue'),
        go.Bar(name='Construção (Total)', x=['Resultado Final'], y=[final_s2_total_benefit], text=format_currency(final_s2_total_benefit), textposition='auto', marker_color='darkorange')
    ])
    fig_comp_bar.update_layout(barmode='group', title='Comparativo dos Valores Finais', yaxis_title='Valor Total (R$)', height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_comp_bar, use_container_width=True)

# --- PARTE 5: FERRAMENTAS AVANÇADAS ---
st.markdown("---")
st.header("🛠️ Ferramentas Avançadas")
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []

col_tools1, col_tools2 = st.columns(2)
with col_tools1:
    if st.button("💾 Salvar Cenário Atual"):
        new_scenario = {
            "Investimento (R$)": initial_investment_input,
            "Resultado Renda Fixa (R$)": final_s1,
            "Resultado Construção (R$)": final_s2_total_benefit,
            "Diferença (R$)": difference_total_benefit,
            "Tempo (Meses)": months_input,
            "Var. Venda (%)": sale_price_variation_input,
            "Var. Custo (%)": construction_cost_variation_input
        }
        st.session_state.scenarios.append(new_scenario)
        st.success("Cenário salvo!")
with col_tools2:
    if st.button("🗑️ Limpar Cenários Salvos"):
        st.session_state.scenarios = []
        st.info("Lista de cenários limpa.")

if st.session_state.scenarios:
    st.subheader("📋 Cenários Salvos para Comparação")
    df_scenarios = pd.DataFrame(st.session_state.scenarios)
    df_scenarios_display = df_scenarios.style.format({
        "Investimento (R$)": '{:,.2f}', "Resultado Renda Fixa (R$)": '{:,.2f}',
        "Resultado Construção (R$)": '{:,.2f}', "Diferença (R$)": '{:,.2f}'
    })
    st.dataframe(df_scenarios_display, use_container_width=True)

with st.expander("📄 Gerar Relatório para Impressão/PDF"):
    st.markdown("Para salvar, use a função de impressão do seu navegador (Ctrl+P) e selecione 'Salvar como PDF'.")
    st.markdown(f"### Relatório de Simulação - {pd.to_datetime('today').strftime('%d/%m/%Y')}")
    st.markdown("#### Parâmetros Iniciais")
    st.write(f"- **Investimento Inicial:** {format_currency(initial_investment_input)}")
    st.write(f"- **Custo do Terreno:** {format_currency(land_cost_input)}")
    st.write(f"- **Custo da Construção:** {format_currency(construction_cost_input)}")
    st.write(f"- **Período:** {months_input} meses")
    st.write(f"- **Taxa de Rendimento Mensal:** {monthly_rate_input:.3f}%")
    st.markdown("#### Resultados Consolidados")
    st.write(f"- **Resultado Final da Aplicação (Líquido de IR):** {format_currency(final_s1)}")
    st.write(f"- **Resultado Final da Construção (com benefícios):** {format_currency(final_s2_total_benefit)}")
    st.write(f"- **Diferença (Construção vs. Aplicação):** {format_currency(difference_total_benefit)}")
    st.markdown("---")