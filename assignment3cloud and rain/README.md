# Data Rain — CSV-driven raindrop visualization

This small Python project reads a CSV and maps a numeric column to animated raindrops. Each raindrop represents one row (by default the latest year per country). Larger values produce larger, faster, and more opaque drops. Click a drop to trigger a rain sound (WAV).

Features
- Maps a numeric column (default `Literacy rate`) to drop size, speed and opacity.
- Raindrop tails and terminal splash effects.
- Click a raindrop to play a WAV sound (`assets/rain.wav`).

Quick start

1. (Optional) Create a virtual environment and activate it.
2. Install requirements:

```powershell
python -m pip install -r requirements.txt
```

3. Place a WAV file at `assets/rain.wav` (optional). If missing, clicks are silent.
4. Run the visualization (defaults to `cross-country-literacy-rates.csv` in the same folder):

```powershell
python main.py
```

Useful arguments
- `--csv` path to CSV
- `--column` numeric column to map (default: `Literacy rate`)
- `--year` use a specific year (optional)
- `--width` and `--height` for window size

Notes
- The provided CSV in this repo contains a `Literacy rate` column; this script will use that by default. If you have a precipitation column in another CSV, point `--csv` and `--column` appropriately.

If you want, I can add a small sample `rain.wav` or enhance visuals (color mapping, country labels on hover, filters by region). Which would you like next?
