# Samplenavigator2FDP

## description


## Installation

### Install Mamba
Packages are managed using the cross-platform package manager [Mamba](https://mamba.readthedocs.io/en/latest/index.html). Mamba is compatible with [Conda](https://conda.io/projects/conda/en/latest/index.html) but generally [faster](https://conda.org/learn/faq/) at resolving dependencies. Mamba can be installed using a [Miniforge installer](https://github.com/conda-forge/miniforge).

```{bash}
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```
Note: Mamba is a recommendation, as it is compatible with conda you can use conda as well.

### Create and activate `conda`/`mamba` environment

Dependencies are specified in `environment.yml`. See the [Mamba User Guide](https://mamba.readthedocs.io/en/latest/user_guide/mamba.html) for more information.

```{bash}
mamba env create -f environment.yml
mamba activate .conda
```

#### Install local `fairopal` Python package 

Install local package in the activated environment in development mode using `pip` but without installing package dependencies. Any dependencies must be installed in the `conda` environment, i.e., specified in `envs/environment.yml`.

```
pip install --no-build-isolation --no-deps -e .
```

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
```
Which mode the pipeline should run, if we want to replace current metadata of an existing catalog we set replace to True and set a catalog_purl URL below. Two different input formats are currently accepted: "Excel" or "csv"
mode: 
  replace: False
  input_format: csv

FDP related settings, the URL should not have a / at the end, the PURL should have one. The catalog_purl is ignored when replace is False, this is the URI/URL to the catalog that should be updated with the content of the input files.
FDP:
  URL: https://fdp.example.org
  PURL: https://fdp.example.org/
  catalog_purl: https://fdp.example.org/catalog/62fda175-c196-46f4-a067-d24a6de65468

Keyring parameters:
keyring:
  system: test-FDP
  username: email

We recommend using full paths to the data and schema files. catalog_shacl and dataset_shacl are the data schema/model that should be complied to. Each file corresponds to a FDP resource concept. catalog_input_file contains one catalog and datasets_input_file contains all datasets to upload. In Excel mode, these should be the same file and follow the example in data seen in the 'data' folder.
file_paths: # settings for running the main inside src:
  catalog_shacl: PATH
  dataset_shacl: PATH
  catalog_input_file: PATH
  datasets_input_file: PATH
```

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

## Roadmap
TODO
