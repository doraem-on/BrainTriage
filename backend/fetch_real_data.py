"""Fetches the CSF-biomarker dataset used to train the Blood/CSF stage model.

Unlike the OASIS CSVs (CC0, committed directly to app/data/), this dataset's
license is CC BY-NC-ND per the author's own dataset description — noncommercial
use is fine (this is a noncommercial student hackathon project), but we avoid
redistributing a copy of the file itself, so it's fetched here instead of
committed.

No Kaggle account or token is required — kaggle>=2.x falls back to
anonymous access for public dataset downloads, verified working with zero
credentials. If that ever gets rate-limited/blocked from a given host's IP,
set KAGGLE_API_TOKEN (a single value from kaggle.com/settings -> API Tokens
-> Generate New Token) and the kaggle client will use it automatically —
no code change needed here.

Source: Dakterzada F, Jove M, Huerto R, Carnes A, Sol J, Pamplona R,
Pinol-Ripoll G. (2023) Changes in Plasma Neutral and Ether-Linked Lipids Are
Associated with The Pathology and Progression of Alzheimer's Disease. Aging
and Disease, 14(5), 1728. DOI: 10.34810/data614
Kaggle mirror: fereshtehjozaghkar/plasma-lipidomics-in-alzheimers-disease
"""
import os
import shutil
import subprocess

DATA_DIR = os.path.join(os.path.dirname(__file__), "app", "data_external")
CSV_NAME = "csf_biomarkers.csv"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    target = os.path.join(DATA_DIR, CSV_NAME)
    if os.path.exists(target):
        print(f"{target} already present, skipping download.")
        return

    kaggle_bin = shutil.which("kaggle")
    if not kaggle_bin:
        raise RuntimeError(
            "kaggle CLI not found on PATH — `pip install kaggle` installs it as a "
            "console script, not a `python -m kaggle` module (it has no __main__.py)."
        )
    subprocess.run([
        kaggle_bin, "datasets", "download",
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
