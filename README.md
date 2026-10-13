# Battery Intelligence

Physics-Informed Battery Health & Thermal Management dashboard for the NASA Lithium-Ion Battery Aging Dataset.

This project is an interactive Streamlit research dashboard. It explores source battery data, processed SOH/RUL/thermal datasets, saved prediction outputs, model metrics, physics-informed experiments, and available research reports. The dashboard reads existing files and does not train models automatically when launched.

## Quick Start

Open PowerShell and run:

```powershell
cd "E:\NASA Dataset"
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

If port `8501` is already busy, run on another port:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

## Important Paths

Project directory:

```powershell
E:\NASA Dataset
```

Python virtual environment:

```powershell
E:\battery-pinn-env
```

Recommended Python interpreter:

```powershell
E:\battery-pinn-env\Scripts\python.exe
```

Use the explicit interpreter above when running commands. A plain `streamlit` command may point to a different global Python installation.

## Project Structure

- `app.py` - Streamlit overview dashboard and landing page.
- `pages/` - Streamlit multipage screens.
- `utils/` - shared configuration, cached loading, metrics, plotting, validation, and UI helpers.
- `.streamlit/config.toml` - dashboard theme configuration.
- `assets/images/` - local dashboard images.
- `charge.csv`, `discharge.csv`, `impedance.csv`, `meta.csv` - source datasets.
- `data/processed/` - processed SOH, RUL, thermal, and physics observation datasets.
- `outputs/` - saved predictions, metrics, reports, and experimental artifacts.
- `outputs/reports/` - SOH report artifacts.
- `model_results/` - saved model files and SOH model metrics.
- `requirements.txt` - Python dependencies used by the dashboard.

Do not move the dataset files or the virtual environment. The app resolves project files relative to `app.py`.

## Setup on This Machine

1. Open PowerShell.

2. Go to the project:

```powershell
cd "E:\NASA Dataset"
```

3. Check that the expected Python is available:

```powershell
E:\battery-pinn-env\Scripts\python.exe --version
```

4. Check Streamlit:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit version
```

5. Install or refresh dependencies only if needed:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m pip install -r requirements.txt
```

6. Launch the dashboard:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py
```

## Optional: Activate the Environment

You can activate the environment first:

```powershell
& "E:\battery-pinn-env\Scripts\Activate.ps1"
cd "E:\NASA Dataset"
python -m streamlit run app.py
```

If PowerShell blocks activation scripts, use the explicit interpreter command instead:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py
```

## Optional: Install Streamlit Agent Skills

This is only for AI coding assistants. It is not required to run the dashboard.

```powershell
cd "E:\NASA Dataset"
E:\battery-pinn-env\Scripts\python.exe -m streamlit skills --yes
```

The installed skill symlinks are environment-specific and should not be committed:

```gitignore
.agents/skills/developing-with-streamlit
.claude/skills/developing-with-streamlit
```

## Useful Development Commands

Run the app:

```powershell
cd "E:\NASA Dataset"
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py
```

Run on a specific port:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

Run headless:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py --server.headless true
```

Compile-check the application:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m compileall app.py pages utils
```

Check installed package versions:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m pip list
```

Check Streamlit configuration:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit config show
```

Clear Streamlit cache:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit cache clear
```

Check whether ports `8501` or `8502` are occupied:

```powershell
netstat -ano | findstr ":850"
```

Stop a process by PID:

```powershell
Stop-Process -Id <PID> -Force
```

## Dashboard Pages

- Overview: project landing page, dataset availability, KPI cards, saved metrics, quick navigation, and limitations.
- Dataset explorer: schema inspection, quality summaries, filters, charts, and CSV export.
- Battery health (SOH): validated SOH records, capacity plots, saved SOH model predictions, and warnings.
- Remaining useful life (RUL): cycle-level targets, saved predictions, residuals, and per-battery summaries.
- Thermal analysis: measured discharge behavior, thermal prediction datasets, next-temperature predictions, and residuals.
- Model evaluation: saved model metrics, actual-vs-predicted plots, largest errors, and battery-level results.
- Physics-informed model: empirical physics metrics, PINN metrics, training history, prediction plots, assumptions, and limitations.
- Research report: existing report files, downloadable documentation, and scientific limitations.

## Workflow for a New User

1. Confirm the source files exist:

```text
charge.csv
discharge.csv
impedance.csv
meta.csv
```

2. Confirm processed data and outputs exist:

```text
data/processed/
outputs/
model_results/
```

3. Launch the app from the project root:

```powershell
cd "E:\NASA Dataset"
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py
```

4. Start with the Overview page to confirm dataset availability and saved result files.

5. Use Dataset explorer to inspect schemas before making assumptions about columns.

6. Use SOH, RUL, Thermal analysis, Model evaluation, and Physics-informed model pages to review saved research artifacts.

7. Use download buttons inside the dashboard to export filtered records or result tables.

8. Do not overwrite source CSV files or saved research outputs unless you are deliberately regenerating results outside the dashboard workflow.

## Development Guidelines

- Keep source datasets in the project root.
- Keep the virtual environment outside the project at `E:\battery-pinn-env`.
- Use `pathlib` and paths relative to `PROJECT_DIR`.
- Use `st.cache_data` for expensive CSV loading.
- Prefer Streamlit native widgets and layouts over custom HTML/CSS.
- Use `.streamlit/config.toml` for theme settings.
- Do not use deprecated `use_container_width`; use `width="stretch"` or `width="content"`.
- Add `alt=` text for images and charts where supported.
- Do not train models when the dashboard starts.
- Do not fabricate missing metrics, predictions, or research conclusions.
- Keep scientific warnings visible when presenting SOH, RUL, thermal, and PINN results.

## Adding or Updating Data

If new processed data or output files are generated, place them in the existing folders:

```text
data/processed/
outputs/
outputs/reports/
model_results/
```

Then update the file maps in:

```text
utils/config.py
```

Restart Streamlit after changing code:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py
```

## Troubleshooting

If `streamlit` is not recognized or uses the wrong version, run Streamlit through the venv:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py
```

If `streamlit skills` says `No such command`, use the venv Streamlit:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit skills --yes
```

If port `8501` is busy:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

If the app seems stale, refresh the browser or clear Streamlit cache:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m streamlit cache clear
```

If a page is slow, remember that some source and processed CSV files are large. The app samples large datasets for interactive plotting while preserving saved outputs for downloads where available.

## Dependencies

The dashboard uses:

- Streamlit
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- PyTorch, only for compatibility with existing artifacts if needed

Install dependencies with:

```powershell
E:\battery-pinn-env\Scripts\python.exe -m pip install -r requirements.txt
```

## Scientific Limitations

- SOH reference capacity and chronological cycle mapping require verification.
- Numeric `cycle_id` is not automatically assumed to equal `cycle_number`.
- The provenance and meaning of `cycles_left` must be verified before making RUL claims.
- Thermal prediction currently targets the next recorded observation, not a fixed future horizon.
- Train/test battery separation must be verified in the original training workflow.
- Early thermal parameters were not experimentally calibrated.
- The PINN is an experimental prototype, not a validated electrothermal model.
- Predictive accuracy does not establish battery safety, safety certification, or deployment readiness.

## Main Launch Command

Use this command for normal use:

```powershell
cd "E:\NASA Dataset"
E:\battery-pinn-env\Scripts\python.exe -m streamlit run app.py
```
