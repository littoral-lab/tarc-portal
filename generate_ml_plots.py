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

# Criar estrutura de pastas para organizar as figuras
os.makedirs("figures/temperatura", exist_ok=True)
os.makedirs("figures/umidade", exist_ok=True)
os.makedirs("figures/gas", exist_ok=True)
os.makedirs("figures/comparacao", exist_ok=True)


# ============================================================================
# GRÁFICO 1: Série Temporal com Clusters (EIXO COMPRIMIDO)
# ============================================================================
print("\n🔷 Gerando gráfico de Clustering (Temperatura - Eixo Comprimido)...")

temp_data = df[df["sensor_type"] == "temperatura"].copy()
temp_data = temp_data.sort_values("timestamp")
temp_data = temp_data[(temp_data["value"] >= 20) & (temp_data["value"] <= 34)]

if len(temp_data) >= 10:
    # 1. Preparar Eixo Comprimido (Remove gaps > 12 horas)
    temp_data_comp, gaps = prepare_compressed_axis(temp_data, gap_threshold_minutes=60)

    # Clustering
    values = temp_data_comp["value"].values.reshape(-1, 1)
    scaler = StandardScaler()
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaler.fit_transform(values))

    # Calcular estatísticas dos clusters
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_stats = []
    for i in range(3):
        vals = temp_data_comp["value"][clusters == i]
        cluster_stats.append(
            {
                "mean": vals.mean(),
                "std": vals.std(),
                "min": vals.min(),
                "max": vals.max(),
                "count": len(vals),
            }
        )

    # Criar figura única (mais limpa)
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

    # Plotar scatter com cores dos clusters
    for cluster_id in range(3):
        mask = clusters == cluster_id
        cluster_color = plt.cm.viridis(cluster_id / 3)

        # Scatter plot
        ax1.scatter(
            temp_data_comp.loc[mask, "compressed_x"],
            temp_data_comp.loc[mask, "value"],
            c=[cluster_color],
            label=f"Cluster {cluster_id + 1} (n={cluster_stats[cluster_id]['count']}, μ={cluster_stats[cluster_id]['mean']:.1f}°C)",
            s=25,
            alpha=0.7,
            edgecolors="black",
            linewidths=0.4,
            zorder=3,
        )

        # Adicionar linha horizontal no centro do cluster
        center_value = cluster_centers[cluster_id][0]
        ax1.axhline(
            y=center_value,
            color=cluster_color,
            linestyle="--",
            linewidth=2,
            alpha=0.6,
            zorder=1,
        )

    # Adicionar linhas verticais para gaps
    for gap_x in gaps:
        ax1.axvline(
            x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
        )

    # Ajustar Ticks do Eixo X
    apply_date_ticks(
        ax1, temp_data_comp["compressed_x"], temp_data_comp["timestamp"], num_ticks=10
    )

    ax1.set_xlabel("Tempo", fontweight="bold")
    ax1.set_ylabel("Temperatura (°C)", fontweight="bold")
    ax1.set_title(
        "Análise de Clustering: Série Temporal de Temperatura",
        fontweight="bold",
        pad=15,
    )
    ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
    ax1.legend(loc="upper left", framealpha=0.95, fontsize=9)

    # Adicionar caixa de texto com estatísticas resumidas
    stats_text = "Estatísticas dos Clusters:\n"
    for i in range(3):
        stats_text += f"Cluster {i + 1}: {cluster_stats[i]['mean']:.1f}°C ± {cluster_stats[i]['std']:.1f}°C\n"

    # Posicionar caixa de texto no canto superior direito
    ax1.text(
        0.98,
        0.98,
        stats_text.strip(),
        transform=ax1.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        family="monospace",
    )

    plt.tight_layout()
    plt.savefig("figures/temperatura/clustering_temperatura.pdf", bbox_inches="tight")
    plt.savefig("figures/temperatura/clustering_temperatura.png", bbox_inches="tight")
    print("   ✅ Salvo: figures/temperatura/clustering_temperatura")
    plt.close()


# ============================================================================
# GRÁFICO 2: Predição de Temperatura (Random Forest Regressor)
# ============================================================================
print("\n🔮 Gerando gráfico de Predição (Temperatura - Eixo Comprimido)...")

temp_data_pred = df[df["sensor_type"] == "temperatura"].copy()
temp_data_pred = temp_data_pred.sort_values("timestamp")
temp_data_pred = temp_data_pred[
    (temp_data_pred["value"] >= 20) & (temp_data_pred["value"] <= 34)
]

