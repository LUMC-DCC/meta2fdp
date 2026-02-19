# Meta2FDP

## description
This is a project to make an adapter from Samplenavigator to the LUMC FDP, at the same time it is the current project that has active development into making a package for onboarding metadata on the Health-RI Metadata catalog. This package should be able to handle the most common input types and be able to transform the given metadata into RDF and publish it to the LUMC FDP. Current version is able to parse, csv, excel and direct mssql connections. Current implementations are primairely for catalog and dataset metadata as these are the mandatory classes within the [Health-RI Schema](https://github.com/Health-RI/health-ri-metadata). Note: LLS/mongodb implementation is currently not in this project as it was made for the v1 schema and has to be reworked to be properly integrated.

## Installation

### Install Mamba
Packages are managed using the cross-platform package manager [Mamba](https://mamba.readthedocs.io/en/latest/index.html). Mamba is compatible with [Conda](https://conda.io/projects/conda/en/latest/index.html) but generally [faster](https://conda.org/learn/faq/) at resolving dependencies. Mamba can be installed using a [Miniforge installer](https://github.com/conda-forge/miniforge).

```{bash}
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```
Note: Mamba is a recommendation, as it is compatible with conda you can use conda as well.

### Create and activate `conda`/`mamba` environment

Dependencies are specified in `envs/meta2fdp.yml`. See the [Mamba User Guide](https://mamba.readthedocs.io/en/latest/user_guide/mamba.html) for more information. This is a minimum environment with only Python and the uv package manager created using `conda env export --no-builds --from-history > envs/meta2fdp.yml`.

```{bash}
mamba env create -f envs/meta2fdp.yml
mamba activate meta2fdp
uv sync
```

Creation of conda environment. See https://medium.com/@datagumshoe/using-uv-and-conda-together-effectively-a-fast-flexible-workflow-d046aff622f0

```
mamba create -n meta2fdp python=3.12
mamba activate meta2fdp
pip install uv
conda env export --no-builds | grep -v "^prefix: " > envs/meta2fdp.yml
```

Installing Python packages with uv

```
uv add pandas
```

### Install meta2fdp package



#### Install missing packages

Do not use `pip` for installing missing Python packages. The preferred way to install them is `mamba`. To find the missing package, search [anaconda.org](https://anaconda.org/). The preferred installation channel is [conda-forge](https://anaconda.org/conda-forge/repo). Use `mamba install` to install a package into the activated environment. 

Example: install [`pymongo`](https://anaconda.org/conda-forge/pymongo).

```
mamba install conda-forge::pymongo
```

Don't forget to add the newly installed package including its version to the dependencies in `envs/environment.yml`. Preferably, do not export the `environment.yml` file using `mamba env export`. If this is done anyways, use the `--from-history` flag to ensure cross-platform compatibility.

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
