import pandas as pd
import argparse

def simular_solar(
    tarifa_inicial=0.973,
    fio_b_inicial=0.69568,
    geracao_mensal_media=1346.64,
    consumo_mensal=1237.17,
    perc_autoconsumo=0.20,
    valor_parcela=750,
    meses_financiamento=72,
    anos_simulacao=10,
    reajuste_anual=0.10,
    custo_manutencao_anual=750,
    degradacao_anual=0.005,
    ano_inicial=2026,
    usar_sazonalidade=True
):
    """
    Simula economia com energia solar considerando financiamento, manutenção, degradação e sazonalidade.

    Args:
        tarifa_inicial: Tarifa total inicial (R$/kWh)
        fio_b_inicial: Tarifa Fio B inicial (R$/kWh)
        geracao_mensal_media: Geração mensal média anual do sistema (kWh)
        consumo_mensal: Consumo mensal da residência (kWh)
        perc_autoconsumo: Percentual de autoconsumo instantâneo (0-1)
        valor_parcela: Valor da parcela do financiamento (R$/mês)
        meses_financiamento: Duração do financiamento em meses
        anos_simulacao: Duração total da simulação em anos
        reajuste_anual: Taxa de reajuste anual da tarifa (0-1)
        custo_manutencao_anual: Custo anual de manutenção/limpeza (R$/ano)
        degradacao_anual: Taxa de degradação anual da eficiência (0-1, padrão 0.5%)
        ano_inicial: Ano inicial da simulação
        usar_sazonalidade: Se True, aplica variação sazonal típica de Florianópolis
    """
    # Percentual de Fio B pago por ano (Lei 14.300/2022)
    pagamento_fioB = {
        2026: 0.60, 2027: 0.75, 2028: 0.90,
        2029: 1.00, 2030: 1.00, 2031: 1.00
    }

    # Fatores de sazonalidade para Florianópolis (baseado em insolação típica)
    # Janeiro = mês 1, Dezembro = mês 12
    # Valores relativos à média anual (1.0 = média)
    sazonalidade_mensal = {
        1: 1.25,   # Janeiro - verão, alta insolação
        2: 1.20,   # Fevereiro - verão
        3: 1.10,   # Março - outono começa
        4: 0.90,   # Abril - outono
        5: 0.75,   # Maio - outono/inverno
        6: 0.70,   # Junho - inverno, menor insolação
        7: 0.75,   # Julho - inverno
        8: 0.85,   # Agosto - inverno/primavera
        9: 0.95,   # Setembro - primavera
        10: 1.05,  # Outubro - primavera
        11: 1.15,  # Novembro - primavera/verão
        12: 1.25   # Dezembro - verão
    }

    custo_manutencao_mensal = custo_manutencao_anual / 12
    saldo_creditos = 0  # Saldo de créditos de energia acumulados (kWh)

    dados = []
    tarifa = tarifa_inicial
    fio_b = fio_b_inicial

    for mes in range(1, anos_simulacao * 12 + 1):
        ano = ano_inicial + (mes - 1) // 12
        anos_passados = (mes - 1) // 12
        mes_do_ano = ((mes - 1) % 12) + 1  # 1-12

        # Reajuste anual (aplicado no início de cada ano)
        if mes > 1 and (mes - 1) % 12 == 0:
            tarifa *= (1 + reajuste_anual)
            fio_b *= (1 + reajuste_anual)

        # Geração considerando degradação e sazonalidade
        geracao_base = geracao_mensal_media * ((1 - degradacao_anual) ** anos_passados)

        if usar_sazonalidade:
            fator_sazonal = sazonalidade_mensal[mes_do_ano]
            geracao_mensal = geracao_base * fator_sazonal
        else:
            geracao_mensal = geracao_base

        # Percentual do Fio B (100% após 2029)
        p_fio_b = pagamento_fioB.get(ano, 1.00)

        # Preço do crédito injetado
        preco_credito = tarifa - (fio_b * p_fio_b)

        # Cálculo da economia considerando a geração real e créditos acumulados
        auto_consumo = consumo_mensal * perc_autoconsumo
        consumo_rede = consumo_mensal - auto_consumo

        # Energia disponível para crédito (injetada na rede)
        energia_injetada = max(0, geracao_mensal - auto_consumo)

        # Adiciona energia injetada ao saldo de créditos
        saldo_creditos += energia_injetada

        # Usa créditos acumulados para compensar o consumo da rede
        energia_compensada = min(consumo_rede, saldo_creditos)
        saldo_creditos -= energia_compensada

        # Energia que ainda precisa comprar da rede (após usar créditos)
        energia_comprada_rede = consumo_rede - energia_compensada

        # Economia total:
        # - Autoconsumo valorizado pela tarifa cheia
        # - Energia compensada valorizada pelo preço do crédito
        economia = (auto_consumo * tarifa) + (energia_compensada * preco_credito)

        # Custo da energia que ainda precisa comprar (se houver)
        custo_energia_rede = energia_comprada_rede * tarifa

        # Parcela do financiamento (0 após término)
        parcela = valor_parcela if mes <= meses_financiamento else 0

        # Fluxo líquido = economia - parcela - manutenção - energia comprada da rede
        fluxo_liquido = economia - parcela - custo_manutencao_mensal - custo_energia_rede

        dados.append({
            "Mês": mes,
            "Ano": ano,
            "Mês/Ano": f"{mes_do_ano:02d}/{ano}",
            "Geração (kWh)": round(geracao_mensal, 2),
            "Consumo (kWh)": round(consumo_mensal, 2),
            "Saldo créditos (kWh)": round(saldo_creditos, 2),
            "Tarifa (R$/kWh)": round(tarifa, 3),
            "Preço crédito (R$/kWh)": round(preco_credito, 3),
            "Economia (R$)": round(economia, 2),
            "Compra rede (R$)": round(custo_energia_rede, 2),
            "Parcela (R$)": parcela,
            "Manutenção (R$)": round(custo_manutencao_mensal, 2),
            "Fluxo líquido (R$)": round(fluxo_liquido, 2)
        })

    df = pd.DataFrame(dados)
    df["Acumulado (R$)"] = df["Fluxo líquido (R$)"].cumsum()

    return df


