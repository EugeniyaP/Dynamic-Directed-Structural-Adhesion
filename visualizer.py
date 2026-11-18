import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def plot_core_volatility_and_churn(owner, repo, base_dir="./data/temporal_networks"):
    """
    Plot longitudinal trajectories comparing 2-ESCC Core Volatility (v_t),
    LSCC Edge Volatility, and Global Tie Churn Rate (C_E).
    Saves high-resolution PNG and vector PDF figures.
    """
    project_dir = os.path.join(base_dir, f"temporal_networks_{owner}_{repo}")
    csv_path = os.path.join(project_dir, f"core_volatility_metrics_{owner}_{repo}.csv")

    if not os.path.exists(csv_path):
        print(f"Metrics file not found: {csv_path}. Run core_volatility_analyzer.py first.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        print("Metrics CSV file is empty.")
        return

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(14, 6.8))

    # 1. 2-ESCC Core Volatility Index (v_t)
    sns.lineplot(
        data=df,
        x="Month_t",
        y="Core_Volatility",
        marker="o",
        color="#1f77b4",
        linewidth=2.5,
        markersize=6,
        label=r"2-ESCC Core Volatility ($\nu_t$)",
        ax=ax,
    )

    # 2. LSCC Edge Volatility
    if "LSCC_Edge_Volatility" in df.columns:
        sns.lineplot(
            data=df,
            x="Month_t",
            y="LSCC_Edge_Volatility",
            marker="^",
            color="#9467bd",
            linewidth=2.0,
            markersize=6,
            linestyle="-.",
            label=r"LSCC Edge Volatility",
            ax=ax,
        )

    # 3. Global Tie Churn Rate (C_E)
    sns.lineplot(
        data=df,
        x="Month_t",
        y="Global_Tie_Churn_CE",
        marker="s",
        color="#ff7f0e",
        linewidth=2.0,
        markersize=6,
        linestyle="--",
        label=r"Global Tie Churn Rate ($\mathcal{C}_E$)",
        ax=ax,
    )

    ax.set_title(
        f"Structural Redundancy vs. Relational Churn\nProject: {owner}/{repo}",
        fontsize=14,
        fontweight="bold",
        pad=45,
    )
    ax.set_xlabel("Temporal Window ($t$)", fontsize=12, labelpad=10)
    ax.set_ylabel("Metric Value", fontsize=12, labelpad=10)
    ax.set_ylim(-0.05, 1.05)

    step = max(1, len(df) // 15)
    tick_indices = list(range(0, len(df), step))
    tick_labels = [str(df["Month_t"].iloc[i]) for i in tick_indices]

    ax.set_xticks(tick_indices)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right")

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.14),
        ncol=3,
        fontsize=10.5,
        frameon=True,
        shadow=False,
    )

    plt.tight_layout()

    output_png = os.path.join(project_dir, f"core_vs_churn_plot_{owner}_{repo}.png")
    output_pdf = os.path.join(project_dir, f"core_vs_churn_plot_{owner}_{repo}.pdf")

    plt.savefig(output_png, dpi=300)
    plt.savefig(output_pdf, format="pdf")

    print("Figures saved successfully:")
    print(f"  1. PNG: {output_png}")
    print(f"  2. PDF: {output_pdf}")
    plt.close(fig)


if __name__ == "__main__":
    plot_core_volatility_and_churn("google", "zx")
