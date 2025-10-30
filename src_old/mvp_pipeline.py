import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path

# ------------------------
# CONFIG
# ------------------------
CROP = "wheat"
LAT = 46.77  # Cluj-Napoca
GDD_BASE = 5.0
GDD_THRESHOLDS = [150, 300, 600, 1000, 1500, 2000]  # simplificate pentru grâu

# ------------------------
# FUNCTIONS
# ------------------------

def compute_et0_hargreaves(tmin, tmax, rad, lat=LAT):
    """Hargreaves reference ET0 [mm/day]"""
    tmean = (tmin + tmax) / 2
    et0 = 0.0023 * (tmean + 17.8) * np.sqrt(tmax - tmin) * rad
    return et0

def compute_gdd(tmin, tmax, base=GDD_BASE):
    """Growing Degree Days"""
    tmean = (tmin + tmax) / 2
    return max(0, tmean - base)

def estimate_swi(prev_swi, precip, et0, capacity=150):
    """Simple bucket model for Soil Water Index"""
    swi = prev_swi + precip - et0
    swi = max(0, min(capacity, swi))
    return swi

def estimate_bbch(gdd_cum, thresholds=GDD_THRESHOLDS):
    """Approximate BBCH stage from cumulative GDD"""
    stage = np.searchsorted(thresholds, gdd_cum) + 1
    return stage

# ------------------------
# MAIN PIPELINE
# ------------------------

def run_pipeline(input_csv, output_dir="pipeline_output"):
    Path(output_dir).mkdir(exist_ok=True)

    # Load input data
    df = pd.read_csv(input_csv, parse_dates=["date"])

    # Initialize SWI
    swi_values, gdd_cum_values, bbch_values = [], [], []
    swi, gdd_cum = 100, 0

    for _, row in df.iterrows():
        et0 = compute_et0_hargreaves(row["tmin_c"], row["tmax_c"], row["solar_rad_MJ_m2"])
        gdd = compute_gdd(row["tmin_c"], row["tmax_c"])
        gdd_cum += gdd
        swi = estimate_swi(swi, row["precip_mm"], et0)
        bbch = estimate_bbch(gdd_cum)

        swi_values.append(swi)
        gdd_cum_values.append(gdd_cum)
        bbch_values.append(bbch)

    # Save features
    df["et0_mm"] = df.apply(lambda r: compute_et0_hargreaves(r["tmin_c"], r["tmax_c"], r["solar_rad_MJ_m2"]), axis=1)
    df["gdd"] = df.apply(lambda r: compute_gdd(r["tmin_c"], r["tmax_c"]), axis=1)
    df["gdd_cum"] = gdd_cum_values
    df["swi_proxy"] = swi_values
    df["bbch_stage"] = bbch_values

    feature_csv = Path(output_dir) / "features.csv"
    df.to_csv(feature_csv, index=False)

    # Plot GDD cumulative
    plt.figure(figsize=(10, 5))
    plt.plot(df["date"], df["gdd_cum"], label="Cumulative GDD")
    plt.xlabel("Date")
    plt.ylabel("Cumulative GDD")
    plt.title(f"{CROP.capitalize()} - Cumulative GDD")
    plt.legend()
    plt.savefig(Path(output_dir) / "plot_gdd.png")
    plt.close()

    # Plot SWI
    plt.figure(figsize=(10, 5))
    plt.plot(df["date"], df["swi_proxy"], label="SWI proxy", color="green")
    plt.xlabel("Date")
    plt.ylabel("SWI (mm)")
    plt.title(f"{CROP.capitalize()} - Soil Water Index Proxy")
    plt.legend()
    plt.savefig(Path(output_dir) / "plot_swi.png")
    plt.close()

    # Save farm descriptor
    farm_desc = {
        "farm_name": "Cluj Test Farm",
        "location": {"lat": LAT, "lon": 23.6},
        "crop": CROP,
        "area_ha": 4,
        "features_file": str(feature_csv)
    }
    with open(Path(output_dir) / "farm_descriptor.json", "w") as f:
        json.dump(farm_desc, f, indent=2)

    print(f"✅ Pipeline finished. Files saved in {output_dir}")

# ------------------------
# ENTRY POINT
# ------------------------
if __name__ == "__main__":
    # Expect input CSV with: date, tmin_c, tmax_c, precip_mm, solar_rad_MJ_m2
    run_pipeline("sample_weather.csv")
