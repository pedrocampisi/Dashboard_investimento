import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Consórcio | Simulador",
    page_icon="📄",
    layout="wide"
)

# --- FUNÇÕES DE CÁLCULO (sem alterações) ---
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calculate_progressive_tax(profit):
    if profit <= 0: return 0
    tax = 0
    if profit <= 5_000_000: tax += profit * 0.15
    if profit > 5_000_000: tax += min(profit - 5_000_000, 5_000_000) * 0.175
    if profit > 10_000_000: tax += min(profit - 10_000_000, 20_000_000) * 0.20
    if profit > 30_000_000: tax += (profit - 30_000_000) * 0.225
    return tax

def calculate_scenario_1(initial_investment, monthly_rate, months):
    history = []
    balance = initial_investment
    for month in range(months + 1):
        history.append({'Mês': month, 'Saldo (R$)': balance})
        if month < months: balance *= (1 + monthly_rate)
    history_df = pd.DataFrame(history)
    final_amount_gross = history_df.iloc[-1]['Saldo (R$)']
    profit = final_amount_gross - initial_investment
    income_tax = profit * 0.15 if profit > 0 else 0
    final_amount_net = final_amount_gross - income_tax
    return final_amount_net, income_tax, history_df

def calculate_consortium_operation(params):
    effective_construction_cost = params['construction_cost_input'] * (1 + params['construction_cost_variation'] / 100)
    effective_sale_price = params['sale_price'] * (1 + params['sale_price_variation'] / 100)
    final_investment_balance = 0
    ir_from_fund_yields = 0
    history_s2 = []
    if params['consortium_loan'] > 0 and params['months'] > 0:
        monthly_withdrawal = effective_construction_cost / params['months']
        balance = params['consortium_loan']
        for month in range(params['months'] + 1):
            history_s2.append({'Mês': month, 'Saldo do Fundo (R$)': balance})
            if month < params['months']:
                monthly_yield = balance * params['monthly_rate']
                ir_on_yield = monthly_yield * 0.15
                ir_from_fund_yields += ir_on_yield
                balance += monthly_yield
                balance -= monthly_withdrawal
        final_investment_balance = balance if balance > 0 else 0
    history_s2_df = pd.DataFrame(history_s2)
    history_s2_df['Saldo do Fundo (R$)'] = history_s2_df['Saldo do Fundo (R$)'].clip(lower=0)
    construction_years = params['months'] / 12.0
    total_interest_paid = params['consortium_loan'] * (params['consortium_interest_rate'] / 100) * construction_years
    total_loan_repayment = params['consortium_loan'] + total_interest_paid
    house_total_cost = params['land_cost'] + effective_construction_cost
    house_sale_profit = effective_sale_price - house_total_cost
    real_estate_tax_paid = calculate_progressive_tax(house_sale_profit) if params['apply_sale_tax'] else 0
    total_taxes = real_estate_tax_paid + ir_from_fund_yields
    final_net_cash = (effective_sale_price + final_investment_balance) - (total_loan_repayment + total_taxes)
    tax_saving = params['land_cost'] * (params['corporate_tax_rate'] / 100)
    final_result_with_benefit = final_net_cash + tax_saving
    details = {
        "Custo Efetivo da Construção": effective_construction_cost,
        "Valor Efetivo de Venda": effective_sale_price,
        "Repagamento Total do Consórcio": total_loan_repayment,
        "Juros do Consórcio": total_interest_paid,
        "Imposto sobre Venda do Imóvel": real_estate_tax_paid,
        "IR sobre Rendimento do Fundo": ir_from_fund_yields,
        "Benefício Fiscal (sobre Terreno)": tax_saving,
        "Saldo Final do Fundo de Investimento": final_investment_balance,
        "Resultado Líquido da Operação": final_result_with_benefit
    }
    return final_result_with_benefit, details, history_s2_df

# --- INTERFACE DA APLICAÇÃO ---
st.title("📄 Simulador de Investimento com Consórcio")
st.markdown("Simule a operação de construção utilizando um consórcio como fonte de recursos e o capital próprio para o terreno.")
st.markdown("---")

