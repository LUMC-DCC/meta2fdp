# Meta2FDP

`meta2fdp` is a Python package designed to automate the extraction, transformation, and publication of metadata to a FAIR Data Point (FDP) following the [Health‑RI Core Metadata Schema](https://github.com/Health-RI/health-ri-metadata). It enables programmatic onboarding of metadata from a variety of source systems to an FDP, making the process scalable, repeatable, and aligned with national FAIR metadata standards.

## Purpose

`meta2fdp` provides a structured way to build automated ETL pipelines that:

* Extract information (metadata) from internal or external data source systems
* Transform the metadata into RDF compliant with the Health‑RI schema
* Publish (create or update) the metadata to an FDP instance

The package reduces manual work, ensures schema compliance, and supports reuse of existing metadata already collected in systems such as Opal/Mica, SampleNavigator, SQL sources, and CSV or Excel files.

## Key features

* Source metadata ingestion with built-in parsers

    * OBiBa Opal/Mica (MongoDB/SQL sources)
    * SampleNavigator (SQL)
    * Excel/CSV-based metadata templates

* Schema‑aware transformation

    * Uses the Health‑RI `SemPyRo` Pydantic classes to map source-system metadata into valid RDF resources.
    * Ensures mandatory fields and schema structure are created correctly.

* Automated metadata publishing to FDP

    * Uploads new catalog and dataset metadata
    * Updates existing FDP resources using identifiers
    * Maintains relationships and resource links
    * Applies SHACL validation via the FDP backend
    * Minimizes manual editing after upload


## Installation

Installation of Python package dependencies using `uv` package manager.

```{bash}
# install meta2fdp and Python dependencies with uv
uv sync
source .venv/bin/activate
```

Make sure to have a keyring backend configured.



## Repository overview

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
│     ├─ extractors/
# TODO: decide whether to combines or separate connector and extractor/reader/parser
│     │
│     ├─ models/                    # Core domain models (clean & independent), pure Pydantic
│     │  ├─ base.py               # Abstract model - base class for metadata record
│     │  └─ HRIcore/              # Keep different schemas separate
│     │     └─ v2/                # Keep different versions separate
│     │        └─ dataset.py
# TODO: this should not contain functionality related to RDF serialization; it should only represent the data structures for schema validation; move serialization of models to rdf/serializers/ module per schema and version - this makes models/ independent of rdflib;
# TODO: add models/registry.py to register the differnt schemas/versions (important in future) (started);
# TODO: separate classes/concepts dataset, catalog, distribution etc.; - this might jus be imports from Sempyro; name the classes in a uniform way, so that schemas can be replaced easily
# TODO: base class should only enforce common behaviour; is currently schema-specific
# TODO: add default profiles
# don't reference connectors, pipelines, clients inside models
│     │
│     ├─ transformers/           # Pydantic model --> Graph
# TODO: implement a metadata adapter / schema handler that validates record and serializes to rdf; the current implementation resembles an adapter but mixed with the model; transformers are schema-specific; inject information form default profiles
hexagonal architecture
│     │
│     ├─ validation/ # for additional business / semantic validation (in addition to strcutural validation through Pydantic classes)
│     │
│     ├─ rdf/ # rdf serializer, graph building, managing namespaces
│     │   ├─serializers/
│     │   └─graph/
# only part that depends on rdflib
│     │
│     ├─ fdp/ # client for API interactions, publisher, updater
│     │
│     ├─ pipeline/
# TODO: create config-driven pipeline connecting all steps; start with base class
# TODO: additional orchestrator/ may be needed for scheduling / executing multiple pipelines in the future
# composes connector -> extractor -> transformer -> validator -> rdf serializer -> FDP publisher
# create base and registry.py

addtional logging.py, utils if needed, exceptions (in in modules where needed)

```

## Development

Python packages are installed with [`uv` Python package manager](https://docs.astral.sh/uv/).

```
# install missing packages with uv
# uv add <package-name>
# uv add --dev <package-name> # for development dependencies
```

```
# enable pre-commit hooks for linting and formatting
pre-commit install
```

When running tests, submodules are used to deploy an FDP locally for testing. This requires **Docker**.

```
# initialize local configuration file for Git submodules and fetch data from projects
git submodule init
git submodule update
```

### Documentation

```
# Clean existing doc files
rm -r docs/build/*
# Build documentation
#sphinx-build -M dirhtml docs/source docs/build
make html
```

<!--

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