def exibir_resultados(df, meses_financiamento, exportar_csv=True, nome_arquivo="simulacao_solar.csv"):
    """Exibe resultados da simulação de forma formatada.

    Args:
        df: DataFrame com os resultados da simulação
        meses_financiamento: Número de meses do financiamento
        exportar_csv: Se True, exporta os resultados para CSV
        nome_arquivo: Nome do arquivo CSV a ser gerado
    """
    pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

    print("\n=== SIMULAÇÃO MENSAL ===")
    print(df.to_string(index=False))

    # Resumo geral
    total_economia = df["Economia (R$)"].sum()
    total_pago = df["Parcela (R$)"].sum()
    total_manutencao = df["Manutenção (R$)"].sum()
    total_compra_rede = df["Compra rede (R$)"].sum()
    fluxo_final = df["Acumulado (R$)"].iloc[-1]
    media_mensal = df["Fluxo líquido (R$)"].mean()

    geracao_inicial = df["Geração (kWh)"].iloc[0]
    geracao_final = df["Geração (kWh)"].iloc[-1]
    degradacao_total = ((geracao_inicial - geracao_final) / geracao_inicial) * 100

    print("\n=== RESUMO FINAL ===")
    print(f"Período total: {len(df)} meses ({len(df) // 12} anos)")
    print(f"Total economizado: R$ {total_economia:,.2f}")
    print(f"Total pago no financiamento: R$ {total_pago:,.2f}")
    print(f"Total gasto com manutenção: R$ {total_manutencao:,.2f}")
    print(f"Total gasto com compra de energia: R$ {total_compra_rede:,.2f}")
    print(f"Fluxo líquido acumulado: R$ {fluxo_final:,.2f}")
    print(f"Média mensal de fluxo líquido: R$ {media_mensal:,.2f}")
    print(f"\nDegradação das placas: {degradacao_total:.2f}% ({geracao_inicial:.2f} → {geracao_final:.2f} kWh/mês)")

    # Análise do período de financiamento
    df_financiamento = df[df["Mês"] <= meses_financiamento]
    fluxo_durante_financ = df_financiamento["Fluxo líquido (R$)"].sum()
    acum_fim_financ = df_financiamento["Acumulado (R$)"].iloc[-1] if not df_financiamento.empty else 0

    print(f"\n=== ANÁLISE POR PERÍODO ===")
    print(f"Durante financiamento ({meses_financiamento} meses):")
    print(f"  - Fluxo líquido total: R$ {fluxo_durante_financ:,.2f}")
    print(f"  - Acumulado ao final: R$ {acum_fim_financ:,.2f}")

    # Análise do período pós-financiamento
    if len(df) > meses_financiamento:
        df_pos_financ = df[df["Mês"] > meses_financiamento]
        fluxo_pos_financ = df_pos_financ["Fluxo líquido (R$)"].sum()
        media_pos_financ = df_pos_financ["Fluxo líquido (R$)"].mean()

        print(f"\nApós financiamento ({len(df_pos_financ)} meses):")
        print(f"  - Fluxo líquido total: R$ {fluxo_pos_financ:,.2f}")
        print(f"  - Média mensal: R$ {media_pos_financ:,.2f}")

        # Análise de payback mais realista
        print("\n=== ANÁLISE DE PAYBACK ===")

        # Identifica quando o fluxo acumulado fica definitivamente positivo
        acum_min = df["Acumulado (R$)"].min()
        mes_min = df["Acumulado (R$)"].idxmin() + 1

        print(f"Acumulado mínimo: R$ {acum_min:,.2f} no mês {mes_min}")

        # Verifica se há payback (acumulado positivo ao final)
        if fluxo_final > 0:
            # Encontra quando cruza zero pela última vez
            df_negativo = df[df["Acumulado (R$)"] < 0]
            if not df_negativo.empty:
                ultimo_mes_negativo = df_negativo.iloc[-1]["Mês"]
                mes_payback = ultimo_mes_negativo + 1
                ano_payback = mes_payback // 12
                mes_resto = mes_payback % 12
                print(f"Payback (última vez que cruza zero): mês {mes_payback} ({ano_payback} anos e {mes_resto} meses)")
            else:
                print("Payback: imediato (fluxo sempre positivo)")
        else:
            print(f"Payback: não atingido no período simulado")
            print(f"Acumulado final ainda negativo: R$ {fluxo_final:,.2f}")

    # Exportar para CSV
    if exportar_csv:
        df.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
        print(f"\n=== ARQUIVO EXPORTADO ===")
        print(f"Dados salvos em: {nome_arquivo}")