if len(temp_data_pred) >= 50:
    # Preparar eixo comprimido
    temp_data_pred_comp, gaps_pred = prepare_compressed_axis(
        temp_data_pred, gap_threshold_minutes=60
    )

    # Criar features temporais
    temp_data_pred_comp["hour"] = temp_data_pred_comp["timestamp"].dt.hour
    temp_data_pred_comp["day_of_week"] = temp_data_pred_comp["timestamp"].dt.weekday
    temp_data_pred_comp["day_of_year"] = temp_data_pred_comp["timestamp"].dt.dayofyear

    # Criar features de lag
    temp_data_pred_comp["lag_1"] = temp_data_pred_comp["value"].shift(1)
    temp_data_pred_comp["lag_2"] = temp_data_pred_comp["value"].shift(2)
    temp_data_pred_comp["lag_3"] = temp_data_pred_comp["value"].shift(3)

    # Remover NaN
    temp_data_pred_comp = temp_data_pred_comp.dropna()

    if len(temp_data_pred_comp) >= 20:
        # Preparar dados
        X = temp_data_pred_comp[
            ["hour", "day_of_week", "day_of_year", "lag_1", "lag_2", "lag_3"]
        ]
        y = temp_data_pred_comp["value"]

        # Dividir em treino e teste (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Treinar modelo
        model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        model.fit(X_train, y_train)

        # Predições
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Calcular métricas
        r2_train = r2_score(y_train, y_pred_train)
        r2_test = r2_score(y_test, y_pred_test)
        mae_test = np.mean(np.abs(y_test - y_pred_test))
        rmse_test = np.sqrt(np.mean((y_test - y_pred_test) ** 2))

        # Criar figura
        fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

        # Plotar dados reais
        ax1.plot(
            temp_data_pred_comp["compressed_x"],
            temp_data_pred_comp["value"],
            color="blue",
            label="Valores Reais",
            linewidth=1.5,
            alpha=0.7,
            zorder=2,
        )

        # Plotar predições (treino e teste)
        train_x = temp_data_pred_comp.iloc[:split_idx]["compressed_x"]
        test_x = temp_data_pred_comp.iloc[split_idx:]["compressed_x"]

        ax1.plot(
            train_x,
            y_pred_train,
            color="green",
            label="Predições (Treino)",
            linewidth=1.5,
            alpha=0.6,
            linestyle="--",
            zorder=3,
        )

        ax1.plot(
            test_x,
            y_pred_test,
            color="red",
            label="Predições (Teste)",
            linewidth=1.5,
            alpha=0.8,
            linestyle="--",
            zorder=3,
        )

        # Marcar linha de divisão treino/teste
        split_x = temp_data_pred_comp.iloc[split_idx]["compressed_x"]
        ax1.axvline(
            x=split_x,
            color="orange",
            linestyle="-",
            linewidth=2,
            alpha=0.5,
            label="Divisão Treino/Teste",
            zorder=1,
        )

        # Adicionar linhas verticais para gaps
        for gap_x in gaps_pred:
            ax1.axvline(
                x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
            )

        # Ajustar ticks do eixo X
        apply_date_ticks(
            ax1,
            temp_data_pred_comp["compressed_x"],
            temp_data_pred_comp["timestamp"],
            num_ticks=10,
        )

        ax1.set_xlabel("Tempo", fontweight="bold")
        ax1.set_ylabel("Temperatura (°C)", fontweight="bold")
        ax1.set_title(
            "Análise de Predição: Série Temporal de Temperatura (Random Forest)",
            fontweight="bold",
            pad=15,
        )
        ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
        ax1.legend(loc="upper left", framealpha=0.95, fontsize=9)

        # Adicionar caixa de texto com métricas
        metrics_text = f"Métricas de Performance:\n"
        metrics_text += f"R² (Treino): {r2_train:.3f}\n"
        metrics_text += f"R² (Teste): {r2_test:.3f}\n"
        metrics_text += f"MAE (Teste): {mae_test:.2f}°C\n"
        metrics_text += f"RMSE (Teste): {rmse_test:.2f}°C"

        ax1.text(
            0.98,
            0.98,
            metrics_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
            family="monospace",
        )

        plt.tight_layout()
        plt.savefig("figures/temperatura/predicao_temperatura.pdf", bbox_inches="tight")
        plt.savefig("figures/temperatura/predicao_temperatura.png", bbox_inches="tight")
        print("   ✅ Salvo: figures/temperatura/predicao_temperatura")
        plt.close()


# ============================================================================
# GRÁFICO 3: Classificação de Temperatura (Random Forest Classifier)
# ============================================================================
print("\n🎯 Gerando gráfico de Classificação (Temperatura - Eixo Comprimido)...")

temp_data_class = df[df["sensor_type"] == "temperatura"].copy()
temp_data_class = temp_data_class.sort_values("timestamp")
temp_data_class = temp_data_class[
    (temp_data_class["value"] >= 20) & (temp_data_class["value"] <= 34)
]

