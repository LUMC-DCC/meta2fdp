# Meta2FDP

`meta2fdp` is a Python framework for extracting metadata from source systems, transforming that metadata into RDF, and publishing it to a FAIR Data Point (FDP) instance.

## Why use meta2fdp?

- Build reusable metadata pipelines with connector, extractor, transformer, and publishing components.
- Keep source-specific logic separate from FDP publishing logic.
- Extend the project with new connectors, extractors, schema transformers, or FDP clients.
- Use existing Health-RI schema support and RDF publishing workflows.

## Quick start

Install the project and dependencies:

```bash
uv sync
python -m pip install -e .
```

Run the package entry point to verify installation:

```bash
meta2fdp
```

## Example usage

Use the Python API to assemble a pipeline:

```python
from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.config.transformer.transformer import TransformerConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig
from meta2fdp.pipeline.publish_metadata import PublishMetadataPipeline
from meta2fdp.bootstrap import register_modules

registries = register_modules()
transformer_configs = register_transformer_configs()

connector_config = CSVConnectorConfig(
    name="csv_connector",
    connector_name="CSVConnector",
    connector_type="csv",
    separator=";",
    header=0,
    catalog_input_file=Path("tests/data/input/Health-RI_LUMC_catalogue.csv"),
    dataset_input_file=Path("tests/data/input/Health-RI_LUMC_datasets.csv"),
)

extractor_config = ExtractorConfig(
    name="df_extractor",
    config_type="extractor",
    extractor_name="DFExtractor",
    extractor_type="df",
    mapping_file=Path("tests/config/mappings_test.yaml"),
)
extractor_config.get_mappings()  # Load mappings from the specified mapping file

schema_config = transformer_configs["HRIcore_v2_LUMC"]

fdp_config = FDPConfig(
    name="FDPClient",
    fdp_version="v2",
    URL="http://localhost",
    environmentprovider=registries["secrets"]["env"](),
    keyringprovider=registries["secrets"]["keyring"](),

)

pipeline = PublishCatalogsDatasetsMetadataPipeline(
    connector_config=connector_config,
    extractor_config=extractor_config,
    schema_config=schema_config,
    FDP_config=fdp_config,
    registries=registries,
)

pipeline.run()
```

## Project structure

- `src/meta2fdp/connectors/` — source system connectors
- `src/meta2fdp/extractors/` — extractors for raw source data
- `src/meta2fdp/transformers/` — transformer modules and schema adaptors
- `src/meta2fdp/fdp/` — FAIR Data Point clients
- `src/meta2fdp/pipeline/` — orchestration layer linking the pipeline stages
- `src/meta2fdp/config/` — typed configuration objects
- `docs/` — Sphinx documentation source and examples

## Installation

```bash
uv sync
python -m pip install -e .
```

If you prefer not to use `uv`, install with:

```bash
python -m pip install -e .
```

## Documentation

Build the documentation from the `docs` folder:

```bash
cd docs
sphinx-build -M html source build
```

Then open `docs/build/index.html`.

## Contributing

See `CONTRIBUTING.md` for details on how to contribute new modules, tests, and documentation.

## License

This project is licensed under Apache-2.0 .

<!--

