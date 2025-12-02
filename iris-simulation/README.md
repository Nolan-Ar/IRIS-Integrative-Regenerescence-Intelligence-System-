# IRIS Economic Simulation

A scientific simulation of the **IRIS (Integrative Regenerescence Intelligence System)** thermodynamic economic model.

This simulation validates the viability of thermodynamic regulation through **Kappa (κ)** and **Eta (η)** coefficients over long-term economic cycles.

## 🎯 Objectives

1. **Prove thermodynamic stability**: Does the D/V ratio converge to 1?
2. **Analyze inequality evolution**: How does the Gini coefficient evolve?
3. **Validate κ and η efficiency**: Do these parameters effectively regulate the system?
4. **Test demographic resilience**: Does the system survive demographic shocks?

## 📋 Features

### Core Economic Components
- **Oracle**: Initialization with D₀ = V₀ (thermodynamic equilibrium)
- **Economic Agents**: 5 aptitudes-based behavior (croissance, confiance, conso, social_up, épargne)
- **Enterprises**: 1-5★ levels with casino mechanics and fundraising
- **Goods Catalog**: Fibonacci distribution (1-5★ NFT goods)
- **RAD**: Segmented debt tracking (material, services, engagement, regulator)

### Regulation System
- **Exchange Module**: Calculates κ and η from 3 system sensors
  - r (thermometric ratio D/V)
  - ν_eff (circulation velocity)
  - τ_eng (engagement rate)
- **Universal Income**: Distributed monthly, modulated by individual η
- **Chambre Mémorielle**: 4-5★ goods via staking contracts
- **Chambre de Relance**: 1-3★ goods recycling

### Demographics
- **Mortality**: Gompertz model (exponential increase after 60)
- **Natality**: Balanced for +1% population growth

### Analysis
- **Metrics Collection**: 30+ indicators per cycle
- **Visualizations**: Thermodynamics, distribution, demographics, flows, sensors
- **Statistical Tests**: ADF convergence, Gini trends, regulation efficiency

## 🚀 Installation

### Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`

### Setup

```bash
# Clone repository
cd iris-simulation

# Install dependencies
pip install -r requirements.txt
```

## 📖 Usage

### Basic Run

```bash
# From src/ directory
cd src
python main.py
```

This runs with default parameters:
- 4069 agents
- V_total = 23530
- 120 cycles (10 years)

### Custom Simulation

```bash
# Specify parameters
python main.py --agents 5000 --v_total 30000 --cycles 240

# With seed for reproducibility
python main.py --seed 42 --output ../data/runs/exp1

# From configuration file
python main.py --config ../config.yaml
```

### Command Line Options

```
--config FILE           Configuration YAML file
--agents N              Number of initial agents (default: 4069)
--v_total V             Total Verum to distribute (default: 23530)
--cycles N              Number of cycles (default: 120)
--entreprises_ratio R   Ratio of agents with enterprises (default: 0.3)
--distribution TYPE     'pareto_80_20' or 'equal' (default: pareto_80_20)
--seed N                Random seed for reproducibility
--output DIR            Output directory for results
--verbose               Enable verbose logging
--no-plots              Disable plot generation
```

## 📊 Outputs

Simulation results are saved to `data/runs/run_TIMESTAMP/`:

```
data/runs/run_20250601_143022/
├── metrics.csv                 # All metrics (30+ indicators per cycle)
├── statistical_report.txt      # Convergence analysis
├── thermodynamique.png         # D/V ratio, κ, η, V_ON
├── distribution.png            # Gini, top shares, median wealth
├── demographie.png             # Population, births, deaths, age
├── flux.png                    # RU, U_burn, V flows, staking
├── capteurs.png                # r_ic, ν_eff, τ_eng sensors
└── rad_sectors.png             # RAD debt segmentation
```

### Key Metrics

**Thermodynamic**:
- `ratio_D_V`: D/V ratio (target = 1.0)
- `kappa`: Liquidity regulator κ ∈ [0.5, 2.0]
- `eta_global`: Creation multiplier η ∈ [0.5, 2.0]
- `V_ON`: Total active Verum in circulation

**Distribution**:
- `gini`: Gini coefficient (inequality)
- `top10_share`: Wealth share of top 10%
- `median_wealth`: Median agent patrimony

**Sensors**:
- `r_ic`: Investment/consumption ratio
- `nu_eff`: Circulation velocity (target = 0.20)
- `tau_eng`: Engagement rate (target = 0.35)

**Demographics**:
- `population`: Living agents
- `entreprises`: Active enterprises
- `deaths`, `births`: Monthly demographic flows

## 🔬 Scientific Validation

### Convergence Test (ADF)

The simulation uses the **Augmented Dickey-Fuller test** to validate that the D/V ratio converges to 1.0:

```python
from analysis.statistics import analyze_convergence

df = metrics.to_dataframe()
result = analyze_convergence(df)

print(result['interpretation'])
# Expected: "CONVERGED: D/V ratio is stable around 1.0"
```

### Inequality Evolution

Tracks how the Gini coefficient evolves under thermodynamic regulation:

```python
from analysis.statistics import analyze_inequality_evolution

result = analyze_inequality_evolution(df)
print(result['trend'])  # 'decreasing' or 'increasing'
```

### Regulation Efficiency

Analyzes κ and η oscillations and correlations:

```python
from analysis.statistics import analyze_regulation_efficiency

result = analyze_regulation_efficiency(df)
print(result['kappa']['mean'])  # Should oscillate around 1.0
print(result['eta']['mean'])    # Should oscillate around 1.0
```

## 🧩 Architecture

```
iris-simulation/
├── src/
│   ├── main.py                 # CLI entry point
│   ├── simulation.py           # Main simulation engine
│   ├── core/
│   │   ├── oracle.py           # Initialization (D₀ = V₀)
│   │   ├── agent.py            # Agents & Enterprises
│   │   ├── bien.py             # Goods (NFT 1-5★)
│   │   ├── rad.py              # RAD debt tracker
│   │   ├── exchange.py         # κ & η regulation
│   │   ├── universe.py         # Universal Income
│   │   ├── chambre_memorielle.py  # 4-5★ staking
│   │   ├── chambre_relance.py     # 1-3★ recycling
│   │   └── behaviors.py        # Agent decision logic
│   └── analysis/
│       ├── metrics.py          # Metrics collection
│       ├── plots.py            # Visualizations
│       └── statistics.py       # Statistical tests
├── data/
│   ├── runs/                   # Simulation outputs
│   └── results/                # Analysis results
├── config.yaml                 # Default configuration
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

## 🔑 Key Formulas (from IRIS Protocol)

### Thermodynamic Equilibrium

$$\sum V_0 = \sum D_0$$

At initialization, total Verum equals total debt (thermodynamic neutrality).

### Regulation Laws (Layer 1)

**Eta (η) variation**:

$$\Delta \eta_t = +\alpha_\eta \times (1 - r_{t-1}) + \beta_\eta \times (\nu_{\text{target}} - \nu_{t-1}) - \gamma_\eta \times (\tau_{\text{eng}} - \tau_{\text{target}})$$

**Kappa (κ) variation**:

$$\Delta \kappa_t = +\alpha_\kappa \times (\nu_{\text{target}} - \nu_{t-1}) - \beta_\kappa \times (\tau_{\text{eng}} - \tau_{\text{target}}) + \gamma_\kappa \times (1 - r_{t-1})$$

Coefficients (from protocol):
- α_η = 0.3, β_η = 0.4, γ_η = 0.2
- α_κ = 0.4, β_κ = 0.3, γ_κ = 0.2

Constraints:
- |Δη|, |Δκ| ≤ 0.15 (max 15% change per cycle)
- η, κ ∈ [0.5, 2.0]

### Sensors

**Thermometric ratio**:
$$r_t = \frac{D_t}{V_t^{\text{on}}}$$

**Circulation velocity**:
$$\nu_{\text{eff}} = \frac{U^{\text{burn}} + S^{\text{burn}}}{V_{t-1}^{\text{on}}}$$

**Engagement rate**:
$$\tau_{\text{eng}} = \frac{U_t^{\text{staké}}}{U_t}$$

## 📝 Configuration

Edit `config.yaml` to customize simulation parameters:

```yaml
simulation:
  agents: 4069
  v_total: 23530
  cycles: 120
  entreprises_ratio: 0.3
  distribution: 'pareto_80_20'
  seed: 42

regulation:
  nu_target: 0.20
  tau_target: 0.35
  alpha_eta: 0.3
  beta_eta: 0.4
  # ... (see config.yaml for all options)
```

## 🧪 Example Workflow

```bash
# 1. Run simulation with seed
cd src
python main.py --seed 42 --cycles 240 --output ../data/runs/experiment_1

# 2. Check results
ls ../data/runs/experiment_1/
# metrics.csv, *.png, statistical_report.txt

# 3. View statistical report
cat ../data/runs/experiment_1/statistical_report.txt

# 4. (Optional) Load in Jupyter for custom analysis
jupyter notebook
```

```python
# In Jupyter
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data/runs/experiment_1/metrics.csv')

# Plot D/V convergence
plt.plot(df['cycle'], df['ratio_D_V'])
plt.axhline(y=1.0, linestyle='--', color='red')
plt.title('Thermodynamic Convergence')
plt.show()
```

## 📚 References

- **IRIS Protocol**: See `Iris_proto_complet.md` for complete theoretical foundation
- **Thermodynamic Economics**: Conservation principles applied to economic systems
- **Holochain**: Distributed hash table for decentralized implementation

## 🤝 Contributing

This simulation is for academic thesis validation. For questions or suggestions:

1. Review the IRIS protocol document
2. Check existing issues
3. Submit detailed bug reports or enhancement proposals

## 📄 License

Academic research project. Please cite if using for publications.

## ✨ Acknowledgments

Developed as part of a PhD thesis on thermodynamic economic systems.

Special thanks to the IRIS protocol research team.

---

**For detailed implementation notes, see code comments in each module.**

**For theoretical foundation, refer to `Iris_proto_complet.md`.**