if len(temp_data_class) >= 50:
    # Preparar eixo comprimido
    temp_data_class_comp, gaps_class = prepare_compressed_axis(
        temp_data_class, gap_threshold_minutes=60
    )

    # Criar classes baseadas em quartis
    q1 = temp_data_class_comp["value"].quantile(0.33)
    q2 = temp_data_class_comp["value"].quantile(0.67)

    def classify_temp(value):
        if value < q1:
            return 0  # Baixa
        elif value < q2:
            return 1  # Média
        else:
            return 2  # Alta

    temp_data_class_comp["class"] = temp_data_class_comp["value"].apply(classify_temp)

    # Criar features temporais
    temp_data_class_comp["hour"] = temp_data_class_comp["timestamp"].dt.hour
    temp_data_class_comp["day_of_week"] = temp_data_class_comp["timestamp"].dt.weekday
    temp_data_class_comp["day_of_year"] = temp_data_class_comp["timestamp"].dt.dayofyear

    # Criar features de lag
    temp_data_class_comp["lag_1"] = temp_data_class_comp["value"].shift(1)
    temp_data_class_comp["lag_2"] = temp_data_class_comp["value"].shift(2)
    temp_data_class_comp["lag_3"] = temp_data_class_comp["value"].shift(3)

    # Remover NaN
    temp_data_class_comp = temp_data_class_comp.dropna()

    if len(temp_data_class_comp) >= 20:
        # Preparar dados
        X = temp_data_class_comp[
            ["hour", "day_of_week", "day_of_year", "lag_1", "lag_2", "lag_3"]
        ]
        y = temp_data_class_comp["class"]

        # Dividir em treino e teste (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Treinar modelo
        model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        model.fit(X_train, y_train)

        # Predições
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Calcular métricas
        accuracy_train = accuracy_score(y_train, y_pred_train)
        accuracy_test = accuracy_score(y_test, y_pred_test)

        # Criar figura
        fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

        # Definir cores para classes
        class_colors = ["blue", "orange", "red"]
        class_labels = ["Baixa", "Média", "Alta"]
        class_thresholds = [q1, q2]

        # Plotar valores reais com cores por classe
        for class_id in range(3):
            mask = temp_data_class_comp["class"] == class_id
            ax1.scatter(
                temp_data_class_comp.loc[mask, "compressed_x"],
                temp_data_class_comp.loc[mask, "value"],
                c=class_colors[class_id],
                label=f"Classe {class_labels[class_id]} (Real)",
                s=25,
                alpha=0.6,
                edgecolors="black",
                linewidths=0.3,
                zorder=3,
            )

        # Plotar predições (teste) com marcadores diferentes
        test_mask = temp_data_class_comp.index[split_idx:]
        test_x = temp_data_class_comp.loc[test_mask, "compressed_x"]
        test_y = temp_data_class_comp.loc[test_mask, "value"]

        for class_id in range(3):
            mask = y_pred_test == class_id
            if mask.sum() > 0:
                ax1.scatter(
                    test_x[mask],
                    test_y[mask],
                    c=class_colors[class_id],
                    marker="X",
                    s=80,
                    alpha=0.8,
                    edgecolors="black",
                    linewidths=1,
                    label=f"Predição: {class_labels[class_id]}",
                    zorder=4,
                )

        # Adicionar linhas horizontais para limites das classes
        ax1.axhline(
            y=q1,
            color="gray",
            linestyle="--",
            linewidth=1.5,
            alpha=0.5,
            label=f"Limite Baixa/Média ({q1:.1f}°C)",
            zorder=1,
        )
        ax1.axhline(
            y=q2,
            color="gray",
            linestyle="--",
            linewidth=1.5,
            alpha=0.5,
            label=f"Limite Média/Alta ({q2:.1f}°C)",
            zorder=1,
        )

        # Marcar linha de divisão treino/teste
        split_x = temp_data_class_comp.iloc[split_idx]["compressed_x"]
        ax1.axvline(
            x=split_x,
            color="orange",
            linestyle="-",
            linewidth=2,
            alpha=0.5,
            label="Divisão Treino/Teste",
            zorder=2,
        )

        # Adicionar linhas verticais para gaps
        for gap_x in gaps_class:
            ax1.axvline(
                x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
            )

        # Ajustar ticks do eixo X
        apply_date_ticks(
            ax1,
            temp_data_class_comp["compressed_x"],
            temp_data_class_comp["timestamp"],
            num_ticks=10,
        )

        ax1.set_xlabel("Tempo", fontweight="bold")
        ax1.set_ylabel("Temperatura (°C)", fontweight="bold")
        ax1.set_title(
            "Análise de Classificação: Série Temporal de Temperatura (Random Forest)",
            fontweight="bold",
            pad=15,
        )
        ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
        ax1.legend(loc="upper left", framealpha=0.95, fontsize=8, ncol=2)

        # Adicionar caixa de texto com métricas
        metrics_text = f"Métricas de Performance:\n"
        metrics_text += f"Acurácia (Treino): {accuracy_train:.3f}\n"
        metrics_text += f"Acurácia (Teste): {accuracy_test:.3f}\n"
        metrics_text += f"\nLimites das Classes:\n"
        metrics_text += f"Baixa: < {q1:.1f}°C\n"
        metrics_text += f"Média: {q1:.1f}°C - {q2:.1f}°C\n"
        metrics_text += f"Alta: ≥ {q2:.1f}°C"

        # Caixa de texto com zorder alto para ficar acima dos pontos
        ax1.text(
            0.98,
            0.98,
            metrics_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(
                boxstyle="round",
                facecolor="lightgreen",
                alpha=0.95,
                edgecolor="black",
                linewidth=1,
            ),
            family="monospace",
            zorder=10,
        )

        plt.tight_layout()
        plt.savefig(
            "figures/temperatura/classificacao_temperatura.pdf", bbox_inches="tight"
        )
        plt.savefig(
            "figures/temperatura/classificacao_temperatura.png", bbox_inches="tight"
        )
        print("   ✅ Salvo: figures/temperatura/classificacao_temperatura")
        plt.close()


# ============================================================================
# GRÁFICO 4: Clustering de Umidade (K-Means)
# ============================================================================
print("\n🔷 Gerando gráfico de Clustering (Umidade - Eixo Comprimido)...")

umidade_data = df[df["sensor_type"] == "umidade"].copy()
umidade_data = umidade_data.sort_values("timestamp")
umidade_data = umidade_data[
    (umidade_data["value"] >= 20) & (umidade_data["value"] <= 100)
]

if len(umidade_data) >= 10:
    # Preparar Eixo Comprimido
    umidade_data_comp, gaps_umid = prepare_compressed_axis(
        umidade_data, gap_threshold_minutes=60
    )

    # Clustering
    values = umidade_data_comp["value"].values.reshape(-1, 1)
    scaler = StandardScaler()
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaler.fit_transform(values))

    # Calcular estatísticas dos clusters
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_stats = []
    for i in range(3):
        vals = umidade_data_comp["value"][clusters == i]
        cluster_stats.append(
            {
                "mean": vals.mean(),
                "std": vals.std(),
                "min": vals.min(),
                "max": vals.max(),
                "count": len(vals),
            }
        )

    # Criar figura única
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

    # Plotar scatter com cores dos clusters
    for cluster_id in range(3):
        mask = clusters == cluster_id
        cluster_color = plt.cm.viridis(cluster_id / 3)

        # Scatter plot
        ax1.scatter(
            umidade_data_comp.loc[mask, "compressed_x"],
            umidade_data_comp.loc[mask, "value"],
            c=[cluster_color],
            label=f"Cluster {cluster_id + 1} (n={cluster_stats[cluster_id]['count']}, μ={cluster_stats[cluster_id]['mean']:.1f}%)",
            s=25,
            alpha=0.7,
            edgecolors="black",
            linewidths=0.4,
            zorder=3,
        )

        # Adicionar linha horizontal no centro do cluster
        center_value = cluster_centers[cluster_id][0]
        ax1.axhline(
            y=center_value,
            color=cluster_color,
            linestyle="--",
            linewidth=2,
            alpha=0.6,
            zorder=1,
        )

    # Adicionar linhas verticais para gaps
    for gap_x in gaps_umid:
        ax1.axvline(
            x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
        )

    # Ajustar Ticks do Eixo X
    apply_date_ticks(
        ax1,
        umidade_data_comp["compressed_x"],
        umidade_data_comp["timestamp"],
        num_ticks=10,
    )

    ax1.set_xlabel("Tempo", fontweight="bold")
    ax1.set_ylabel("Umidade (%)", fontweight="bold")
    ax1.set_title(
        "Análise de Clustering: Série Temporal de Umidade",
        fontweight="bold",
        pad=15,
    )
    ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
    ax1.legend(loc="upper left", framealpha=0.95, fontsize=9)

    # Adicionar caixa de texto com estatísticas resumidas
    stats_text = "Estatísticas dos Clusters:\n"
    for i in range(3):
        stats_text += f"Cluster {i + 1}: {cluster_stats[i]['mean']:.1f}% ± {cluster_stats[i]['std']:.1f}%\n"

    # Posicionar caixa de texto no canto superior direito
    ax1.text(
        0.98,
        0.98,
        stats_text.strip(),
        transform=ax1.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        family="monospace",
    )

    plt.tight_layout()
    plt.savefig("figures/umidade/clustering_umidade.pdf", bbox_inches="tight")
    plt.savefig("figures/umidade/clustering_umidade.png", bbox_inches="tight")
    print("   ✅ Salvo: figures/umidade/clustering_umidade")
    plt.close()


