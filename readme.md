# Digital Twin for Agriculture

## Description

I don't have the vibe yet for this

## Setup

We should setup a virtual environment so we don't mess-up our OS built-in systems. The choice of 'conda' versus other virtual environments for Python was because my 2015 MacBook with macOS Monterey (Version 12.7.6) was unable to install the 'tensorflow' library any other way.

Install Anaconda on your system by following the official site [here](https://www.anaconda.com/docs/getting-started/miniconda/install)

After installation, in the root of the repo open a command line and run

`conda env create -f environment.yml`

This will create a conda virtual environent called '**tf**' that you can then activate by running `conda activate tf` and it you ever forget all the conda environments you have (like I did) you can always run `conda env list`.