from pathlib import Path

import numpy as np
import pandas as pd


def generate_logs(num_rows: int = 5000, random_seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)
    timestamps = pd.date_range(start="2026-01-01", periods=num_rows, freq="5min")

    cpu_usage = np.clip(rng.normal(loc=62, scale=20, size=num_rows), 5, 100)
    ram_usage = np.clip(rng.normal(loc=68, scale=18, size=num_rows), 10, 100)
    temp_celsius = np.clip(rng.normal(loc=62, scale=16, size=num_rows), 20, 105)
    network_latency = np.clip(rng.normal(loc=120, scale=55, size=num_rows), 5, 350)

    failure = (
        ((cpu_usage > 85) & (temp_celsius > 80))
        | ((ram_usage > 90) & (network_latency > 200))
    ).astype(int)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "cpu_usage": np.round(cpu_usage, 2),
            "ram_usage": np.round(ram_usage, 2),
            "temp_celsius": np.round(temp_celsius, 2),
            "network_latency": np.round(network_latency, 2),
            "failure": failure,
        }
    )


def main() -> None:
    data_dir = Path(__file__).resolve().parent
    output_path = data_dir / "system_logs.csv"
    logs_df = generate_logs(num_rows=5000)
    logs_df.to_csv(output_path, index=False)
    print(f"Dataset saved to: {output_path}")
    print(f"Rows: {len(logs_df)}")


if __name__ == "__main__":
    main()