# ============================================================================
# GRÁFICO 5: Predição de Umidade (Random Forest Regressor)
# ============================================================================
print("\n🔮 Gerando gráfico de Predição (Umidade - Eixo Comprimido)...")

umidade_data_pred = df[df["sensor_type"] == "umidade"].copy()
umidade_data_pred = umidade_data_pred.sort_values("timestamp")
umidade_data_pred = umidade_data_pred[
    (umidade_data_pred["value"] >= 20) & (umidade_data_pred["value"] <= 100)
]

if len(umidade_data_pred) >= 50:
    # Preparar eixo comprimido
    umidade_data_pred_comp, gaps_pred_umid = prepare_compressed_axis(
        umidade_data_pred, gap_threshold_minutes=60
    )

    # Criar features temporais
    umidade_data_pred_comp["hour"] = umidade_data_pred_comp["timestamp"].dt.hour
    umidade_data_pred_comp["day_of_week"] = umidade_data_pred_comp[
        "timestamp"
    ].dt.weekday
    umidade_data_pred_comp["day_of_year"] = umidade_data_pred_comp[
        "timestamp"
    ].dt.dayofyear

    # Criar features de lag
    umidade_data_pred_comp["lag_1"] = umidade_data_pred_comp["value"].shift(1)
    umidade_data_pred_comp["lag_2"] = umidade_data_pred_comp["value"].shift(2)
    umidade_data_pred_comp["lag_3"] = umidade_data_pred_comp["value"].shift(3)

    # Remover NaN
    umidade_data_pred_comp = umidade_data_pred_comp.dropna()

    if len(umidade_data_pred_comp) >= 20:
        # Preparar dados
        X = umidade_data_pred_comp[
            ["hour", "day_of_week", "day_of_year", "lag_1", "lag_2", "lag_3"]
        ]
        y = umidade_data_pred_comp["value"]

        # Dividir em treino e teste (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Treinar modelo
        model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        model.fit(X_train, y_train)

        # Predições
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Calcular métricas
        r2_train = r2_score(y_train, y_pred_train)
        r2_test = r2_score(y_test, y_pred_test)
        mae_test = np.mean(np.abs(y_test - y_pred_test))
        rmse_test = np.sqrt(np.mean((y_test - y_pred_test) ** 2))

        # Criar figura
        fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

        # Plotar dados reais
        ax1.plot(
            umidade_data_pred_comp["compressed_x"],
            umidade_data_pred_comp["value"],
            color="blue",
            label="Valores Reais",
            linewidth=1.5,
            alpha=0.7,
            zorder=2,
        )

        # Plotar predições (treino e teste)
        train_x = umidade_data_pred_comp.iloc[:split_idx]["compressed_x"]
        test_x = umidade_data_pred_comp.iloc[split_idx:]["compressed_x"]

        ax1.plot(
            train_x,
            y_pred_train,
            color="green",
            label="Predições (Treino)",
            linewidth=1.5,
            alpha=0.6,
            linestyle="--",
            zorder=3,
        )

        ax1.plot(
            test_x,
            y_pred_test,
            color="red",
            label="Predições (Teste)",
            linewidth=1.5,
            alpha=0.8,
            linestyle="--",
            zorder=3,
        )

        # Marcar linha de divisão treino/teste
        split_x = umidade_data_pred_comp.iloc[split_idx]["compressed_x"]
        ax1.axvline(
            x=split_x,
            color="orange",
            linestyle="-",
            linewidth=2,
            alpha=0.5,
            label="Divisão Treino/Teste",
            zorder=1,
        )

        # Adicionar linhas verticais para gaps
        for gap_x in gaps_pred_umid:
            ax1.axvline(
                x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
            )

        # Ajustar ticks do eixo X
        apply_date_ticks(
            ax1,
            umidade_data_pred_comp["compressed_x"],
            umidade_data_pred_comp["timestamp"],
            num_ticks=10,
        )

        ax1.set_xlabel("Tempo", fontweight="bold")
        ax1.set_ylabel("Umidade (%)", fontweight="bold")
        ax1.set_title(
            "Análise de Predição: Série Temporal de Umidade (Random Forest)",
            fontweight="bold",
            pad=15,
        )
        ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
        ax1.legend(loc="upper left", framealpha=0.95, fontsize=9)

        # Adicionar caixa de texto com métricas
        metrics_text = f"Métricas de Performance:\n"
        metrics_text += f"R² (Treino): {r2_train:.3f}\n"
        metrics_text += f"R² (Teste): {r2_test:.3f}\n"
        metrics_text += f"MAE (Teste): {mae_test:.2f}%\n"
        metrics_text += f"RMSE (Teste): {rmse_test:.2f}%"

        ax1.text(
            0.98,
            0.98,
            metrics_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
            family="monospace",
        )

        plt.tight_layout()
        plt.savefig("figures/umidade/predicao_umidade.pdf", bbox_inches="tight")
        plt.savefig("figures/umidade/predicao_umidade.png", bbox_inches="tight")
        print("   ✅ Salvo: figures/umidade/predicao_umidade")
        plt.close()