```
meta2fdp/
│
├─ src/
│  └─ meta2fdp/
│     │
│     ├─ __init__.py
│     │
│     ├─ config/                    # Configuration of models & defaults; typed with Pydantic
│     │  ├─ connector.py
│     │  ├─ schema.py
│     │  └─ etc.
# TODO: create config/ modules - connector type, schema version, profiles, FDP endpoint, pipeline options; don't mix config logic with business logic
# TODO: add configuration registry
│     │
│     ├─ connectors/
# TODO: create base class connector; create different connectors for sqlserver, mongodb, csv etc.; this does not handle the content, it only establishes the connection; handle opening of connections, authentication, closing connection
# should also retrieve information from source system, but logically separate establishing connection and reading information
# base connector defines connect, extract, clode/cleanup; subclassess for SQL, RESTAPI, ; the subclass for specific databases
│     ├─ extractors/  # raw input → pandas.df
# TODO: decide whether to combines or separate connector and extractor/reader/parser
since current sources are dataframe-like, they are read as dataframe; this could change in future
https://openreview.net/pdf?id=sK9YZ4JyyI
│     │
│     ├─ models/                    # Core domain models (clean & independent), pure Pydantic
│     │  ├─ base.py               # Abstract model - base class for metadata record
│     │  └─ HRIcore/              # Keep different schemas separate
│     │     └─ v2/                # Keep different versions separate
│     │        └─ dataset.py # sempyro
│     │        └─ catalog.py
# TODO: this should not contain functionality related to RDF serialization; it should only represent the data structures for schema validation; move serialization of models to rdf/serializers/ module per schema and version - this makes models/ independent of rdflib;
# TODO: add models/registry.py to register the differnt schemas/versions (important in future) (started);
# TODO: separate classes/concepts dataset, catalog, distribution etc.; - this might jus be imports from Sempyro; name the classes in a uniform way, so that schemas can be replaced easily
# TODO: base class should only enforce common behaviour; is currently schema-specific
# TODO: add default profiles
# don't reference connectors, pipelines, clients inside models

│     ├─ profiles/
│     │  └─ HRIcore/              # Keep different schemas separate
│     │     └─ v2/                # Keep different versions separate
│     │        └─ dataset/LUMC.py
│     │
│     ├─ transformers/           # df → Pydantic model → Graph
1. combine source df and profile - df processing
2. pydantic instantiation - mapping execution
# TODO: implement a metadata adapter / schema handler that validates record and serializes to rdf; the current implementation resembles an adapter but mixed with the model; transformers are input and schema-specific; inject information form default profiles
pydantic classes from sempyro function as mapping executor
hexagonal architecture - https://jmgarridopaz.github.io/content/hexagonalarchitecture.html#tc2

updater/ logic about what to do when
milestone 4
│     │
│     ├─ validation/ # for additional business / semantic validation (in addition to strcutural validation through Pydantic classes)
milestone 3; examples: check if title is unique enough and meaningful
input: graph from transformer; output: yes/no
│     │
│     ├─ rdf/ # graph building, managing namespaces, graph comparison; what is now graphutils
│     │
│     ├─ fdp/ # client for API interactions, interactions to publish, to update, to delete
functionality to interact with FDP, no logic about when to do what
│     │
│     ├─ pipeline/
# TODO: create config-driven pipeline connecting all steps; start with base class
# TODO: additional orchestrator/ may be needed for scheduling / executing multiple pipelines in the future
# composes connector -> extractor -> transformer -> validator -> rdf serializer -> FDP publisher
# create base and registry.py

addtional logging.py, utils if needed, exceptions (in in modules where needed)
```

## Running the pipeline

### Set up keyring library:
When running the pipeline in WSL, keyring-pybridge is needed to run keyring with Windos Credential Locker. Use setup_keyring_env.sh to enable a connection to the windows system for keyring.
NOTE: This script adds two export commands to bashrc file, this file is run on startup of a terminal. This change is permanent until manually removed by the user.

### configuration file

Configuration files are found in the folder config. Each one is specific for one usecase. default_values.yaml is not used (yet)

Once the configuration file is set, you can run the pipeline by running the src/BEAT/main.py file. (preferably inside it's folder)


## Documentation generation


### Documentation with Sphinx

*Note that this is not needed, when files are already added to the Git repository! It is only needed when `doc/` is empty.*

The documentation for this project is generated using [Sphinx](https://www.sphinx-doc.org/en/master/index.html). 

## System variables
To ensure Sphinx is able to parse the project from the local install of the Python package set the following environment variables:
```
export CONF_PATH="/PATHTOPROJECT/config/FDP/configuration.yaml"

```



## new documentation
To create the required files from scratch, follow the instructions in the [Sphinx documentation *Getting Started*](https://www.sphinx-doc.org/en/master/usage/quickstart.html). In the example, `sphinx-quickstart` is run in the `doc` directory and source and build directories are separated.

```
sphinx-quickstart
```

This generates the following files and folders:

```
Makefile
build
make.bat
source

./build:

./source:
_static
_templates
conf.py
index.rst

./source/_static:

./source/_templates:
```



### Edit documentation

Add [docstrings](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html) to the `fairopal` package source code to document Python modules, classes, and functions.

Edit `doc/source/conf.py` to configure the project, e.g., specifying a different template, the path to the source directory of a Python module, or adding extensions. [`sphinx.ext.autodoc`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) can be used to automatically include informtion from docstrings.

Edit `doc/source/index.rst` to add content to the documentation.

### Build documentation

Run this command from the `doc/` directory. It will create `html` files in `doc/build/html/`.

```
sphinx-build -M html source build
```

## Usage
For usage of parsers check __main__ functions on the bottom of the file.

## testing
Environment setup for test-FDP docker compose:
BASH:
```
export FDP_CLIENT_VERSION=1.16.3
export FDP_VERSION=1.16.2
```

Windows Powershell:
```
$env:FDP_CLIENT_VERSION = '1.16.3'
$env:FDP_VERSION = '1.16.2'
```

SHACL files that are used for integration testing are modified so all " symbols are escaped. This is because the original SHACL files are not recognized as a full string when put in JSON


## Roadmap
TODO

-->