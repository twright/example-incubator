# The Incubator Case Study

The overall purpose of the system is to reach a certain temperature within a box and keep the temperature regardless of content.
![Incubator](figures/system.png)

An introduction to the incubator case study is given in the following publication: TODO
and the up-to-date documentation in generated in the docs folder.

# Generating and Viewing Documentation

Run/Read the script [./docs/build_docs.ps1](./docs/build_docs.ps1)

# pipenv primer
PIPENV is the recommended packaging tool from [python.org](https://packaging.python.org/guides/tool-recommendations/#application-dependency-management)

To execute a Python script prefix it with `pipenv run`. I.e. `pipenv run python test.py`

Alternatively, start a shell with the pipenv wth `pipenv shell`.  
Within this shell, one can directly use i.e. `python test.py`

To install a new package use `pipenv install PACKAGE`

To ensure your local development environment will be same as the deployed lock the pipefile with `pipenv lock`

# Running the Unit Tests

## First-time setup
1. Open terminal in this folder.
1. Install pipenv: `pip install pipenv`
1. Install from pipfile: `pipenv install`


## After first time setup

Run/Read the script [./run_tests.ps1](./run_tests.ps1) for windows or [./run_tests.sh](./run_tests.sh) for UNIX 

Or execute `pipenv `

# Handling Datasets

1. Small datasets can be committed as csv files into the dataset folder.
2. Each dataset should come in its own folder, with some documentation explaining what it is all about, and a description of the physical setup.
3. Medium sized datasets should be zipped (same name as the csv file it contains, so it's easy to find when tests fail to load it).
4. Large datasets need to be put elsewhere (but a small version of the same dataset should be committed to this repo, with tests that exercise it)

# Creating Unit Tests

Follow the example of [./tests/example_test.py](./tests/example_test.py)

Each test should correspond to one experiment, and each experiment should be targeted at answering one question.

Commit the tests in a way that they can be run automatically and quickly (use the `self.cli_mode`).
If `self.cli_mode` is true:
1. Plotting should be avoided.
2. Optimization problems can be parameterized with a small number of evaluations (so they still run, but it's much quicker).
3. Tests that involve large data should be adapted in a way that it can be run quickly (e.g., with a subset of the data).
