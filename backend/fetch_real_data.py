"""Fetches the CSF-biomarker dataset used to train the Blood/CSF stage model.

Unlike the OASIS CSVs (CC0, committed directly to app/data/), this dataset's
license is CC BY-NC-ND per the author's own dataset description — noncommercial
use is fine (this is a noncommercial student hackathon project), but we avoid
redistributing a copy of the file itself, so it's fetched here instead of
committed. Requires a Kaggle API token at ~/.kaggle/kaggle.json.

Source: Dakterzada F, Jove M, Huerto R, Carnes A, Sol J, Pamplona R,
Pinol-Ripoll G. (2023) Changes in Plasma Neutral and Ether-Linked Lipids Are
Associated with The Pathology and Progression of Alzheimer's Disease. Aging
and Disease, 14(5), 1728. DOI: 10.34810/data614
Kaggle mirror: fereshtehjozaghkar/plasma-lipidomics-in-alzheimers-disease
"""
import os
import subprocess
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "app", "data_external")
CSV_NAME = "csf_biomarkers.csv"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    target = os.path.join(DATA_DIR, CSV_NAME)
    if os.path.exists(target):
        print(f"{target} already present, skipping download.")
        return

    subprocess.run([
        sys.executable, "-m", "kaggle", "datasets", "download",
        "-d", "fereshtehjozaghkar/plasma-lipidomics-in-alzheimers-disease",
        "-p", DATA_DIR, "--unzip",
    ], check=True)

    # the zip contains one CSV with a long, spaced filename; normalize it
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".csv") and fname != CSV_NAME:
            os.rename(os.path.join(DATA_DIR, fname), target)
    print(f"Fetched real CSF biomarker data to {target}")


if __name__ == "__main__":
    main()
