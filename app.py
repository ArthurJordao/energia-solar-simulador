import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from main import simular_solar

# Configuração da página
st.set_page_config(
    page_title="Simulador Solar",
    page_icon="☀️",
    layout="wide"
)

# Título
st.title("☀️ Simulador de Energia Solar")
st.markdown("Simule a economia com energia solar considerando financiamento, manutenção e sazonalidade.")

# Sidebar com parâmetros
st.sidebar.header("⚙️ Parâmetros da Simulação")

# Sistema Solar
st.sidebar.subheader("⚡ Sistema Solar")
tarifa = st.sidebar.number_input("Tarifa (R$/kWh)", value=0.973, step=0.001, format="%.3f")
fio_b = st.sidebar.number_input("Fio B (R$/kWh)", value=0.69568, step=0.001, format="%.3f")
geracao = st.sidebar.number_input("Geração mensal média (kWh)", value=1346.64, step=10.0)
consumo = st.sidebar.number_input("Consumo mensal (kWh)", value=1237.17, step=10.0)
autoconsumo = st.sidebar.slider("Autoconsumo (%)", 0, 100, 20) / 100

# Financeiro
st.sidebar.subheader("💰 Financeiro")
parcela = st.sidebar.number_input("Parcela (R$/mês)", value=750.0, step=50.0)
meses_financ = st.sidebar.slider("Financiamento (meses)", 12, 180, 72, step=6)
manutencao = st.sidebar.number_input("Manutenção anual (R$)", value=750.0, step=50.0)

# Simulação
st.sidebar.subheader("📊 Simulação")
anos = st.sidebar.slider("Anos de simulação", 1, 25, 10)
reajuste = st.sidebar.slider("Reajuste anual (%)", 0, 20, 8) / 100
degradacao = st.sidebar.slider("Degradação anual (%)", 0.0, 2.0, 0.5, step=0.1) / 100
sazonalidade = st.sidebar.checkbox("Usar sazonalidade (Florianópolis)", value=False)

# Botão de simular
if st.sidebar.button("🚀 Simular", type="primary", use_container_width=True):
    with st.spinner("Executando simulação..."):
        # Executar simulação
        df = simular_solar(
            tarifa_inicial=tarifa,
            fio_b_inicial=fio_b,
            geracao_mensal_media=geracao,
            consumo_mensal=consumo,
            perc_autoconsumo=autoconsumo,
            valor_parcela=parcela,
            meses_financiamento=meses_financ,
            anos_simulacao=anos,
            reajuste_anual=reajuste,
            custo_manutencao_anual=manutencao,
            degradacao_anual=degradacao,
            usar_sazonalidade=sazonalidade
        )

        # Armazenar no session state
        st.session_state['df'] = df
        st.session_state['meses_financ'] = meses_financ

