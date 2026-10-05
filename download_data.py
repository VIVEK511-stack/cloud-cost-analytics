"""
Download cloud billing dataset from Kaggle.
Run: python download_data.py
"""

import os
import sys

def download_from_kaggle():
    """Instructions for manual download."""
    print("=" * 60)
    print("CLOUD COST ANALYTICS - DATA DOWNLOAD")
    print("=" * 60)
    print()
    print("Option 1 - Kaggle API (recommended):")
    print("  1. Go to kaggle.com/account -> Create API Token")
    print("  2. Place kaggle.json in ~/.kaggle/")
    print("  3. Run: pip install kaggle")
    print("  4. Run: kaggle datasets download -d <dataset-id> -p data/")
    print()
    print("Option 2 - Manual Download:")
    print("  1. Go to kaggle.com/datasets")
    print("  2. Search: 'cloud billing data' or 'AWS cost usage'")
    print("  3. Download CSV")
    print(f"  4. Save as: {os.path.abspath('data/cloud_billing.csv')}")
    print()
    print("Recommended datasets:")
    print("  - alexismailz/cloud-cost-optimization-dataset")
    print("  - AWS Cost and Usage Reports sample data")
    print("  - Any cloud billing CSV with: date, service, cost, region")
    print("=" * 60)

    # Check if data already exists
    data_path = 'data/cloud_billing.csv'
    if os.path.exists(data_path):
        size_mb = os.path.getsize(data_path) / (1024 * 1024)
        print(f"\nDataset found: {data_path} ({size_mb:.1f} MB)")
        return True
    return False

if __name__ == '__main__':
    if not download_from_kaggle():
        print("\nNo data file found. Please download manually.")
        sys.exit(1)