# ============================================================================
# GRÁFICO 6: Classificação de Umidade (Random Forest Classifier)
# ============================================================================
print("\n🎯 Gerando gráfico de Classificação (Umidade - Eixo Comprimido)...")

umidade_data_class = df[df["sensor_type"] == "umidade"].copy()
umidade_data_class = umidade_data_class.sort_values("timestamp")
umidade_data_class = umidade_data_class[
    (umidade_data_class["value"] >= 20) & (umidade_data_class["value"] <= 100)
]

if len(umidade_data_class) >= 50:
    # Preparar eixo comprimido
    umidade_data_class_comp, gaps_class_umid = prepare_compressed_axis(
        umidade_data_class, gap_threshold_minutes=60
    )

    # Criar classes baseadas em quartis
    q1 = umidade_data_class_comp["value"].quantile(0.33)
    q2 = umidade_data_class_comp["value"].quantile(0.67)

    def classify_umid(value):
        if value < q1:
            return 0  # Baixa
        elif value < q2:
            return 1  # Média
        else:
            return 2  # Alta

    umidade_data_class_comp["class"] = umidade_data_class_comp["value"].apply(
        classify_umid
    )

    # Criar features temporais
    umidade_data_class_comp["hour"] = umidade_data_class_comp["timestamp"].dt.hour
    umidade_data_class_comp["day_of_week"] = umidade_data_class_comp[
        "timestamp"
    ].dt.weekday
    umidade_data_class_comp["day_of_year"] = umidade_data_class_comp[
        "timestamp"
    ].dt.dayofyear

    # Criar features de lag
    umidade_data_class_comp["lag_1"] = umidade_data_class_comp["value"].shift(1)
    umidade_data_class_comp["lag_2"] = umidade_data_class_comp["value"].shift(2)
    umidade_data_class_comp["lag_3"] = umidade_data_class_comp["value"].shift(3)

    # Remover NaN
    umidade_data_class_comp = umidade_data_class_comp.dropna()

    if len(umidade_data_class_comp) >= 20:
        # Preparar dados
        X = umidade_data_class_comp[
            ["hour", "day_of_week", "day_of_year", "lag_1", "lag_2", "lag_3"]
        ]
        y = umidade_data_class_comp["class"]

        # Dividir em treino e teste (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Treinar modelo
        model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        model.fit(X_train, y_train)

        # Predições
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Calcular métricas
        accuracy_train = accuracy_score(y_train, y_pred_train)
        accuracy_test = accuracy_score(y_test, y_pred_test)

        # Criar figura
        fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

        # Definir cores para classes
        class_colors = ["blue", "orange", "red"]
        class_labels = ["Baixa", "Média", "Alta"]
        class_thresholds = [q1, q2]

        # Plotar valores reais com cores por classe
        for class_id in range(3):
            mask = umidade_data_class_comp["class"] == class_id
            ax1.scatter(
                umidade_data_class_comp.loc[mask, "compressed_x"],
                umidade_data_class_comp.loc[mask, "value"],
                c=class_colors[class_id],
                label=f"Classe {class_labels[class_id]} (Real)",
                s=25,
                alpha=0.6,
                edgecolors="black",
                linewidths=0.3,
                zorder=3,
            )

        # Plotar predições (teste) com marcadores diferentes
        test_mask = umidade_data_class_comp.index[split_idx:]
        test_x = umidade_data_class_comp.loc[test_mask, "compressed_x"]
        test_y = umidade_data_class_comp.loc[test_mask, "value"]

        for class_id in range(3):
            mask = y_pred_test == class_id
            if mask.sum() > 0:
                ax1.scatter(
                    test_x[mask],
                    test_y[mask],
                    c=class_colors[class_id],
                    marker="X",
                    s=80,
                    alpha=0.8,
                    edgecolors="black",
                    linewidths=1,
                    label=f"Predição: {class_labels[class_id]}",
                    zorder=4,
                )

        # Adicionar linhas horizontais para limites das classes
        ax1.axhline(
            y=q1,
            color="gray",
            linestyle="--",
            linewidth=1.5,
            alpha=0.5,
            label=f"Limite Baixa/Média ({q1:.1f}%)",
            zorder=1,
        )
        ax1.axhline(
            y=q2,
            color="gray",
            linestyle="--",
            linewidth=1.5,
            alpha=0.5,
            label=f"Limite Média/Alta ({q2:.1f}%)",
            zorder=1,
        )

        # Marcar linha de divisão treino/teste
        split_x = umidade_data_class_comp.iloc[split_idx]["compressed_x"]
        ax1.axvline(
            x=split_x,
            color="orange",
            linestyle="-",
            linewidth=2,
            alpha=0.5,
            label="Divisão Treino/Teste",
            zorder=2,
        )

        # Adicionar linhas verticais para gaps
        for gap_x in gaps_class_umid:
            ax1.axvline(
                x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
            )

        # Ajustar ticks do eixo X
        apply_date_ticks(
            ax1,
            umidade_data_class_comp["compressed_x"],
            umidade_data_class_comp["timestamp"],
            num_ticks=10,
        )

        ax1.set_xlabel("Tempo", fontweight="bold")
        ax1.set_ylabel("Umidade (%)", fontweight="bold")
        ax1.set_title(
            "Análise de Classificação: Série Temporal de Umidade (Random Forest)",
            fontweight="bold",
            pad=15,
        )
        ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
        ax1.legend(loc="upper left", framealpha=0.95, fontsize=8, ncol=2)

        # Adicionar caixa de texto com métricas
        metrics_text = f"Métricas de Performance:\n"
        metrics_text += f"Acurácia (Treino): {accuracy_train:.3f}\n"
        metrics_text += f"Acurácia (Teste): {accuracy_test:.3f}\n"
        metrics_text += f"\nLimites das Classes:\n"
        metrics_text += f"Baixa: < {q1:.1f}%\n"
        metrics_text += f"Média: {q1:.1f}% - {q2:.1f}%\n"
        metrics_text += f"Alta: ≥ {q2:.1f}%"

        # Caixa de texto com zorder alto para ficar acima dos pontos
        ax1.text(
            0.98,
            0.98,
            metrics_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(
                boxstyle="round",
                facecolor="lightgreen",
                alpha=0.95,
                edgecolor="black",
                linewidth=1,
            ),
            family="monospace",
            zorder=10,
        )

        plt.tight_layout()
        plt.savefig("figures/umidade/classificacao_umidade.pdf", bbox_inches="tight")
        plt.savefig("figures/umidade/classificacao_umidade.png", bbox_inches="tight")
        print("   ✅ Salvo: figures/umidade/classificacao_umidade")
        plt.close()


