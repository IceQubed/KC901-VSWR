#!/usr/bin/env python3
"""
KC901V VNA S11/VSWR analyser.

Reads .ini measurement files from the input folder, plots VSWR vs frequency
with a highlighted band of interest, and computes a figure of merit per file
(best antenna = VSWR close to 1 over the range of interest).
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator


def parse_ini(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Parse a KC901V .ini file; return (freq_Hz, vswr) arrays."""
    freqs = []
    vswr = []
    in_curve = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "[Curve]":
                in_curve = True
                continue
            if in_curve:
                if line.startswith("["):
                    break
                if line.startswith("F:"):
                    part = line[2:].split(",", 1)
                    if len(part) == 2:
                        freqs.append(int(part[0]))
                        vswr.append(float(part[1]))
    if not freqs:
        raise ValueError(f"No curve data in {path}")
    return np.array(freqs), np.array(vswr)


def figure_of_merit(freq_Hz: np.ndarray, vswr: np.ndarray, fmin_Hz: float, fmax_Hz: float) -> dict:
    """
    Compute figures of merit for the band [fmin_Hz, fmax_Hz].
    Best antenna: VSWR close to 1 over the whole range.
    Returns dict with mean_vswr, max_vswr, score (0–1, 1 = best).
    """
    mask = (freq_Hz >= fmin_Hz) & (freq_Hz <= fmax_Hz)
    if not np.any(mask):
        return {"mean_vswr": np.nan, "max_vswr": np.nan, "score": 0.0, "n_points": 0}

    v = vswr[mask]
    n = len(v)
    mean_vswr = float(np.mean(v))
    max_vswr = float(np.max(v))
    # Score: 1 when all VSWR = 1; penalise mean squared deviation from 1.
    # Using 1 / (1 + mean((vswr-1)^2)) so score in (0, 1], 1 = perfect.
    mse = np.mean((v - 1.0) ** 2)
    score = 1.0 / (1.0 + mse)

    return {
        "mean_vswr": mean_vswr,
        "max_vswr": max_vswr,
        "score": score,
        "n_points": n,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse KC901V VNA S11/VSWR .ini files: plot curves and compute FOM."
    )
    parser.add_argument(
        "--fmin",
        type=float,
        default=1.7e9,
        metavar="Hz",
        help="Minimum frequency of interest in Hz (default: 1.7e9 = 1.7 GHz)",
    )
    parser.add_argument(
        "--fmax",
        type=float,
        default=2.5e9,
        metavar="Hz",
        help="Maximum frequency of interest in Hz (default: 2.5e9 = 2.5 GHz)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("input"),
        help="Folder containing .ini files (default: input)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Folder for all outputs: plot and FOM report (default: output)",
    )
    parser.add_argument(
        "--plot-file",
        type=str,
        default="vswr_curves.png",
        help="Plot filename inside output folder (default: vswr_curves.png)",
    )
    args = parser.parse_args()

    fmin_hz = args.fmin
    fmax_hz = args.fmax
    if fmin_hz >= fmax_hz:
        parser.error("--fmin must be less than --fmax")

    input_dir = args.input
    output_dir = args.output
    if not input_dir.is_dir():
        parser.error(f"Input folder not found: {input_dir}")

    ini_files = sorted(input_dir.glob("*.ini"))
    if not ini_files:
        print(f"No .ini files found in {input_dir}")
        return

    # Load all curves and FOMs
    all_data: list[tuple[str, np.ndarray, np.ndarray, dict]] = []
    for p in ini_files:
        try:
            freq, vswr = parse_ini(p)
            fom = figure_of_merit(freq, vswr, fmin_hz, fmax_hz)
            all_data.append((p.stem, freq, vswr, fom))
        except Exception as e:
            print(f"Warning: skip {p.name}: {e}")

    if not all_data:
        print("No valid .ini data loaded.")
        return

    # Plot
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = plt.cm.tab10(np.linspace(0, 1, max(len(all_data), 1)))
    for i, (name, freq, vswr, fom) in enumerate(all_data):
        freq_ghz = freq / 1e9
        label = f"{name} (FoM {fom['score']:.3f})"
        ax.plot(freq_ghz, vswr, label=label, color=colors[i % len(colors)], alpha=0.9)

    # Highlight band of interest
    ax.axvspan(fmin_hz / 1e9, fmax_hz / 1e9, alpha=0.15, color="green", zorder=0)
    ax.axvline(fmin_hz / 1e9, color="green", linestyle="--", alpha=0.6, linewidth=0.8)
    ax.axvline(fmax_hz / 1e9, color="green", linestyle="--", alpha=0.6, linewidth=0.8)

    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("VSWR")
    ax.set_title("VSWR vs frequency (band of interest shaded)")
    ax.xaxis.set_major_locator(MultipleLocator(0.1))
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8, frameon=True)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0.95)
    fig.tight_layout(rect=(0, 0, 0.92, 1))
    # Save plot to output folder (bbox_inches='tight' crops unused whitespace)
    plot_path = output_dir / args.plot_file
    fig.savefig(plot_path, dpi=150, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)

    # Build and save figure-of-merit report to output folder
    by_score = sorted(all_data, key=lambda x: x[3]["score"], reverse=True)
    fom_path = output_dir / "vswr_fom.txt"
    with open(fom_path, "w", encoding="utf-8") as report:
        report.write(
            "Figure of merit (band of interest: {:.3f}–{:.3f} GHz)\n".format(
                fmin_hz / 1e9, fmax_hz / 1e9
            )
        )
        report.write("-" * 70 + "\n")
        report.write(f"{'File':<45} {'Mean VSWR':>10} {'Max VSWR':>10} {'Score':>8}\n")
        report.write("-" * 70 + "\n")
        for name, _freq, _vswr, fom in by_score:
            report.write(
                f"{name:<45} {fom['mean_vswr']:>10.4f} {fom['max_vswr']:>10.4f} {fom['score']:>8.4f}\n"
            )
        report.write("-" * 70 + "\n")
        report.write(
            "Score: 1 = ideal (VSWR = 1 across band). Lower mean/max VSWR is better.\n"
        )
        best = by_score[0]
        report.write(f"Best in band: {best[0]} (score {best[3]['score']:.4f})\n")

    # Print summary to terminal and confirm all outputs are in output folder
    print("\nFigure of merit (band of interest: {:.3f}–{:.3f} GHz)".format(fmin_hz / 1e9, fmax_hz / 1e9))
    print("-" * 70)
    print(f"{'File':<45} {'Mean VSWR':>10} {'Max VSWR':>10} {'Score':>8}")
    print("-" * 70)
    for name, _freq, _vswr, fom in by_score:
        print(
            f"{name:<45} {fom['mean_vswr']:>10.4f} {fom['max_vswr']:>10.4f} {fom['score']:>8.4f}"
        )
    print("-" * 70)
    print("Score: 1 = ideal (VSWR = 1 across band). Lower mean/max VSWR is better.")
    print(f"Best in band: {best[0]} (score {best[3]['score']:.4f})")
    print(f"\nAll outputs written to {output_dir.resolve()}:")
    print(f"  - {plot_path.name}")
    print(f"  - {fom_path.name}")


if __name__ == "__main__":
    main()
