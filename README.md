# KC901-VSWR
Analyser for KC901 VNA S11 VSWR measurement output.

## Usage

1. Place KC901V `.ini` measurement files in the `input/` folder.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the analyser (default band of interest: 1.7–2.5 GHz):

```bash
python analyse_vswr.py
```

To use a different band (e.g. 1.6 - 1.8 GHz):

```bash
python analyse_vswr.py --fmin 1.6e9 --fmax 1.8e9
```

Options:
- `--fmin`, `--fmax`: Min/max frequency of interest in Hz (default: 1.7e9–2.5e9, i.e. 1.7–2.5 GHz).
- `--input`: Folder with `.ini` files (default: `input`).
- `--output`: Folder for all outputs (default: `output`).
- `--plot-file`: Plot filename inside output folder (default: `vswr_curves.png`).

All outputs go into the `output/` folder:
- **vswr_curves.png** – graph of all VSWR curves over the full sweep, with the band of interest shaded.
- **vswr_fom.txt** – figure-of-merit report per file: mean VSWR, max VSWR, and a score (higher scores are better). Best antenna = VSWR close to 1 over the whole range of interest.
