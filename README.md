# The Incubator Case Study

The overall purpose of the system is to reach a certain temperature within a box and keep the temperature regardless of content.
![Incubator](figures/system.png)

The system consists of:

- A Styrofoam box in order to have an insulated container.

- A heat source to heat up the content within the Styrofoam box.

- A fan to distribute the heating within the box

- A temperature sensor to monitor the temperature within the box

- A temperature Sensor to monitor the temperature outside the box

- A controller to communicate with the digital twin, actuate the heat source and the fan and read sensory information from the temperature sensors.

An introduction to the incubator case study is given in the following publication: TODO
and the up-to-date documentation in generated in the docs folder.

# Running the Unit Tests

## First-time setup
1. Open terminal in this folder.
2. Optional: create a virtual environment: `python -m venv venv`
3. Optional: activate the virtual environment (there are multiple possible activate scripts. Pick the one for your command line interface): 
   1. Windows Powershell:`.\venv\Scripts\Activate.ps1` 
   2. Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   1. `pip install -r ./requirements.txt`.
   
## After first time setup

Run/Read the script [./run_tests.ps1](./run_tests.ps1)

# Handling Datasets

1. Small datasets can be committed as csv files into the dataset folder.
2. Each dataset should come in its own folder, with some documentation explaining what it is all about, and a description of the physical setup.
3. Medium sized datasets should be zipped (same name as the csv file it contains, so it's easy to find when tests fail to load it).
4. Large datasets need to be put elsewhere (but a small version of the same dataset should be committed to this repo, with tests that exercise it)
