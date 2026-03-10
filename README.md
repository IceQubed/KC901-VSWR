# KC901-VSWR
Analyser for KC901 VNA S11/VSWR measurement output.

## Input formats

The script reads both:

- **`.ini`** – KC901V native format: `[Curve]` section with `F:<frequency_Hz>,<vswr>` lines.
- **`.xlsx`** – Excel export with an **S11-VSWR** sheet: columns *Frequency(Hz)* and *Value* (VSWR).

Example files (`.ini` and `.xlsx`) are in `example_data/`.

## Usage

1. Place KC901V `.ini` and/or `.xlsx` measurement files in the `input/` folder (or use `example_data/` for the bundled examples).
2. Install dependencies: `pip install -r requirements.txt`
3. Run the analyser (default band of interest: 1.7–2.5 GHz):

```bash
python analyse_vswr.py
```

To run on the example data:

```bash
python analyse_vswr.py --input example_data --output output
```

To use a different band (e.g. 1.6–1.8 GHz):

```bash
python analyse_vswr.py --fmin 1.6e9 --fmax 1.8e9
```

**Options:**
- `--fmin`, `--fmax`: Min/max frequency of interest in Hz (default: 1.7e9–2.5e9, i.e. 1.7–2.5 GHz).
- `--input`: Folder containing `.ini` and/or `.xlsx` files (default: `input`).
- `--output`: Folder for all outputs (default: `output`).
- `--plot-file`: Plot filename inside output folder (default: `vswr_curves.png`).

**Outputs** (written to `output/`):
- **vswr_curves.png** – VSWR vs frequency for all files, with the band of interest shaded.
- **vswr_fom.txt** – Figure-of-merit report: mean VSWR, max VSWR, and score per file (higher = better; ideal is VSWR ≈ 1 across the band).
