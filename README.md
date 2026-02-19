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

Installation of [conda/mamba](#how-to-install-conda-or-mamba) environment and Python package dependencies using `uv` package manager.

```{bash}
# create conda environment from env file
mamba env create -f envs/meta2fdp.yml

# activate conda environment
mamba activate meta2fdp

# install meta2fdp and Python dependencies with uv
uv sync

# install missing packages with uv
# uv add <package-name>
```

```
# enable pre-commit hooks for linting and formatting
pre-commit install
```

Submodules are used to deploy an FDP locally for testing. This requires **Docker**.

```
# initialize local configuration file for Git submodules and fetch data from projects
git submodule init
git submodule update
```

Make sure to have a keyring backend configured.

#### How to install conda or mamba?

Either conda or mamba can be used cross-platform package manager.

[Mamba](https://mamba.readthedocs.io/en/latest/index.html) is compatible with [Conda](https://conda.io/projects/conda/en/latest/index.html) but generally [faster](https://conda.org/learn/faq/) at resolving dependencies. Mamba can be installed using a [Miniforge installer](https://github.com/conda-forge/miniforge).

```{bash}
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

## Development

### Environment

Dependencies othe rthan Python packages are specified in the environment file `envs/meta2fdp.yml`. See the [Mamba User Guide](https://mamba.readthedocs.io/en/latest/user_guide/mamba.html) for more information. 

Below is the code that was used to create the conda environment from scratch. See [Using UV and Conda Together Effectively: A Fast, Flexible Workflow](https://medium.com/@datagumshoe/using-uv-and-conda-together-effectively-a-fast-flexible-workflow-d046aff622f0)

Python packages were installed with [`uv` Python package manager](https://docs.astral.sh/uv/).

```
mamba create -n meta2fdp python=3.12
mamba activate meta2fdp
pip install uv
conda env export --no-builds | grep -v "^prefix: " > envs/meta2fdp.yml
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

## Install local `fairopal` Python package 

Install local package in the activated environment in development mode using `pip` but without installing package dependencies. Any dependencies must be installed in the `conda` environment, i.e., specified in `envs/environment.yml`.

```
pip install --no-build-isolation --no-deps -e .
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