# Mostrar resultados se existirem
if 'df' in st.session_state:
    df = st.session_state['df']
    meses_financ = st.session_state['meses_financ']

    # Métricas principais
    st.header("📊 Resumo Executivo")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Fluxo Líquido Acumulado",
            f"R$ {df['Acumulado (R$)'].iloc[-1]:,.2f}",
            delta=None
        )

    with col2:
        st.metric(
            "Total Economizado",
            f"R$ {df['Economia (R$)'].sum():,.2f}"
        )

    with col3:
        st.metric(
            "Total Pago (Financ.)",
            f"R$ {df['Parcela (R$)'].sum():,.2f}"
        )

    with col4:
        st.metric(
            "Total Manutenção",
            f"R$ {df['Manutenção (R$)'].sum():,.2f}"
        )

    with col5:
        st.metric(
            "Total Compra Rede",
            f"R$ {df['Compra rede (R$)'].sum():,.2f}"
        )

    # Gráfico principal
    st.header("📈 Fluxo Líquido Acumulado")

    fig = go.Figure()

    # Linha principal
    fig.add_trace(go.Scatter(
        x=df['Mês'],
        y=df['Acumulado (R$)'],
        mode='lines',
        name='Acumulado',
        line=dict(color='#2ecc71', width=3),
        fill='tozeroy',
        fillcolor='rgba(46, 204, 113, 0.2)'
    ))

    # Linha zero
    fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)

    # Linha de fim do financiamento
    if meses_financ < len(df):
        fig.add_vline(
            x=meses_financ,
            line_dash="dot",
            line_color="purple",
            opacity=0.7,
            annotation_text=f"Fim financiamento (mês {meses_financ})",
            annotation_position="top"
        )

    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title="R$",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabela de dados
    st.header("📋 Dados Detalhados")

    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["📊 Tabela Completa", "📈 Gráficos Adicionais", "💾 Exportar"])

    with tab1:
        st.dataframe(
            df.style.format({
                'Geração (kWh)': '{:.2f}',
                'Consumo (kWh)': '{:.2f}',
                'Saldo créditos (kWh)': '{:.2f}',
                'Tarifa (R$/kWh)': 'R$ {:.3f}',
                'Preço crédito (R$/kWh)': 'R$ {:.3f}',
                'Economia (R$)': 'R$ {:.2f}',
                'Compra rede (R$)': 'R$ {:.2f}',
                'Parcela (R$)': 'R$ {:.2f}',
                'Manutenção (R$)': 'R$ {:.2f}',
                'Fluxo líquido (R$)': 'R$ {:.2f}',
                'Acumulado (R$)': 'R$ {:.2f}'
            }),
            use_container_width=True,
            height=400
        )

    with tab2:
        # Gráfico de geração vs consumo
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df['Mês'], y=df['Geração (kWh)'],
                                  name='Geração', line=dict(color='orange')))
        fig2.add_trace(go.Scatter(x=df['Mês'], y=df['Consumo (kWh)'],
                                  name='Consumo', line=dict(color='blue')))
        if 'Saldo créditos (kWh)' in df.columns:
            fig2.add_trace(go.Scatter(x=df['Mês'], y=df['Saldo créditos (kWh)'],
                                     name='Saldo Créditos', line=dict(color='green', dash='dash')))
        fig2.update_layout(title="Geração vs Consumo vs Créditos", xaxis_title="Mês", yaxis_title="kWh")
        st.plotly_chart(fig2, use_container_width=True)

        # Gráfico de economia anual
        df_anual = df.groupby('Ano').agg({
            'Economia (R$)': 'sum',
            'Parcela (R$)': 'sum',
            'Manutenção (R$)': 'sum',
            'Compra rede (R$)': 'sum'
        }).reset_index()

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=df_anual['Ano'], y=df_anual['Economia (R$)'],
                             name='Economia', marker_color='green'))
        fig3.add_trace(go.Bar(x=df_anual['Ano'], y=-df_anual['Parcela (R$)'],
                             name='Parcela', marker_color='red'))
        fig3.add_trace(go.Bar(x=df_anual['Ano'], y=-df_anual['Manutenção (R$)'],
                             name='Manutenção', marker_color='orange'))
        fig3.add_trace(go.Bar(x=df_anual['Ano'], y=-df_anual['Compra rede (R$)'],
                             name='Compra Rede', marker_color='purple'))
        fig3.update_layout(title="Economia vs Custos por Ano", xaxis_title="Ano", yaxis_title="R$", barmode='relative')
        st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        st.markdown("### Exportar Dados")
        st.download_button(
            label="📥 Download CSV",
            data=df.to_csv(index=False).encode('utf-8-sig'),
            file_name="simulacao_solar.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption("💡 Baixe os dados completos da simulação em formato CSV (compatível com Excel, Google Sheets, etc.)")

else:
    # Mensagem inicial
    st.info("👈 Configure os parâmetros na barra lateral e clique em 'Simular' para começar!")
