# Project Helios

Project Helios is a research-focused algorithmic trading system for equity selection and execution. It combines market-data collection, feature engineering, reinforcement learning, portfolio optimization, and reporting into a single workflow for strategy research and experimentation.

## Overview

Helios follows a typical research pipeline:

1. Filter a large ticker universe.
2. Collect market data and fundamentals.
3. Generate technical feature vectors.
4. Train or tune a Ray RLlib PPO policy.
5. Evaluate the strategy on benchmark or deployment-like scenarios.
6. Use the resulting trade logic for entries, exits, and risk management.
7. Simulate trading or connect to IBKR for live execution.

The code is organized as a modular research stack rather than a single script, which keeps experiments flexible and easy to iterate on.

## Core Features

- Multi-step data pipeline for equities market data and fundamentals
- Ticker universe filtering using market cap, country/industry exclusions, and custom banned lists
- Technical feature extraction with a large custom indicator library
- PCA-based dimensionality reduction for feature optimization
- PPO-based reinforcement-learning strategy via Ray RLlib
- Hyperparameter tuning via Ray Tune
- Training, evaluation, and inference workflows for strategy performance
- Simulated trading and live order execution hooks
- Portfolio optimization and trade management utilities
- Report generation and ledger logging
- Backtesting utilities using Backtrader and classical technical strategies

## Repository Structure

```text
project_helios/
├── README.md
├── LICENSE.md
├── requirements.txt
├── setup_instructions.txt
├── config.py
├── config_baseline.py
├── config_banned.py
├── config_enums.py
├── trade_v2.py
├── train.py
├── tune.py
├── evaluate.py
├── notes.txt
│
├── accounts/
│   └── w1_if_getAccountInformation.py
│
├── backtests/
│   ├── w1_backtest.py
│   ├── w1_generateMultiSecurityBacktest.py
│   ├── w2_KalmanMovingAverage.py
│   ├── w2_Strategy_EMA_BB.py
│   ├── w2_Strategy_EMA_KMA_MACD.py
│   ├── w2_Strategy_EMA_KMA_MACD_Pivots.py
│   ├── w2_Strategy_EMA_KMA_MACD_RSI.py
│   ├── w2_Strategy_EMA_RSI.py
│   ├── w2_Strategy_MACD_BB.py
│   └── w2_Strategy_SMA.py
│
├── data/
│   ├── w1_if_getHistoricalData.py
│   ├── w1_if_getLiveData.py
│   ├── w1_if_getMarketScannerData.py
│   ├── w1_if_getFundamentals.py
│   ├── w1_if_getTickers.py
│   ├── w1_if_getHistoricalData.py
│   ├── w1_augmentHistoricalData.py
│   ├── w1_refineTickers_PEUndervalued.py
│   ├── w1_refineTickers_PriceThreshold.py
│   ├── w1_refineTickers_FavourableBuyCondition.py
│   ├── w2_filterTickerSelection.py
│   └── scans/
│
├── features/
│   └── w1_if_deriveFeatures.py
│
├── strategies/
│   ├── w1_RLEnvironment.py
│   ├── w1_RLStrategy.py
│   ├── w1_generateTradeSignal.py
│   ├── w2_appendATRIndicator.py
│   ├── w2_appendBBIndicator.py
│   ├── w2_appendEWMATracker.py
│   ├── w2_appendKFTracker.py
│   ├── w2_appendMACDIndicator.py
│   ├── w2_appendRSIIndicator.py
│   ├── w2_appendSMATracker.py
│   ├── w2_appendZScoreIndicator.py
│   ├── w2_implementPPOConfig.py
│   └── memories/
│
├── orders/
│   └── w1_if_placeOrder.py
│
├── reports/
│   └── w1_generateAnalysisReport.py
│
├── utils/
│   ├── w2_calculatePositionSize.py
│   ├── w2_clearPreviousSessionData.py
│   ├── w2_generateDateStringYYYYMMDD.py
│   ├── w2_log.py
│   ├── w2_manageTrade.py
│   ├── w2_optimizePortfolio.py
│   ├── w2_performDataFrameOps.py
│   ├── w2_performDictionaryOps.py
│   ├── w2_performHDF5Ops.py
│   ├── w2_performNumPyOps.py
│   ├── w2_refreshTransactionMemories.py
│   ├── w2_simulateBrownianMotion.py
│   ├── w2_updateLedgerEntries.py
│   └── other helper modules
│
├── ledgers/
│   └── ledger_entries_simulated.csv
│
├── logs/
│   └── runtime logs generated during execution
│
├── models/
│   └── model artifacts and checkpoints
│
├── packages/
│   └── tti_snapshot/
│       ├── indicators/
│       └── utils/
│
├── data/
│   └── generated data files and scan outputs
│
├── reports/
│   └── generated plots and analysis outputs
└── .git/
```

## Configuration and Environment

The project relies on `config.py` for runtime settings such as:

- local project paths
- RL training parameters
- reward configuration
- portfolio and market settings
- IBKR timing and client IDs
- trade sizing and balancing
- banned tickers and filters

Related config modules:

- `config_banned.py` — banned tickers, countries, and industries
- `config_baseline.py` — baseline/reference settings
- `config_enums.py` — trading actions and operational modes

`config.py` contains hard-coded local paths. Before running the workflow in a new environment, update `ROOT_PATH`, `MODEL_SAVE_PATH`, and `TEMP_DIR` to match the local machine and intended data/model/temp directories.

## Data Flow

