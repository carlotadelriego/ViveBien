import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def simulate_biometrics(base_steps=8000, base_sleep=7.0, base_hr=70):
    """Simula valores de pasos, sueño y frecuencia cardiaca para un día."""
    steps = max(0, int(np.random.normal(base_steps, base_steps*0.2)))
    sleep_hours = max(3.0, float(np.random.normal(base_sleep, 1.0)))
    heart_rate = int(np.random.normal(base_hr, 5))
    return {"steps": steps, "sleep_hours": round(sleep_hours,1), "heart_rate": heart_rate}

def generate_history(days=14, base_steps=8000, base_sleep=7.0, base_hr=70):
    """Genera un DataFrame con historia simulada."""
    dates = [datetime.now().date() - timedelta(days=(days-1 - i)) for i in range(days)]
    data = [simulate_biometrics(base_steps=base_steps, base_sleep=base_sleep, base_hr=base_hr) for _ in range(days)]
    df = pd.DataFrame(data, index=pd.to_datetime(dates))
    df.index.name = "date"
    return df
