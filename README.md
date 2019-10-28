![pyphe logo](https://github.com/Bahler-Lab/pyphe/blob/master/icons/toolbox-72dpi_white.png)

# Welcome to the pyphe toolbox
A python toolbox for phenotype analysis of arrayed microbial colonies written by Stephan Kamrad (stephan.kamrad at crick.ac.uk)
Please see our preprint for a detailed description of the algorithms and applications.


## Installation
1. We recommend to run pyphe on a Linux OS. It is possible to install pyphe on other platforms but calling scripts from the command line is not so straight-forward in Windows. Scanning requires a Linux OS with a correctly configured [SANE driver](http://www.sane-project.org/) and [ImageMagick](https://imagemagick.org/) installed.
2. Pyphe requires Python 3 and a few common packages, available through the [anaconda distribution](https://www.anaconda.com/distribution/).
3. Install pyphe by running 'pip install pyphe' in your terminal.
4. Open a new terminal and try and run 'pyphe-quantify -h' which should show the help page of one of pyphe's command line tools. See here for what to do if you're on Windows.


## Overview
A typical fitness screen with pyphe will involve:
1. Image acquisition with pyphe-scan, or pyphe-scan-timecourse
2. Quantification of colony properties from images using pyphe-quantify. In the case of growth curves, parameters are additionally extracted with pyphe-growthcurves.
3. Normalisation and data aggregation using pyphe-analyse.
Please see our paper for a detailed protocol.

## Manual

### Pyphe-scan

### Pyphe-scan-timecourse

### Pyphe-growthcurves

### Pyphe-quantify


### Pyphe analyse


## Support and FAQs
If you run into trouble, please check if your problem is discussed below. If not, feel free to send an email to stephan.kamrad@crick.ac.uk or raise an issue here on github. 

- **How do I run command line tools under Windows?** Under Linux, the scripts in the bin folder are automatically copied into a folder in the PATH during installation of the package. This is not supported under Windows, so you need to specify the path manually. Download pyphe here from github and place the scripts in the bin folder in a convenient location. Now you can run pyphe scripts by typing 'python folder/with/scripts/pyphe-quantify' followed by all other arguments as usual.
