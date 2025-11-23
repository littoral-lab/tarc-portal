# Geração de Gráficos Científicos para Artigo

Este script gera gráficos científicos de alta qualidade para artigo científico usando os algoritmos de Machine Learning implementados na plataforma.

## Requisitos

O script usa um ambiente virtual localizado em `.venv`. Para instalar as dependências:

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
pip install pandas numpy matplotlib seaborn scikit-learn
```

## Execução

```bash
# Ativar ambiente virtual (se ainda não estiver ativado)
source .venv/bin/activate

# Executar script
python generate_ml_plots.py
```

Ou diretamente com o Python do ambiente virtual:

```bash
.venv/bin/python generate_ml_plots.py
```

## Gráficos Gerados

O script gera 5 gráficos científicos:

1. **fig1_clustering_temperatura**: Análise de clustering (K-Means) aplicada à temperatura
   - Série temporal com clusters identificados
   - Estatísticas por cluster

2. **fig2_predicao_temperatura**: Predição de valores futuros usando Random Forest
   - Comparação entre dados reais e predições
   - Importância das features no modelo

3. **fig3_classificacao_umidade**: Classificação automática de umidade
   - Série temporal com classes (Baixo/Normal/Alto)
   - Distribuição de classes

4. **fig4_comparacao_multisensor**: Análise comparativa entre sensores
   - Série temporal comparativa (Temperatura vs Umidade)
   - Análise de correlação

5. **fig5_padroes_temporais_gas**: Padrões temporais na concentração de gás
   - Padrão por hora do dia
   - Padrão por dia da semana

## Formato dos Arquivos

- **PDF**: Ideal para inclusão em LaTeX (alta qualidade vetorial)
- **PNG**: Para visualização rápida e apresentações

## Uso no LaTeX

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{figures/fig1_clustering_temperatura.pdf}
    \caption{Análise de clustering aplicada aos dados de temperatura.}
    \label{fig:clustering}
\end{figure}
```

