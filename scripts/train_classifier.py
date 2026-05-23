from pathlib import Path


def main() -> int:
    notebook = Path("notebooks/pandas_issue_classifier_colab.ipynb")
    print("Local classifier fine-tuning has been moved to Google Colab for GPU training.")
    print(f"Open and run: {notebook}")
    print("After Colab finishes, copy the exported classifier folder into:")
    print("  artifacts/classifier/")
    print("Then run:")
    print("  python3 scripts/evaluate_classifier.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
