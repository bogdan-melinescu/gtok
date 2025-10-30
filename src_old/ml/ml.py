import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

# Load your dataset
df = pd.read_csv("/Users/bogdanmel/Development/gtok/local_data/simulated_farm_data.csv")

# Check if the CSV was read correctly
print(df.head())
print(f"Shape of the DataFrame: {df.shape}")
print(f"Columns in the DataFrame: {df.columns}")
print(df.isnull().sum())
print(df.describe())

# Define input features and targets
features = ["temperature", "humidity", "rainfall", "solar_radiation", "soil_ph"]
targets = ["ndvi", "swi"]

# Prepare inputs and outputs
X = df[features].values
y = df[targets].values

# Scale inputs and outputs
scaler_X = MinMaxScaler()
X_scaled = scaler_X.fit_transform(X)

scaler_y = MinMaxScaler()
y_scaled = scaler_y.fit_transform(y)

# Reshape input for LSTM: (samples, timesteps, features)
X_scaled = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_scaled, test_size=0.2, random_state=42)

# Build the LSTM model
model = Sequential([
    LSTM(64, input_shape=(1, X_scaled.shape[2])),
    Dense(32, activation='relu'),
    Dense(2)  # Predict NDVI and SWI
])

model.compile(optimizer='adam', loss='mse')

# Train the model
model.fit(X_train, y_train, epochs=50, batch_size=8, validation_split=0.1)

# Predict
predictions = model.predict(X_test)
predicted_ndvi_swi = scaler_y.inverse_transform(predictions)

# View first few predictions
print(predicted_ndvi_swi[:5])

# Save the trained model
model.save("ndvi_swi_predictor.h5")