# ============================================================================
# GRÁFICO 7: Clustering de Gás (K-Means)
# ============================================================================
print("\n🔷 Gerando gráfico de Clustering (Gás - Eixo Comprimido)...")

gas_data = df[df["sensor_type"] == "gas"].copy()
gas_data = gas_data.sort_values("timestamp")
gas_data = gas_data[gas_data["value"] > 1600]

if len(gas_data) >= 10:
    # Preparar Eixo Comprimido
    gas_data_comp, gaps_gas = prepare_compressed_axis(
        gas_data, gap_threshold_minutes=60
    )

    # Clustering
    values = gas_data_comp["value"].values.reshape(-1, 1)
    scaler = StandardScaler()
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaler.fit_transform(values))

    # Calcular estatísticas dos clusters
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_stats = []
    for i in range(3):
        vals = gas_data_comp["value"][clusters == i]
        cluster_stats.append(
            {
                "mean": vals.mean(),
                "std": vals.std(),
                "min": vals.min(),
                "max": vals.max(),
                "count": len(vals),
            }
        )

    # Criar figura única
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

    # Plotar scatter com cores dos clusters
    for cluster_id in range(3):
        mask = clusters == cluster_id
        cluster_color = plt.cm.viridis(cluster_id / 3)

        # Scatter plot
        ax1.scatter(
            gas_data_comp.loc[mask, "compressed_x"],
            gas_data_comp.loc[mask, "value"],
            c=[cluster_color],
            label=f"Cluster {cluster_id + 1} (n={cluster_stats[cluster_id]['count']}, μ={cluster_stats[cluster_id]['mean']:.1f})",
            s=25,
            alpha=0.7,
            edgecolors="black",
            linewidths=0.4,
            zorder=3,
        )

        # Adicionar linha horizontal no centro do cluster
        center_value = cluster_centers[cluster_id][0]
        ax1.axhline(
            y=center_value,
            color=cluster_color,
            linestyle="--",
            linewidth=2,
            alpha=0.6,
            zorder=1,
        )

    # Adicionar linhas verticais para gaps
    for gap_x in gaps_gas:
        ax1.axvline(
            x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
        )

    # Ajustar Ticks do Eixo X
    apply_date_ticks(
        ax1,
        gas_data_comp["compressed_x"],
        gas_data_comp["timestamp"],
        num_ticks=10,
    )

    ax1.set_xlabel("Tempo", fontweight="bold")
    ax1.set_ylabel("Concentração de Gás", fontweight="bold")
    ax1.set_title(
        "Análise de Clustering: Série Temporal de Gás",
        fontweight="bold",
        pad=15,
    )
    ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
    ax1.legend(loc="upper left", framealpha=0.95, fontsize=9)

    # Adicionar caixa de texto com estatísticas resumidas
    stats_text = "Estatísticas dos Clusters:\n"
    for i in range(3):
        stats_text += f"Cluster {i + 1}: {cluster_stats[i]['mean']:.1f} ± {cluster_stats[i]['std']:.1f}\n"

    # Posicionar caixa de texto no canto superior direito
    ax1.text(
        0.98,
        0.98,
        stats_text.strip(),
        transform=ax1.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        family="monospace",
    )

    plt.tight_layout()
    plt.savefig("figures/gas/clustering_gas.pdf", bbox_inches="tight")
    plt.savefig("figures/gas/clustering_gas.png", bbox_inches="tight")
    print("   ✅ Salvo: figures/gas/clustering_gas")
    plt.close()


# ============================================================================
# GRÁFICO 8: Predição de Gás (Random Forest Regressor)
# ============================================================================
print("\n🔮 Gerando gráfico de Predição (Gás - Eixo Comprimido)...")

gas_data_pred = df[df["sensor_type"] == "gas"].copy()
gas_data_pred = gas_data_pred.sort_values("timestamp")
gas_data_pred = gas_data_pred[gas_data_pred["value"] > 1600]