# --- BARRA LATERAL ---
with st.sidebar:
    consortium_loan_input = st.number_input("Valor liberado pelo Itaú (Consórcio)", min_value=10000, value=2200000, step=50000, help="O montante total liberado pela carta de consórcio.")
    st.caption(f"Valor: {format_currency(consortium_loan_input)}")
    st.markdown("---")
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
        else:
            land_cost_input = st.number_input("Custo do Terreno (R$)", min_value=0, value=1100000, step=10000)
            construction_cost_input = st.number_input("Custo da Construção (R$)", min_value=0, value=2200000, step=10000)
            sale_price_input = st.number_input("Valor de Venda da Casa (R$)", min_value=10000, value=4500000, step=50000)
        st.info(f"Custo do Terreno (Capital Próprio): {format_currency(land_cost_input)}")
        st.markdown("---")
        months_input = st.number_input("Tempo de Construção (meses)", min_value=1, value=18, step=1)
        apply_sale_tax_input = st.checkbox("Deduzir imposto sobre ganho de capital da venda?", value=True)
    with st.expander("Parâmetros Fiscais e da Aplicação", expanded=True):
        consortium_interest_rate_input = st.number_input("Juros anuais do consórcio (%)", min_value=0.0, max_value=25.0, value=9.5, step=0.1, format="%.1f", help="Taxa de juros anual a ser paga sobre o valor do consórcio.")
        corporate_tax_rate_input = st.number_input("Imposto sobre Lucro da Empresa (%)", min_value=0.0, max_value=100.0, value=25.0, step=0.5, format="%.1f")
        monthly_rate_input = st.slider("Taxa de Rendimento Mensal (%)", min_value=0.5, max_value=3.0, value=1.176, step=0.001, format="%.3f%%")
        MONTHLY_RATE = monthly_rate_input / 100
        annual_rate = ((1 + MONTHLY_RATE)**12 - 1) * 100
        st.info(f"**Taxa Anual Equivalente:** {annual_rate:.2f}%")
        with st.expander("🔬 Extras (Análise de Sensibilidade)"):
            sale_price_variation_input = st.slider("Variação no Valor de Venda (%)", -20, 20, 0)
            construction_cost_variation_input = st.slider("Variação no Custo da Obra (%)", -20, 20, 0)

# --- EXECUÇÃO DOS CÁLCULOS ---
capital_proprio_investido = land_cost_input
final_s1, tax_s1, history_s1 = calculate_scenario_1(capital_proprio_investido, MONTHLY_RATE, months_input)

params_s2 = {
    'consortium_loan': consortium_loan_input, 'land_cost': land_cost_input,
    'construction_cost_input': construction_cost_input, 'sale_price': sale_price_input,
    'monthly_rate': MONTHLY_RATE, 'months': months_input,
    'consortium_interest_rate': consortium_interest_rate_input,
    'corporate_tax_rate': corporate_tax_rate_input, 'apply_sale_tax': apply_sale_tax_input,
    'sale_price_variation': sale_price_variation_input,
    'construction_cost_variation': construction_cost_variation_input
}
final_s2, details_s2, history_s2_df = calculate_consortium_operation(params_s2)

# --- LAYOUT PRINCIPAL ---
st.header("📈 Cenário 1: Investir o Valor do Terreno")
st.markdown(f"Análise do que aconteceria se o capital próprio de **{format_currency(capital_proprio_investido)}** fosse investido em uma aplicação financeira.")
col_rf1, col_rf2 = st.columns([2, 1])
with col_rf1:
    st.subheader("Evolução do Valor (Bruto)")
    fig_rf = go.Figure(data=[go.Scatter(x=history_s1['Mês'], y=history_s1['Saldo (R$)'], mode='lines', name='Saldo', fill='tozeroy', line=dict(color='#1f77b4', width=4), fillcolor='rgba(31, 119, 180, 0.3)', hovertemplate='<b>Mês %{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>')])
    fig_rf.update_layout(height=350, showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_rf, use_container_width=True)
with col_rf2:
    st.subheader("Resultado Final")
    st.metric("💰 Capital Próprio Investido", format_currency(capital_proprio_investido))
    st.metric("💸 Imposto de Renda (15%)", format_currency(tax_s1))
    st.metric("🎯 Valor Final (Líquido)", format_currency(final_s1), delta=f"{((final_s1 / capital_proprio_investido - 1) * 100):.2f}%")

st.markdown("---")
st.header("🏗️ Cenário 2: Operação de Construção com Consórcio")

st.subheader("Custos e Impostos da Operação")
cols_s2_costs = st.columns(4)
cols_s2_costs[0].metric("Custo Efetivo da Construção", format_currency(details_s2["Custo Efetivo da Construção"]))
cols_s2_costs[3].metric("Pagamento do Consórcio", format_currency(details_s2["Repagamento Total do Consórcio"]), delta=f'-{format_currency(details_s2["Juros do Consórcio"])} de juros', delta_color="normal")
cols_s2_costs[1].metric("Imposto sobre Venda do Imóvel", format_currency(details_s2["Imposto sobre Venda do Imóvel"]))
cols_s2_costs[2].metric("IR sobre Rendimento do Fundo", format_currency(details_s2["IR sobre Rendimento do Fundo"]))