def main():
    """CLI para simulação de energia solar."""
    parser = argparse.ArgumentParser(
        description="Simulador de economia com energia solar",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Parâmetros do sistema
    parser.add_argument("--tarifa-inicial", type=float, default=0.973,
                        help="Tarifa total inicial (R$/kWh)")
    parser.add_argument("--fio-b-inicial", type=float, default=0.69568,
                        help="Tarifa Fio B inicial (R$/kWh)")
    parser.add_argument("--geracao-mensal", type=float, default=1346.64,
                        help="Geração mensal média do sistema (kWh)")
    parser.add_argument("--consumo-mensal", type=float, default=1237.17,
                        help="Consumo mensal da residência (kWh)")
    parser.add_argument("--autoconsumo", type=float, default=0.20,
                        help="Percentual de autoconsumo instantâneo (0-1)")

    # Parâmetros financeiros
    parser.add_argument("--parcela", type=float, default=750,
                        help="Valor da parcela do financiamento (R$/mês)")
    parser.add_argument("--meses-financiamento", type=int, default=72,
                        help="Duração do financiamento em meses")
    parser.add_argument("--manutencao-anual", type=float, default=750,
                        help="Custo anual de manutenção/limpeza (R$/ano)")

    # Parâmetros de simulação
    parser.add_argument("--anos", type=int, default=10,
                        help="Duração total da simulação em anos")
    parser.add_argument("--reajuste-anual", type=float, default=0.08,
                        help="Taxa de reajuste anual da tarifa (0-1)")
    parser.add_argument("--degradacao-anual", type=float, default=0.005,
                        help="Taxa de degradação anual das placas (0-1)")
    parser.add_argument("--ano-inicial", type=int, default=2026,
                        help="Ano inicial da simulação")

    # Opções de sazonalidade e exportação
    parser.add_argument("--sazonalidade", action="store_true",
                        help="Ativar variação sazonal de Florianópolis")
    parser.add_argument("--output", type=str, default="simulacao_solar.csv",
                        help="Nome do arquivo CSV de saída")
    parser.add_argument("--no-export", action="store_true",
                        help="Não exportar para CSV")

    args = parser.parse_args()

    # Executar simulação
    df = simular_solar(
        tarifa_inicial=args.tarifa_inicial,
        fio_b_inicial=args.fio_b_inicial,
        geracao_mensal_media=args.geracao_mensal,
        consumo_mensal=args.consumo_mensal,
        perc_autoconsumo=args.autoconsumo,
        valor_parcela=args.parcela,
        meses_financiamento=args.meses_financiamento,
        anos_simulacao=args.anos,
        reajuste_anual=args.reajuste_anual,
        custo_manutencao_anual=args.manutencao_anual,
        degradacao_anual=args.degradacao_anual,
        ano_inicial=args.ano_inicial,
        usar_sazonalidade=args.sazonalidade
    )

    # Exibir resultados
    exibir_resultados(
        df,
        meses_financiamento=args.meses_financiamento,
        exportar_csv=not args.no_export,
        nome_arquivo=args.output
    )


if __name__ == "__main__":
    main()
