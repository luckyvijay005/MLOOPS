"""Dataset acquisition module.

Downloads or prepares the UCI Diabetes 130-US Hospitals (1999-2008) dataset.
Source: UCI Machine Learning Repository (Dataset ID: 296).
"""

import sys
import io
import zipfile
import requests
from pathlib import Path

# Ensure src can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.utils.config import Config
from src.utils.logger import logger
from scripts.generate_sample_data import generate_synthetic_dataset, generate_synthetic_id_mapping


def download_and_extract_dataset(force_download: bool = False) -> tuple[Path, Path]:
    """Acquires the UCI Diabetes 130-US Hospitals dataset.

    Returns:
        tuple[Path, Path]: Paths to (diabetic_data.csv, IDs_mapping.csv)
    """
    raw_dir = Config.RAW_DATA_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)

    data_csv = Config.DATASET_PATH
    mapping_csv = Config.MAPPING_PATH

    if data_csv.exists() and mapping_csv.exists() and not force_download:
        logger.info(f"Dataset already exists at: {data_csv} and {mapping_csv}")
        return data_csv, mapping_csv

    logger.info(f"Attempting to download dataset from: {Config.UCI_DOWNLOAD_URL}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(Config.UCI_DOWNLOAD_URL, headers=headers, timeout=30)
        response.raise_for_status()

        logger.info("Archive downloaded successfully. Extracting contents...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for member in z.namelist():
                filename = Path(member).name
                if filename in ["diabetic_data.csv", "IDs_mapping.csv"]:
                    target_file = raw_dir / filename
                    with z.open(member) as source, open(target_file, "wb") as target:
                        target.write(source.read())
                    logger.info(f"Extracted {filename} to {target_file}")

        if data_csv.exists() and mapping_csv.exists():
            logger.info("Dataset download and extraction complete.")
            return data_csv, mapping_csv

    except Exception as exc:
        logger.warning(
            f"Automated download failed or was unavailable: {exc}. "
            f"If working offline, ensure '{data_csv}' is provided manually "
            f"or use the synthetic development dataset."
        )

    # If the file still doesn't exist, we generate the synthetic sample as development fallback
    if not data_csv.exists():
        logger.warning(f"Initializing fallback development dataset at {data_csv}...")
        generate_synthetic_dataset(num_records=1000, output_path=data_csv)
    
    if not mapping_csv.exists():
        generate_synthetic_id_mapping(output_path=mapping_csv)

    return data_csv, mapping_csv


if __name__ == "__main__":
    download_and_extract_dataset()