st.subheader("Fluxo de Caixa da Operação")
s2_timeline = history_s2_df.copy().rename(columns={'Saldo do Fundo (R$)': 'Valor'})
pico_valor = details_s2["Saldo Final do Fundo de Investimento"] + details_s2["Valor Efetivo de Venda"]
s2_timeline.loc[s2_timeline['Mês'] == months_input, 'Valor'] = pico_valor
queda_valor = pico_valor - details_s2["Repagamento Total do Consórcio"]
linha_queda = pd.DataFrame([{'Mês': months_input + 1, 'Valor': queda_valor}])
s2_timeline = pd.concat([s2_timeline, linha_queda], ignore_index=True)

# ####################################################################
# ### INÍCIO DA CORREÇÃO DE SINTAXE ###
# ####################################################################

history_s1_ext = pd.concat([
    history_s1, 
    pd.DataFrame([{'Mês': months_input + 1, 'Saldo (R$)': history_s1.iloc[-1]['Saldo (R$)']}])
], ignore_index=True)

# ####################################################################
# ### FIM DA CORREÇÃO DE SINTAXE ###
# ####################################################################

fig_comp_evolucao = go.Figure()
fig_comp_evolucao.add_trace(go.Scatter(x=history_s1_ext['Mês'], y=history_s1_ext['Saldo (R$)'], mode='lines', name='Aplicação (Valor do Terreno)', line=dict(color='royalblue', width=4), hovertemplate='Mês %{x}:<br>R$ %{y:,.2f}<extra></extra>'))
fig_comp_evolucao.add_trace(go.Scatter(x=s2_timeline['Mês'], y=s2_timeline['Valor'], mode='lines', name='Operação Consórcio (Fluxo de Caixa)', line=dict(color='darkorange', width=4, dash='dash'), hovertemplate='Mês %{x}:<br>R$ %{y:,.2f}<extra></extra>'))
fig_comp_evolucao.update_layout(height=400, title_text='<b>Evolução do Fundo do Consórcio vs. Aplicação do Capital Próprio</b>', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig_comp_evolucao, use_container_width=True)

st.subheader("Receitas e Benefícios")
cols_s2_rev = st.columns(3)
cols_s2_rev[0].metric("Valor de Venda do Imóvel", format_currency(details_s2["Valor Efetivo de Venda"]))
cols_s2_rev[1].metric("Saldo Final do Fundo de Investimento", format_currency(details_s2["Saldo Final do Fundo de Investimento"]))
cols_s2_rev[2].metric("✅ Benefício Fiscal (Empresa)", format_currency(details_s2["Benefício Fiscal (sobre Terreno)"]))

st.metric("Resultado Líquido Final da Operação", format_currency(details_s2["Resultado Líquido da Operação"]))

st.markdown("---")
st.header("🏆 Veredito: Consórcio vs. Aplicação Financeira")

lucro_s1 = final_s1 - capital_proprio_investido
lucro_s2 = final_s2 - capital_proprio_investido
diferenca_lucro = lucro_s2 - lucro_s1

col_veredicto_1, col_veredicto_2 = st.columns(2)
with col_veredicto_1:
    st.subheader("Comparativo de Lucro")
    st.markdown(f"Análise do lucro gerado a partir do seu investimento inicial de **{format_currency(capital_proprio_investido)}**.")
    st.metric("Lucro ao Investir o Valor do Terreno", format_currency(lucro_s1))
    st.metric("Lucro com a Operação de Consórcio", format_currency(lucro_s2))
    st.metric("Diferença (a favor da Operação Consórcio)", format_currency(diferenca_lucro), delta=f"{(diferenca_lucro / capital_proprio_investido * 100 if capital_proprio_investido > 0 else 0):.2f}%")

with col_veredicto_2:
    st.subheader("Resultado Visual")
    if diferenca_lucro > 0:
        st.success(f"**A Operação de Consórcio foi mais rentável!** A operação gerou **{format_currency(diferenca_lucro)}** a mais de lucro.")
    else:
        st.warning(f"**A aplicação financeira foi mais rentável.** A operação de consórcio gerou **{format_currency(abs(diferenca_lucro))}** a menos de lucro.")
    fig_comp_bar = go.Figure(data=[go.Bar(name='Lucro Aplicação', x=['Lucro Final'], y=[lucro_s1], text=format_currency(lucro_s1), textposition='auto', marker_color='royalblue'), go.Bar(name='Lucro Consórcio', x=['Lucro Final'], y=[lucro_s2], text=format_currency(lucro_s2), textposition='auto', marker_color='darkorange')])
    fig_comp_bar.update_layout(barmode='group', title='Comparativo dos Lucros Finais', yaxis_title='Lucro Total (R$)', height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_comp_bar, use_container_width=True)

st.markdown("---")
if st.button("Salvar Resultado para Comparação 💾"):
    st.session_state['consorcio_results'] = {"lucro_rf": lucro_s1, "lucro_consorcio": lucro_s2}
    st.success("Resultado do cenário 'Consórcio' foi salvo! Você poderá vê-lo na página 'Resumo'.")