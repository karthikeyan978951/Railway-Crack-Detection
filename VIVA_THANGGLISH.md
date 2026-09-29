# Viva quick explanation

**Problem:** Railway track condition changes over time due to vibration, acceleration, deformation, temperature, stress and environmental conditions. Periodic inspection can miss changes between inspections.

**Solution:** Historical sequential sensor readings are converted into sequences of 12 time steps and passed to an LSTM. The LSTM learns temporal patterns and outputs a failure-risk probability.

**Why LSTM?** Railway sensor measurements are time-series data. LSTM is designed to learn useful information across previous time steps.

**Output:** Probability + LOW/MEDIUM/HIGH/CRITICAL risk + track health score.

**API:** Flask exposes section, weather, alert and simulation endpoints. Open-Meteo supplies current weather data for the section coordinates.

**Dataset:** Synthetic demonstration data. It is not real railway sensor data.

**Safety:** The system is an AI-assisted early-warning prototype, not a certified railway safety system.
