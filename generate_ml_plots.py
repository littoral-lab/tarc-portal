"""
Script para gerar gráficos científicos de análises de Machine Learning
a partir dos dados de sensores para artigo científico.
ATUALIZADO: Tratamento visual de gaps temporais (dias sem dados).
"""

import os
import warnings
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# Configuração para gráficos científicos
plt.rcParams.update(
    {
        "font.size": 11,
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
    }
)

colors = sns.color_palette("Set2")
sns.set_palette(colors)


def prepare_compressed_axis(df, time_col="timestamp", gap_threshold_minutes=None):
    """
    Cria um eixo X artificial que remove gaps, sejam eles de dias ou de horas.

    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe com os dados.
    time_col : str
        Nome da coluna de tempo.
    gap_threshold_minutes : float (opcional)
        Se definido, qualquer intervalo maior que isso será cortado.
        Se None, o script calcula automático (5x a mediana do tempo de coleta).
    """
    df = df.copy().sort_values(time_col).reset_index(drop=True)

    # 1. Calcular diferença de tempo em minutos para cada ponto
    df["delta_s"] = df[time_col].diff().dt.total_seconds().fillna(0)
    df["delta_min"] = df["delta_s"] / 60.0

    # 2. Definir o limiar de corte (Threshold)
    if gap_threshold_minutes is None:
        # Lógica Automática: Pega a mediana dos intervalos (ex: sensor coleta a cada 5 min)
        # e define o gap como qualquer coisa maior que 5x ou 10x esse valor.
        # Filtramos zeros ou valores muito pequenos para evitar ruído
        intervals = df.loc[df["delta_min"] > 0.1, "delta_min"]
        median_rate = intervals.median()

        # Se não tiver dados suficientes, assume 60 minutos
        if np.isnan(median_rate):
            median_rate = 10

        # Define gap como algo 6x maior que o tempo normal de coleta
        gap_threshold_minutes = max(median_rate * 6, 60)
        print(
            f"   ℹ️ Limiar de gap calculado automaticamente: {gap_threshold_minutes:.1f} minutos"
        )

    # 3. Converter threshold para segundos
    threshold_s = gap_threshold_minutes * 60

    # 4. Criar o 'pulo visual' (gap visual)
    # Quando houver um gap, visualmente ele ocupará o espaço de apenas "2 passos normais"
    visual_step = df.loc[df["delta_s"] < threshold_s, "delta_s"].median()
    if np.isnan(visual_step) or visual_step == 0:
        visual_step = 60  # fallback

    gap_visual_size = visual_step * 2  # O tamanho visual do corte no gráfico

    # 5. Processar o eixo
    df["adj_delta"] = df["delta_s"]

    # Identificar onde ocorrem os gaps (intra-dia ou inter-dias)
    gap_mask = df["delta_s"] > threshold_s

    # Substituir o tempo real enorme pelo tempo visual pequeno
    df.loc[gap_mask, "adj_delta"] = gap_visual_size

    # Criar eixo X cumulativo para plotagem
    df["compressed_x"] = df["adj_delta"].cumsum()

    # Retornar DF e os pontos onde houve corte
    cut_points = df.loc[gap_mask, "compressed_x"].values
    cut_timestamps = df.loc[gap_mask, time_col].values

    return df, cut_points


def apply_date_ticks(ax, x_values, timestamps, num_ticks=8):
    """
    Aplica labels de data corretos no eixo X comprimido.
    """
    # Selecionar índices espaçados igualmente
    idx = np.linspace(0, len(x_values) - 1, num_ticks, dtype=int)

    tick_locs = x_values.iloc[idx]
    tick_labels = timestamps.iloc[idx].dt.strftime("%d/%m\n%H:%M")

    ax.set_xticks(tick_locs)
    ax.set_xticklabels(tick_labels, rotation=0, ha="center")