Helios follows a research pipeline from ticker selection through execution and evaluation.

### 1. Market universe and filtering

The code acquires ticker lists and filters them to a smaller, investable pool using logic in:

- `data/w1_if_getTickers.py`
- `data/w2_filterTickerSelection.py`
- `config_banned.py`
- `data/w1_refineTickers_*.py`

This step removes penny stocks, bad market caps, restricted countries/industries, and predefined banned symbols.

### 2. Feature engineering

Feature generation is implemented in `features/w1_if_deriveFeatures.py`. It computes a large set of indicators using the custom `packages/tti_snapshot` library, including momentum, volatility, trend, volume, and oscillator signals.

The system supports:

- standardization/robust scaling
- PCA dimensionality reduction
- support data retention for price and volume reference values
- per-ticker feature dictionaries used in the RL environment

### 3. Reinforcement learning

The RL layer is built around a custom `gymnasium` environment in `strategies/w1_RLEnvironment.py` and a strategy manager in `strategies/w1_RLStrategy.py`.

Key aspects:

- sampled portfolio of tickers at each episode
- feature vectors as observations
- discrete action space for buy/hold/sell decisions
- reward functions tied to returns, action quality, and drawdown penalties
- PPO configuration and Ray Tune optimization

The repository uses Ray RLlib and supports training, evaluation, and tuning workflows.

### 4. Execution and portfolio logic

The trade loop in `trade_v2.py` is the main operational orchestration. It can run in simulated or live mode and cycles through phases such as:

- account and portfolio retrieval
- passive pool determination
- acquisition/disposal preference logic
- market orders and limit-order handling
- ledger updates and session cleanup

The system writes ledger entries and logs while managing the active trading state.

## Training, Evaluation, and Tuning

### Train

```bash
python train.py
```

This runs the RL strategy in training mode with a sampled set of tickers and the configured simulation/training parameters.

### Evaluate

```bash
python evaluate.py
```

This evaluates the trained or configured policy against a selected ticker set and records run results and plots.

### Tune

```bash
python tune.py
```

This launches a hyperparameter search with Ray Tune using the configured search space in `config.py`.

### Main live or simulated trade loop

```bash
python trade_v2.py
```

This starts the higher-level execution lifecycle and manages continuous strategy operation.

## Backtesting and Strategy Comparison

The repository includes classical technical backtesting utilities in `backtests/` using Backtrader. Examples include:

- EMA + KMA + MACD + RSI
- MACD + Bollinger Bands
- SMA
- EMA/RSI strategies

The backtest script in `backtests/w1_backtest.py` downloads historical data for a symbol, loads a technical strategy, and produces a chart and profitability summary.

## IBKR and Live Trading

The system includes IBKR-oriented modules such as:

- `accounts/w1_if_getAccountInformation.py`
- `orders/w1_if_placeOrder.py`
- `data/w1_if_getLiveData.py`
- `data/w1_if_getHistoricalData.py`

The project references Interactive Brokers and includes timing constants, order quantity limits, and trade execution configuration in `config.py`.

This means the repository can be used for:

- paper/simulated trading
- strategy experiments in a sandbox environment
- live trading deployments after additional validation, permissioning, and risk controls

## Reporting and Logs

The project logs detailed execution state and produces generated outputs in:

- `logs/` for runtime logs
- `reports/` for analysis outputs and plots
- `ledgers/` for transaction/portfolio ledger entries
- `models/` for model checkpoint artifacts

This supports debugging and interpretation of strategy performance across sessions.

## Dependencies

This project was developed and tested with Python 3.10.

The Python dependencies are listed in `requirements.txt` and include, among others:

- Ray / RLlib
- Gymnasium
- PyTorch
- NumPy / pandas / scipy
- scikit-learn
- Plotly / Matplotlib / seaborn
- h5py
- backtrader
- riskfolio-lib
- ta-lib
- statsmodels
- IBKR client tooling (via local installation workflow)

Create and activate a Python environment, then install the requirements:

```bash
pip install -r requirements.txt
# or
uv pip install -r requirements.txt
```

Follow the remaining setup notes in `requirements.txt` for additional system packages and components not handled by the install command.

The project also references additional package installation steps in `setup_instructions.txt`, including:

- GCC and CUDA/cuDNN setup notes
- GPU environment configuration
- PyTorch CUDA build instructions
- IBAPI installation guidance
- TWS / IBKR installation walkthrough

## Important Notes

- The project expects a local environment and directory layout compatible with `config.py`.
- Some modules are Linux-specific and may require the proper system packages and toolchain.
- This is a research project, not a turnkey application.
- Live execution should only be considered after careful validation and risk controls.

## License

This project is licensed under the GNU LGPLv3. See `LICENSE.md` for the full text.

## Recommended Workflow

1. Create and activate a Python environment.
2. Install packages with `pip` or `uv` using `requirements.txt`, and follow its remaining setup instructions.
3. Update configuration paths in `config.py`.
4. Run the data and scan pipeline to assemble candidate tickers.
5. Train or tune the RL policy.
6. Evaluate the system on a smaller sampled universe.
7. Run the trade loop in simulation mode.
8. Only then consider enabling live execution hooks with appropriate controls.

## Practical Summary

Project Helios is a modular, research-first equities trading platform that combines:

- data collection and screening
- technical and factor feature engineering
- PPO-driven portfolio RL
- classical backtesting
- risk and portfolio logic
- IBKR execution interfaces

It is intended for research and simulation-first workflow development of automated equity trading strategies.

