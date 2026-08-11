# CSV catalog and dataset example

This example shows how to build a simple CSV-based metadata pipeline with meta2fdp.

## Files

- catalog.csv: example catalog metadata
- datasets.csv: example dataset metadata
- mappings.yaml: column mappings used by the extractor
- default_values.yaml: default values used by the transformer
- upload_catalogs_with_datasets.py: runnable example script

## Run

From the repository root:

```bash
python docs/examples/csv/catalogsanddatasets/upload_catalogs_with_datasets.py
```

The script expects the FDP connection details to be available through environment variables such as FDP_BASE_URL and FDP_USERNAME, and it can use a keyring entry for the API token.