# ============================================================================
# CARREGAMENTO DOS DADOS
# ============================================================================
print("📊 Carregando dados...")
# Simulando carregamento (substitua pelo seu pd.read_csv real)
try:
    df = pd.read_csv("sensor_readings.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
except FileNotFoundError:
    print("❌ Arquivo não encontrado. Certifique-se que 'sensor_readings.csv' existe.")
    exit()

df = df[df["sensor_type"].isin(["temperatura", "umidade", "gas"])]
df = df.sort_values("timestamp")
os.makedirs("figures", exist_ok=True)


# ============================================================================
# GRÁFICO 1: Série Temporal com Clusters (EIXO COMPRIMIDO)
# ============================================================================
print("\n🔷 Gerando gráfico de Clustering (Temperatura - Eixo Comprimido)...")

temp_data = df[df["sensor_type"] == "temperatura"].copy()
temp_data = temp_data.sort_values("timestamp")
temp_data = temp_data[temp_data["value"] >= 20]

if len(temp_data) >= 10:
    # 1. Preparar Eixo Comprimido (Remove gaps > 12 horas)
    # temp_data_comp, gaps = prepare_compressed_axis(temp_data, max_gap_hours=12)
    temp_data_comp, gaps = prepare_compressed_axis(temp_data, gap_threshold_minutes=60)

    # Clustering (lógica original mantida)
    values = temp_data_comp["value"].values.reshape(-1, 1)
    scaler = StandardScaler()
    clusters = KMeans(n_clusters=3, random_state=42, n_init=10).fit_predict(
        scaler.fit_transform(values)
    )

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    ax1 = axes[0]

    # Plotar usando o eixo comprimido
    for cluster_id in range(3):
        mask = clusters == cluster_id
        # Scatter
        ax1.scatter(
            temp_data_comp.loc[mask, "compressed_x"],
            temp_data_comp.loc[mask, "value"],
            c=[plt.cm.viridis(cluster_id / 3)],
            label=f"Cluster {cluster_id + 1}",
            s=20,
            alpha=0.6,
            edgecolors="black",
            linewidths=0.3,
        )

    # Adicionar linhas verticais pontilhadas onde houve corte de tempo (gap)
    for gap_x in gaps:
        ax1.axvline(x=gap_x, color="gray", linestyle=":", alpha=0.4, linewidth=1)
        # ax1.axvline(
        #     x=gap_x - (gap_x * 0.001),
        #     color="gray",
        #     linestyle=":",
        #     alpha=0.5,
        #     linewidth=1.5,
        # )
        # Opcional: Adicionar texto "Gap"
        # ax1.text(gap_x, ax1.get_ylim()[0], "//", ha='center', va='bottom', color='gray')

    # Ajustar Ticks do Eixo X
    # apply_date_ticks(ax1, temp_data_comp["compressed_x"], temp_data_comp["timestamp"])
    apply_date_ticks(
        ax1, temp_data_comp["compressed_x"], temp_data_comp["timestamp"], num_ticks=10
    )

    ax1.set_xlabel("Tempo", fontweight="bold")
    ax1.set_ylabel("Temperatura (°C)", fontweight="bold")
    ax1.set_title("(a) Análise de Clustering: Temperatura", fontweight="bold")
    ax1.grid(True, alpha=0.3, linestyle="--")
    ax1.legend(loc="upper right")

    # Subplot 2 (Estatísticas - inalterado)
    ax2 = axes[1]
    # ... (código de estatísticas de barras mantido igual ao original) ...
    cluster_stats = []
    for i in range(3):
        vals = temp_data_comp["value"][clusters == i]
        cluster_stats.append(
            {"mean": vals.mean(), "std": vals.std(), "count": len(vals)}
        )

    # Plot barras simples para economizar espaço aqui
    means = [c["mean"] for c in cluster_stats]
    stds = [c["std"] for c in cluster_stats]
    ax2.bar(
        range(3),
        means,
        yerr=stds,
        color=[plt.cm.viridis(i / 3) for i in range(3)],
        capsize=5,
        alpha=0.8,
        edgecolor="k",
    )
    ax2.set_xticks(range(3))
    ax2.set_xticklabels([f"Cluster {i + 1}" for i in range(3)])
    ax2.set_ylabel("Temp. Média (°C)", fontweight="bold")
    ax2.set_title("(b) Estatísticas por Cluster", fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig("figures/fig1_clustering_temperatura_no_gaps.pdf")
    plt.savefig("figures/fig1_clustering_temperatura_no_gaps.png")
    print("   ✅ Salvo: fig1_clustering_temperatura_no_gaps")
    plt.close()


# ============================================================================
# GRÁFICO 4: Comparação Multi-Sensor (EIXO COMPRIMIDO)
# ============================================================================
print("\n📊 Gerando gráfico de Comparação Multi-Sensor (Eixo Comprimido)...")

# Preparação dos dados (Agrupamento por hora)
temp_agg = (
    df[df["sensor_type"] == "temperatura"]
    .set_index("timestamp")
    .resample("1H")["value"]
    .mean()
    .reset_index()
)
umid_agg = (
    df[df["sensor_type"] == "umidade"]
    .set_index("timestamp")
    .resample("1H")["value"]
    .mean()
    .reset_index()
)

merged = pd.merge(
    temp_agg, umid_agg, on="timestamp", suffixes=("_temp", "_umid")
).dropna()

if len(merged) > 0:
    # Aplicar compressão de tempo no dataset combinado
    # merged_comp, gaps_merged = prepare_compressed_axis(merged, max_gap_hours=12)
    merged_comp, gaps_merged = prepare_compressed_axis(merged, gap_threshold_minutes=60)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    ax1 = axes[0]
    ax1_twin = ax1.twinx()

    # Plotar Temperatura (Linha Vermelha)
    ax1.plot(
        merged_comp["compressed_x"],
        merged_comp["value_temp"],
        color="red",
        label="Temperatura",
        linewidth=1.5,
        alpha=0.8,
    )

    # Plotar Umidade (Linha Azul)
    ax1_twin.plot(
        merged_comp["compressed_x"],
        merged_comp["value_umid"],
        color="blue",
        label="Umidade",
        linewidth=1.5,
        alpha=0.8,
    )

    # Marcar Gaps
    for gap_x in gaps_merged:
        ax1.axvline(x=gap_x, color="gray", linestyle=":", alpha=0.5)

    # Configurar Eixo X
    apply_date_ticks(ax1, merged_comp["compressed_x"], merged_comp["timestamp"])

    ax1.set_xlabel("Tempo (Escala não linear nos gaps)", fontweight="bold")
    ax1.set_ylabel("Temp (°C)", color="red", fontweight="bold")
    ax1_twin.set_ylabel("Umidade (%)", color="blue", fontweight="bold")
    ax1.set_title(
        "(a) Comparação Temporal (Dias sem dados ocultados)", fontweight="bold"
    )

    # Legendas
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    # Subplot 2: Correlação (Scatter não depende do tempo, então permanece igual)
    ax2 = axes[1]
    sc = ax2.scatter(
        merged["value_temp"],
        merged["value_umid"],
        c=range(len(merged)),
        cmap="viridis",
        alpha=0.6,
    )
    # Linha de tendência
    z = np.polyfit(merged["value_temp"], merged["value_umid"], 1)
    p = np.poly1d(z)
    ax2.plot(
        merged["value_temp"],
        p(merged["value_temp"]),
        "r--",
        label=f"R={merged['value_temp'].corr(merged['value_umid']):.2f}",
    )

    ax2.set_xlabel("Temperatura (°C)", fontweight="bold")
    ax2.set_ylabel("Umidade (%)", fontweight="bold")
    ax2.set_title("(b) Correlação", fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("figures/fig4_comparacao_multisensor_no_gaps.pdf")
    plt.savefig("figures/fig4_comparacao_multisensor_no_gaps.png")
    print("   ✅ Salvo: fig4_comparacao_multisensor_no_gaps")
    plt.close()

print("\n✅ Processo finalizado. Gráficos sem espaços vazios gerados.")
