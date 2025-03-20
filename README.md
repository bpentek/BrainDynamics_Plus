# Support library for BrainDynamics protocol

This package aims to extend the applicability of the [BrainDynamics protocol package](https://github.com/vlewir/BrainDynamics_STARProtocols) by implementing the storage of brain activity recordings (EEG, fMRI, etc. samples) and extracting samples from the experimental trials defined by the user.

The main idea of this package would be to write as many wrapper functions (in `src/braindynamics_plus/io/`) as needed for different data formats used for storing brain activity recordings. This would allow 
transferring from your dataset format into a more common ground that allows easier usage of the original protocol package.

## Requirements

- Python (tested for 3.12 and later versions)
    - braindynamics-starprotocol (1.0.0 or later)

## Setting up

### 1) Set up virtual python environment using python or conda.

For example:

```
python -m venv braindynamics_env
```

OR via Anaconda:

```
conda create --name braindynamics_env python=3.12
```

Install required dependencies:

### 2) Install package

Unlike the original `braindynamics-starprotocol` package, this one is not uploaded to PyPi. It can be installed locally by cloning this repository and using pip.

```
cd ~
git clone https://github.com/bpentek/BrainDynamics_Plus.git
pip install .
```

### 3) Usage

For an example of the pipeline, check `example/pipeline_example.py` script. The data used in that example is not available, so modify it to suit your needs.

For more details, feel free to look into the source code or contact me.