if len(gas_data_pred) >= 50:
    # Preparar eixo comprimido
    gas_data_pred_comp, gaps_pred_gas = prepare_compressed_axis(
        gas_data_pred, gap_threshold_minutes=60
    )

    # Criar features temporais
    gas_data_pred_comp["hour"] = gas_data_pred_comp["timestamp"].dt.hour
    gas_data_pred_comp["day_of_week"] = gas_data_pred_comp["timestamp"].dt.weekday
    gas_data_pred_comp["day_of_year"] = gas_data_pred_comp["timestamp"].dt.dayofyear

    # Criar features de lag
    gas_data_pred_comp["lag_1"] = gas_data_pred_comp["value"].shift(1)
    gas_data_pred_comp["lag_2"] = gas_data_pred_comp["value"].shift(2)
    gas_data_pred_comp["lag_3"] = gas_data_pred_comp["value"].shift(3)

    # Remover NaN
    gas_data_pred_comp = gas_data_pred_comp.dropna()

    if len(gas_data_pred_comp) >= 20:
        # Preparar dados
        X = gas_data_pred_comp[
            ["hour", "day_of_week", "day_of_year", "lag_1", "lag_2", "lag_3"]
        ]
        y = gas_data_pred_comp["value"]

        # Dividir em treino e teste (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Treinar modelo
        model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        model.fit(X_train, y_train)

        # Predições
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Calcular métricas
        r2_train = r2_score(y_train, y_pred_train)
        r2_test = r2_score(y_test, y_pred_test)
        mae_test = np.mean(np.abs(y_test - y_pred_test))
        rmse_test = np.sqrt(np.mean((y_test - y_pred_test) ** 2))

        # Criar figura
        fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

        # Plotar dados reais
        ax1.plot(
            gas_data_pred_comp["compressed_x"],
            gas_data_pred_comp["value"],
            color="blue",
            label="Valores Reais",
            linewidth=1.5,
            alpha=0.7,
            zorder=2,
        )

        # Plotar predições (treino e teste)
        train_x = gas_data_pred_comp.iloc[:split_idx]["compressed_x"]
        test_x = gas_data_pred_comp.iloc[split_idx:]["compressed_x"]

        ax1.plot(
            train_x,
            y_pred_train,
            color="green",
            label="Predições (Treino)",
            linewidth=1.5,
            alpha=0.6,
            linestyle="--",
            zorder=3,
        )

        ax1.plot(
            test_x,
            y_pred_test,
            color="red",
            label="Predições (Teste)",
            linewidth=1.5,
            alpha=0.8,
            linestyle="--",
            zorder=3,
        )

        # Marcar linha de divisão treino/teste
        split_x = gas_data_pred_comp.iloc[split_idx]["compressed_x"]
        ax1.axvline(
            x=split_x,
            color="orange",
            linestyle="-",
            linewidth=2,
            alpha=0.5,
            label="Divisão Treino/Teste",
            zorder=1,
        )

        # Adicionar linhas verticais para gaps
        for gap_x in gaps_pred_gas:
            ax1.axvline(
                x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
            )

        # Ajustar ticks do eixo X
        apply_date_ticks(
            ax1,
            gas_data_pred_comp["compressed_x"],
            gas_data_pred_comp["timestamp"],
            num_ticks=10,
        )

        ax1.set_xlabel("Tempo", fontweight="bold")
        ax1.set_ylabel("Concentração de Gás", fontweight="bold")
        ax1.set_title(
            "Análise de Predição: Série Temporal de Gás (Random Forest)",
            fontweight="bold",
            pad=15,
        )
        ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
        ax1.legend(loc="upper left", framealpha=0.95, fontsize=9)

        # Adicionar caixa de texto com métricas
        metrics_text = f"Métricas de Performance:\n"
        metrics_text += f"R² (Treino): {r2_train:.3f}\n"
        metrics_text += f"R² (Teste): {r2_test:.3f}\n"
        metrics_text += f"MAE (Teste): {mae_test:.2f}\n"
        metrics_text += f"RMSE (Teste): {rmse_test:.2f}"

        ax1.text(
            0.98,
            0.98,
            metrics_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
            family="monospace",
        )

        plt.tight_layout()
        plt.savefig("figures/gas/predicao_gas.pdf", bbox_inches="tight")
        plt.savefig("figures/gas/predicao_gas.png", bbox_inches="tight")
        print("   ✅ Salvo: figures/gas/predicao_gas")
        plt.close()


# ============================================================================
# GRÁFICO 9: Classificação de Gás (Random Forest Classifier)
# ============================================================================
print("\n🎯 Gerando gráfico de Classificação (Gás - Eixo Comprimido)...")

gas_data_class = df[df["sensor_type"] == "gas"].copy()
gas_data_class = gas_data_class.sort_values("timestamp")
gas_data_class = gas_data_class[gas_data_class["value"] > 1600]

