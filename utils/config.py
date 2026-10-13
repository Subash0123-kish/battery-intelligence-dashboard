from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = PROJECT_DIR / "outputs"
MODEL_DIR = PROJECT_DIR / "model_results"
REPORT_DIR = OUTPUT_DIR / "reports"
ASSET_DIR = PROJECT_DIR / "assets"
IMAGE_DIR = ASSET_DIR / "images"
HERO_IMAGE = IMAGE_DIR / "battery-thermal-hero.png"
APP_ICON = IMAGE_DIR / "battery-intelligence-icon.png"

SOURCE_DATASETS = {
    "Charge dataset": PROJECT_DIR / "charge.csv",
    "Discharge dataset": PROJECT_DIR / "discharge.csv",
    "Impedance dataset": PROJECT_DIR / "impedance.csv",
    "Metadata dataset": PROJECT_DIR / "meta.csv",
}

PROCESSED_DATASETS = {
    "SOH validated": PROCESSED_DIR / "soh_validated.csv",
    "SOH engineered features": PROCESSED_DIR / "soh_engineered_features.csv",
    "SOH discharge features": PROCESSED_DIR / "soh_discharge_features.csv",
    "SOH cycle mapping diagnostics": PROCESSED_DIR / "soh_cycle_mapping_diagnostics.csv",
    "RUL cycle features": PROCESSED_DIR / "rul_cycle_features.csv",
    "RUL cycle dataset": PROCESSED_DIR / "rul_cycle_dataset.csv",
    "Thermal prediction dataset": PROCESSED_DIR / "thermal_prediction_dataset.csv",
    "Physics thermal observations": PROCESSED_DIR / "physics_thermal_observations.csv",
}

KEY_OUTPUTS = {
    "RUL model comparison": OUTPUT_DIR / "rul_model_comparison.csv",
    "RUL evaluated predictions": OUTPUT_DIR / "rul_test_predictions_evaluated.csv",
    "Thermal common-test comparison": OUTPUT_DIR / "thermal_common_test_comparison.csv",
    "Thermal common-test predictions": OUTPUT_DIR / "thermal_common_test_predictions.csv",
    "Thermal evaluated predictions": OUTPUT_DIR / "thermal_test_predictions_evaluated.csv",
    "Thermal final rankings": OUTPUT_DIR / "final_thermal_model_rankings.csv",
    "Thermal battery metrics": OUTPUT_DIR / "final_thermal_battery_metrics.csv",
    "Physics thermal metrics": OUTPUT_DIR / "physics_thermal_model_metrics.csv",
    "Physics thermal predictions": OUTPUT_DIR / "physics_thermal_predictions.csv",
    "PINN thermal metrics": OUTPUT_DIR / "pinn_thermal_metrics.csv",
    "PINN training history": OUTPUT_DIR / "pinn_training_history.csv",
    "SOH report comparison": REPORT_DIR / "soh_model_comparison.csv",
    "SOH report predictions": REPORT_DIR / "soh_test_predictions.csv",
}

REPORT_FILES = {
    "Thermal research summary": OUTPUT_DIR / "thermal_research_summary.txt",
    "Scientific validation report": OUTPUT_DIR / "scientific_validation_report.txt",
    "Battery research report": OUTPUT_DIR / "battery_research_report.md",
}

DEFAULT_SAMPLE_ROWS = 250_000
PLOT_SAMPLE_POINTS = 5_000
LARGE_FILE_BYTES = 75 * 1024 * 1024


def relative_to_project(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_DIR))
    except ValueError:
        return str(path)

