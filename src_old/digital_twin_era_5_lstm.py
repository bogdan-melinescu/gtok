"""
Digital Twin — ERA5-Land pipeline + LSTM weather forecasting
Filename: digital_twin_era5_lstm.py

This is a runnable, well-documented Python script that:
 1. Downloads ERA5-Land daily aggregated data via the CDS API for a user-provided
    bounding box and date range (temperature, precipitation, soil moisture, evap).
 2. Loads and preprocesses the NetCDF with xarray (daily resampling / cleaning).
 3. Builds train/val/test sequences and trains a Keras LSTM to forecast next N days
    of key meteorological variables (e.g., 2m temperature and total precipitation).
 4. Saves model and scalers and provides example predict/evaluate utilities.

Notes before running:
 - You must register at https://cds.climate.copernicus.eu/ and create ~/.cdsapirc
   with your personal token (see the CDS web portal instructions).
 - Install dependencies (suggested in a venv):
     pip install cdsapi xarray netCDF4 numpy pandas scikit-learn tensorflow matplotlib

This script is written to be adaptable: supply bbox coords, variables and dates.
"""

import os
import json
import cdsapi
import xarray as xr
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import matplotlib.pyplot as plt

# ------------------------- USER PARAMETERS -------------------------
# Bounding box [north, west, south, east] or single point handled below
# Example: small bbox around a farm (replace with real coords)
BBOX = {
    'north': 46.5,
    'west': 26.5,
    'south': 46.4,
    'east': 26.6,
}

# Date range
START_DATE = '2000-01-01'
END_DATE = '2023-12-31'

# Variables to request (ERA5-Land daily aggregated names)
# You can adjust variables as needed; see ERA5-Land documentation for full list.
VARIABLES = [
    '2m_temperature',              # daily mean 2m temperature (K)
    'total_precipitation',         # daily total precipitation (m)
    'potential_evaporation',       # daily potential evapotranspiration (m)
    'volumetric_soil_water_layer_1' # soil moisture top layer (m3 m-3)
]

# Local filenames
OUTPUT_DIR = 'data'
os.makedirs(OUTPUT_DIR, exist_ok=True)
ERA5_FILE = os.path.join(OUTPUT_DIR, 'era5_land_daily.nc')
MODEL_FILE = os.path.join(OUTPUT_DIR, 'lstm_weather_model.h5')
SCALER_FILE = os.path.join(OUTPUT_DIR, 'scalers.npz')

# Forecast horizon (days) and sequence length for LSTM
PRED_HORIZON = 7   # predict next 7 days
SEQ_LEN = 30       # use past 30 days to predict next 7

# ------------------------- CDS DOWNLOAD -------------------------

def download_era5_land(bbox, start_date, end_date, variables, target_file):
    """
    Download ERA5-Land daily aggregated data via CDS API.

    This function assumes you have configured ~/.cdsapirc with your token.
    It requests data for the bounding box and time range and saves a NetCDF.
    """
    c = cdsapi.Client()

    # Build area as [north, west, south, east]
    area = [bbox['north'], bbox['west'], bbox['south'], bbox['east']]

    # The dataset name: 'reanalysis-era5-land-monthly-means' vs daily aggregated
    # We'll use the ERA5-Land "daily aggregated" dataset. If this exact name
    # changes on CDS portal, update accordingly.
    print('Requesting data from CDS...')
    req = {
        'product_type': 'daily_aggregates',
        'variable': variables,
        'year': list(map(str, range(int(start_date[:4]), int(end_date[:4]) + 1))),
        'month': [f'{m:02d}' for m in range(1,13)],
        'day': [f'{d:02d}' for d in range(1,32)],
        'area': area,
        'format': 'netcdf'
    }

    # The exact dataset id used here may need to be adjusted depending on CDS naming.
    dataset_id = 'reanalysis-era5-land-daily-aggregates'

    # Submit request
    c.retrieve(dataset_id, req, target_file)
    print('Download complete:', target_file)


# ------------------------- LOAD & PREPROCESS -------------------------

def load_and_preprocess(nc_file, variables):
    """
    Load NetCDF into xarray, select variables, compute spatial mean over bbox,
    convert units where appropriate, and return a pandas DataFrame indexed by date.
    """
    ds = xr.open_dataset(nc_file)

    # Keep only requested variables (if they have different names, adjust here)
    # Spatial average over lat/lon dims if present
    df = pd.DataFrame()

    for var in variables:
        if var not in ds.variables:
            raise KeyError(f'Variable {var} not found in dataset. Available: {list(ds.data_vars)}')

        da = ds[var]

        # If variable has lat/lon dimensions, average across them
        if {'latitude', 'longitude'}.issubset(set(da.dims)) or {'lat','lon'}.issubset(set(da.dims)):
            da_mean = da.mean(dim=[d for d in ['latitude','longitude','lat','lon'] if d in da.dims])
        else:
            da_mean = da

        # Ensure time coordinate is pandas datetime
        pd_time = pd.to_datetime(da_mean.time.values)
        series = pd.Series(da_mean.values, index=pd_time)

        # Convert units if needed (e.g., temperature from K to C)
        if 'temperature' in var and series.mean() > 200:
            series = series - 273.15

        # precipitation often in meters per day → convert to mm/day
        if 'precipitation' in var:
            series = series * 1000.0

        df[var] = series

    # Drop rows with all-NaN
    df = df.dropna(how='all')

    # Optionally fill small gaps
    df = df.interpolate(limit=3)

    return df