if len(gas_data_class) >= 50:
    # Preparar eixo comprimido
    gas_data_class_comp, gaps_class_gas = prepare_compressed_axis(
        gas_data_class, gap_threshold_minutes=60
    )

    # Criar classes baseadas em quartis
    q1 = gas_data_class_comp["value"].quantile(0.33)
    q2 = gas_data_class_comp["value"].quantile(0.67)

    def classify_gas(value):
        if value < q1:
            return 0  # Baixa
        elif value < q2:
            return 1  # Média
        else:
            return 2  # Alta

    gas_data_class_comp["class"] = gas_data_class_comp["value"].apply(classify_gas)

    # Criar features temporais
    gas_data_class_comp["hour"] = gas_data_class_comp["timestamp"].dt.hour
    gas_data_class_comp["day_of_week"] = gas_data_class_comp["timestamp"].dt.weekday
    gas_data_class_comp["day_of_year"] = gas_data_class_comp["timestamp"].dt.dayofyear

    # Criar features de lag
    gas_data_class_comp["lag_1"] = gas_data_class_comp["value"].shift(1)
    gas_data_class_comp["lag_2"] = gas_data_class_comp["value"].shift(2)
    gas_data_class_comp["lag_3"] = gas_data_class_comp["value"].shift(3)

    # Remover NaN
    gas_data_class_comp = gas_data_class_comp.dropna()

    if len(gas_data_class_comp) >= 20:
        # Preparar dados
        X = gas_data_class_comp[
            ["hour", "day_of_week", "day_of_year", "lag_1", "lag_2", "lag_3"]
        ]
        y = gas_data_class_comp["class"]

        # Dividir em treino e teste (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Treinar modelo
        model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        model.fit(X_train, y_train)

        # Predições
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Calcular métricas
        accuracy_train = accuracy_score(y_train, y_pred_train)
        accuracy_test = accuracy_score(y_test, y_pred_test)

        # Criar figura
        fig, ax1 = plt.subplots(1, 1, figsize=(12, 6))

        # Definir cores para classes
        class_colors = ["blue", "orange", "red"]
        class_labels = ["Baixa", "Média", "Alta"]
        class_thresholds = [q1, q2]

        # Plotar valores reais com cores por classe
        for class_id in range(3):
            mask = gas_data_class_comp["class"] == class_id
            ax1.scatter(
                gas_data_class_comp.loc[mask, "compressed_x"],
                gas_data_class_comp.loc[mask, "value"],
                c=class_colors[class_id],
                label=f"Classe {class_labels[class_id]} (Real)",
                s=25,
                alpha=0.6,
                edgecolors="black",
                linewidths=0.3,
                zorder=3,
            )

        # Plotar predições (teste) com marcadores diferentes
        test_mask = gas_data_class_comp.index[split_idx:]
        test_x = gas_data_class_comp.loc[test_mask, "compressed_x"]
        test_y = gas_data_class_comp.loc[test_mask, "value"]

        for class_id in range(3):
            mask = y_pred_test == class_id
            if mask.sum() > 0:
                ax1.scatter(
                    test_x[mask],
                    test_y[mask],
                    c=class_colors[class_id],
                    marker="X",
                    s=80,
                    alpha=0.8,
                    edgecolors="black",
                    linewidths=1,
                    label=f"Predição: {class_labels[class_id]}",
                    zorder=4,
                )

        # Adicionar linhas horizontais para limites das classes
        ax1.axhline(
            y=q1,
            color="gray",
            linestyle="--",
            linewidth=1.5,
            alpha=0.5,
            label=f"Limite Baixa/Média ({q1:.1f})",
            zorder=1,
        )
        ax1.axhline(
            y=q2,
            color="gray",
            linestyle="--",
            linewidth=1.5,
            alpha=0.5,
            label=f"Limite Média/Alta ({q2:.1f})",
            zorder=1,
        )

        # Marcar linha de divisão treino/teste
        split_x = gas_data_class_comp.iloc[split_idx]["compressed_x"]
        ax1.axvline(
            x=split_x,
            color="orange",
            linestyle="-",
            linewidth=2,
            alpha=0.5,
            label="Divisão Treino/Teste",
            zorder=2,
        )

        # Adicionar linhas verticais para gaps
        for gap_x in gaps_class_gas:
            ax1.axvline(
                x=gap_x, color="gray", linestyle=":", alpha=0.3, linewidth=1, zorder=0
            )

        # Ajustar ticks do eixo X
        apply_date_ticks(
            ax1,
            gas_data_class_comp["compressed_x"],
            gas_data_class_comp["timestamp"],
            num_ticks=10,
        )

        ax1.set_xlabel("Tempo", fontweight="bold")
        ax1.set_ylabel("Concentração de Gás", fontweight="bold")
        ax1.set_title(
            "Análise de Classificação: Série Temporal de Gás (Random Forest)",
            fontweight="bold",
            pad=15,
        )
        ax1.grid(True, alpha=0.3, linestyle="--", zorder=0)
        ax1.legend(loc="upper left", framealpha=0.95, fontsize=8, ncol=2)

        # Adicionar caixa de texto com métricas
        metrics_text = f"Métricas de Performance:\n"
        metrics_text += f"Acurácia (Treino): {accuracy_train:.3f}\n"
        metrics_text += f"Acurácia (Teste): {accuracy_test:.3f}\n"
        metrics_text += f"\nLimites das Classes:\n"
        metrics_text += f"Baixa: < {q1:.1f}\n"
        metrics_text += f"Média: {q1:.1f} - {q2:.1f}\n"
        metrics_text += f"Alta: ≥ {q2:.1f}"

        # Caixa de texto com zorder alto para ficar acima dos pontos
        ax1.text(
            0.98,
            0.98,
            metrics_text,
            transform=ax1.transAxes,
            fontsize=9,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(
                boxstyle="round",
                facecolor="lightgreen",
                alpha=0.95,
                edgecolor="black",
                linewidth=1,
            ),
            family="monospace",
            zorder=10,
        )

        plt.tight_layout()
        plt.savefig("figures/gas/classificacao_gas.pdf", bbox_inches="tight")
        plt.savefig("figures/gas/classificacao_gas.png", bbox_inches="tight")
        print("   ✅ Salvo: figures/gas/classificacao_gas")
        plt.close()


# ============================================================================
# GRÁFICO 10: Comparação Multi-Sensor (EIXO COMPRIMIDO)
# ============================================================================
print("\n📊 Gerando gráfico de Comparação Multi-Sensor (Eixo Comprimido)...")

# Preparação dos dados (Agrupamento por hora)
temp_agg = (
    df[(df["sensor_type"] == "temperatura") & (df["value"] >= 20) & (df["value"] <= 34)]
    .set_index("timestamp")
    .resample("1H")["value"]
    .mean()
    .reset_index()
)
umid_agg = (
    df[(df["sensor_type"] == "umidade") & (df["value"] >= 20) & (df["value"] <= 100)]
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
    plt.savefig("figures/comparacao/comparacao_multisensor.pdf")
    plt.savefig("figures/comparacao/comparacao_multisensor.png")
    print("   ✅ Salvo: figures/comparacao/comparacao_multisensor")
    plt.close()

print("\n✅ Processo finalizado. Gráficos sem espaços vazios gerados.")
