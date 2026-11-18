# The Dynamics of Asymmetry: Temporal Evolution of 2-Edge-Strongly-Connected Cores in Knowledge Exchange Networks

Python implementation for longitudinal **2-Edge-Strongly-Connected Component (2-ESCC)** extraction, set-theoretic core transition operators (\(\mathcal{R}_{t \to t+1}, \mathcal{C}_{t \to t+1}, \mathcal{X}_{t \to t+1}\)), and the **Core Volatility Index (\(\nu_t\))** in time-varying directed networks.

## Overview

Traditional connectivity metrics (such as the Largest Strongly Connected Component, LSCC) often mask structural fragility in asymmetric exchange networks. This repository operationalizes a dynamic **topological sieve** that isolates the resilient core (\(\Omega_t = \text{L2-ESCC}(G_t)\)), where every directed channel is reinforced by at least two edge-disjoint directed paths (\(\lambda_{G_t}(u, v) \ge 2\)).

### Key Features
- **Exact L2-ESCC Extraction (`find_2_escc`):** Iterative strong-bridge decomposition on induced subgraphs inside the LSCC.
- **Core Transition Operators:** Tracks Core Retention (\(\mathcal{R}\)), Contraction (\(\mathcal{C}\)), Expansion (\(\mathcal{X}\)), and **Topological Displacement** events.
- **Core Volatility Index (\(\nu_t\)):** Measures structural reconfiguration of the resilient backbone independently of peripheral tie churn (\(\mathcal{C}_E\)).
- **GitHub Longitudinal Pipeline:** Reproducible data collection and monthly snapshot builder across 28 open-source knowledge exchange ecosystems.

## Repository Structure

```text
├── core_volatility_analyzer.py   # L2-ESCC extraction, transition operators, and v_t / C_E metrics
├── data_collector.py             # GitHub REST API thread collector and monthly digraph builder
├── visualizer.py                 # Publication-ready longitudinal trajectory plots (PNG & PDF)
├── demo_example.py               # Minimal standalone demo illustrating Topological Displacement
├── requirements.txt              # Python package dependencies
└── README.md
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the minimal standalone demo (no external data required):**
   ```bash
   python demo_example.py
   ```

3. **Run the full pipeline on a GitHub repository:**
   ```bash
   export GITHUB_TOKEN="your_personal_access_token"
   python data_collector.py
   python core_volatility_analyzer.py
   python visualizer.py
   ```

## Studied Empirical Corpus (28 Repositories)
The empirical validation covers longitudinal issue and pull-request interaction networks across three architectural archetypes:
- **Core Utility Libraries & Tools:** `google/zx`, `svg/svgo`, `sherlock-project/sherlock`, `httpie/cli`, `android/architecture-samples`, `bigskysoftware/htmx`, `carbon-language/carbon-lang`, `CorentinJ/Real-Time-Voice-Cloning`, `ryanoasis/nerd-fonts`, `TheAlgorithms/JavaScript`
- **Development Frameworks & Runtime Utilities:** `avajs/ava`, `FlowiseAI/Flowise`, `h5bp/html5-boilerplate`, `hapijs/joi`, `javascript-tutorial/en.javascript.info`, `localForage/localForage`, `ludwig-ai/ludwig`, `markedjs/marked`, `meilisearch/meilisearch`, `necolas/normalize.css`, `novnc/noVNC`, `QuivrHQ/quivr`, `square/retrofit`, `x64dbg/x64dbg`, `xyflow/xyflow`
- **Ecosystem & Application Platforms:** `gorhill/uBlock`, `termux/termux-app`, `wix/Detox`

## Citation

If you use this code in your research, please cite:

```bibtex
@article{perekhodko2026dynamics,
  title={The Dynamics of Asymmetry: Temporal Evolution of 2-Edge-Strongly-Connected Cores in Knowledge Exchange Networks},
  author={Perekhodko, Eugenia},
  year={2026}
}
```