# ------------------------- SEQUENCE MAKING -------------------------

def make_sequences(df, seq_len, pred_horizon, target_vars):
    """
    Create sliding-window sequences for LSTM.
    X shape: (samples, seq_len, features)
    y shape: (samples, pred_horizon * len(target_vars)) or (samples, pred_horizon, len(target_vars))
    """
    data = df.values
    n_samples = len(df) - seq_len - pred_horizon + 1
    X = np.zeros((n_samples, seq_len, data.shape[1]))
    y = np.zeros((n_samples, pred_horizon, len(target_vars)))

    for i in range(n_samples):
        X[i] = data[i:i+seq_len]
        y[i] = data[i+seq_len:i+seq_len+pred_horizon][:, [df.columns.get_loc(v) for v in target_vars]]

    return X, y


# ------------------------- MODEL BUILDING -------------------------

def build_lstm(input_shape, output_steps, output_vars):
    model = Sequential()
    model.add(LSTM(128, input_shape=input_shape, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(output_steps * output_vars))
    model.compile(optimizer='adam', loss='mse')
    return model


# ------------------------- TRAIN / EVALUATE -------------------------

def train_model(X, y, model_file, scalers=None):
    # y currently shape (samples, pred_horizon, n_vars) -> flatten to (samples, pred_horizon*n_vars)
    n_vars = y.shape[2]
    y_flat = y.reshape((y.shape[0], y.shape[1]*y.shape[2]))

    split1 = int(0.7 * len(X))
    split2 = int(0.85 * len(X))

    X_train, X_val, X_test = X[:split1], X[split1:split2], X[split2:]
    y_train, y_val, y_test = y_flat[:split1], y_flat[split1:split2], y_flat[split2:]

    model = build_lstm(input_shape=(X.shape[1], X.shape[2]), output_steps=y.shape[1], output_vars=n_vars)

    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ModelCheckpoint(model_file, save_best_only=True, monitor='val_loss')
    ]

    history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=200, batch_size=32, callbacks=callbacks)

    # Evaluate
    test_loss = model.evaluate(X_test, y_test)
    print('Test loss (MSE):', test_loss)

    return model, history, (X_test, y_test)


# ------------------------- SAVE/LOAD SCALERS -------------------------

def save_scalers(scalers, path):
    np.savez(path, **scalers)


def load_scalers(path):
    data = np.load(path)
    return {k: data[k] for k in data.files}


# ------------------------- MAIN WORKFLOW -------------------------

if __name__ == '__main__':
    # Step 1: Download data (uncomment to run; requires .cdsapirc)
    # download_era5_land(BBOX, START_DATE, END_DATE, VARIABLES, ERA5_FILE)

    if not os.path.exists(ERA5_FILE):
        print('ERA5 NetCDF not found. Please set up ~/.cdsapirc and uncomment download step, or place a file at', ERA5_FILE)
        exit(1)

    # Step 2: Load and preprocess
    df = load_and_preprocess(ERA5_FILE, VARIABLES)
    print('Loaded data sample:')
    print(df.head())

    # Step 3: Scaling
    feature_scaler = StandardScaler()
    scaled = feature_scaler.fit_transform(df.values)
    df_scaled = pd.DataFrame(scaled, index=df.index, columns=df.columns)

    # Save scalers (only mean/scale from StandardScaler)
    save_scalers({'mean': feature_scaler.mean_, 'scale': feature_scaler.scale_}, SCALER_FILE)

    # Step 4: Make sequences
    target_vars = ['2m_temperature', 'total_precipitation']
    X, y = make_sequences(df_scaled, SEQ_LEN, PRED_HORIZON, target_vars)
    print('X shape, y shape:', X.shape, y.shape)

    # Step 5: Train
    model, history, test_data = train_model(X, y, MODEL_FILE)

    # Step 6: Example predict using last available window
    last_window = X[-1:]
    pred_flat = model.predict(last_window)
    pred = pred_flat.reshape((PRED_HORIZON, len(target_vars)))

    # Unscale predictions for interpretability
    mean = np.load(SCALER_FILE)['mean']
    scale = np.load(SCALER_FILE)['scale']
    # We only scale target variable columns back
    target_idx = [df.columns.get_loc(v) for v in target_vars]
    preds_unscaled = pred * scale[target_idx] + mean[target_idx]

    print('\nPredicted next', PRED_HORIZON, 'days (unscaled):')
    for i, day in enumerate(preds_unscaled, 1):
        print(f'Day+{i}:', dict(zip(target_vars, day)))

    # Plot training history
    plt.figure()
    plt.plot(history.history['loss'], label='train_loss')
    plt.plot(history.history['val_loss'], label='val_loss')
    plt.legend()
    plt.title('Training loss')
    plt.show()

    print('\nAll done. Model saved to', MODEL_FILE)
