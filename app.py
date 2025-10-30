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
valor_sistema = st.sidebar.number_input("Valor do sistema (R$)", value=28000.0, step=1000.0, help="Valor total do sistema solar")
entrada = st.sidebar.number_input("Entrada (R$)", value=0.0, step=1000.0, help="Valor pago à vista no início")
taxa_juros_mensal = st.sidebar.slider("Taxa de juros (% a.m.)", 0.0, 5.0, 2.20, step=0.05, help="Taxa de juros mensal do financiamento") / 100
meses_financ = st.sidebar.slider("Financiamento (meses)", 12, 180, 72, step=6)
manutencao = st.sidebar.number_input("Manutenção anual (R$)", value=750.0, step=50.0)

# Mostrar valores calculados
valor_financiado = valor_sistema - entrada
taxa_juros_anual = ((1 + taxa_juros_mensal) ** 12 - 1)
st.sidebar.info(f"💵 **Valor financiado:** R$ {valor_financiado:,.2f}  \n📊 **Taxa anual equivalente:** {taxa_juros_anual*100:.2f}% a.a.")

# Simulação
st.sidebar.subheader("📊 Simulação")
anos = st.sidebar.slider("Anos de simulação", 1, 25, 10)
reajuste = st.sidebar.slider("Reajuste anual (%)", 0, 20, 10) / 100
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
            valor_sistema=valor_sistema,
            entrada=entrada,
            taxa_juros_anual=taxa_juros_anual,
            meses_financiamento=meses_financ,
            anos_simulacao=anos,
            reajuste_anual=reajuste,
            custo_manutencao_anual=manutencao,
            degradacao_anual=degradacao,
            usar_sazonalidade=sazonalidade
        )

        # Calcular parcela para exibição
        from main import calcular_parcela_price
        parcela_calculada = calcular_parcela_price(valor_financiado, taxa_juros_mensal, meses_financ) if valor_financiado > 0 else 0

        # Armazenar no session state
        st.session_state['df'] = df
        st.session_state['meses_financ'] = meses_financ
        st.session_state['entrada'] = entrada
        st.session_state['valor_sistema'] = valor_sistema
        st.session_state['parcela'] = parcela_calculada
        st.session_state['valor_financiado'] = valor_financiado
        st.session_state['taxa_juros_mensal'] = taxa_juros_mensal
        st.session_state['taxa_juros_anual'] = taxa_juros_anual

# Mostrar resultados se existirem
if 'df' in st.session_state:
    df = st.session_state['df']
    meses_financ = st.session_state['meses_financ']
    entrada = st.session_state.get('entrada', 0)
    valor_sistema = st.session_state.get('valor_sistema', 28000)
    parcela = st.session_state.get('parcela', 0)
    valor_financiado = st.session_state.get('valor_financiado', 0)
    taxa_juros_mensal = st.session_state.get('taxa_juros_mensal', 0.008)
    taxa_juros_anual = st.session_state.get('taxa_juros_anual', 0.10)

    # Métricas principais
    st.header("📊 Resumo Executivo")

    # Informações do financiamento
    if valor_financiado > 0:
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            st.metric("Valor do Sistema", f"R$ {valor_sistema:,.2f}")
        with col_f2:
            st.metric("Entrada", f"R$ {entrada:,.2f}")
        with col_f3:
            st.metric("Parcela Calculada", f"R$ {parcela:,.2f}/mês",
                     help=f"{meses_financ}x de R$ {parcela:,.2f} (juros {taxa_juros_mensal*100:.2f}% a.m.)")
        with col_f4:
            total_pago_financ = entrada + (parcela * meses_financ)
            juros_pagos = total_pago_financ - valor_sistema
            st.metric("Total a Pagar", f"R$ {total_pago_financ:,.2f}",
                     delta=f"+R$ {juros_pagos:,.2f} ({juros_pagos/valor_sistema*100:.1f}% de juros)",
                     delta_color="inverse")
        st.divider()

    # Primeira linha de métricas
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

    # Análise da entrada (se houver)
    if entrada > 0:
        st.subheader("💵 Análise da Entrada")
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric(
                "Entrada Paga",
                f"R$ {entrada:,.2f}"
            )

        with col_b:
            # Encontrar quando recupera a entrada
            df_positivo_entrada = df[df['Acumulado com entrada (R$)'] > 0]
            if not df_positivo_entrada.empty:
                mes_recupera = df_positivo_entrada.iloc[0]['Mês']
                anos_recupera = mes_recupera // 12
                meses_resto = mes_recupera % 12
                st.metric(
                    "Payback da Entrada",
                    f"{anos_recupera}a {meses_resto}m",
                    delta=f"Mês {mes_recupera}",
                    help="Tempo para recuperar o valor da entrada"
                )
            else:
                st.metric(
                    "Payback da Entrada",
                    "Não recuperado",
                    delta="No período simulado"
                )

        with col_c:
            # Comparar com e sem entrada
            acum_final_com_entrada = df['Acumulado com entrada (R$)'].iloc[-1]
            st.metric(
                "Saldo Final (com entrada)",
                f"R$ {acum_final_com_entrada:,.2f}",
                delta=f"R$ {acum_final_com_entrada - df['Acumulado (R$)'].iloc[-1]:,.2f}",
                help="Fluxo acumulado descontando a entrada"
            )

    # Gráfico principal
    st.header("📈 Fluxo Líquido Acumulado")

    fig = go.Figure()

    # Linha principal (sem entrada)
    fig.add_trace(go.Scatter(
        x=df['Mês'],
        y=df['Acumulado (R$)'],
        mode='lines',
        name='Acumulado (sem entrada)',
        line=dict(color='#2ecc71', width=3),
        fill='tozeroy',
        fillcolor='rgba(46, 204, 113, 0.2)'
    ))

    # Linha com entrada (se houver)
    if entrada > 0:
        fig.add_trace(go.Scatter(
            x=df['Mês'],
            y=df['Acumulado com entrada (R$)'],
            mode='lines',
            name='Acumulado (com entrada)',
            line=dict(color='#e74c3c', width=2, dash='dot')
        ))

    # Linha zero
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

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
