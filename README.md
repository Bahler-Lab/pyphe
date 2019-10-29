![pyphe logo](https://github.com/Bahler-Lab/pyphe/blob/master/icons/toolbox-72dpi_white.png)

# Welcome to the pyphe toolbox
A python toolbox for phenotype analysis of arrayed microbial colonies written by Stephan Kamrad (stephan.kamrad at crick.ac.uk).

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
This tools allows you to take consecutive scans of sets of plates, which are then automatically cropped, rotated and named in in a continuos filename scheme of your choice. 

#### Prerequisites
1. This tool will only run on Linux operating systems and uses the SANE library for image acquisition.

2. Make sure your scanner is installed correctly and you can acquire images using the scanimage command. The Gray mode will only work on Epson V800 scanners (potentially the V700 and V750 model as well) and the TPU8x10 transmission scanning source must be enabled. This was first implemented in by Zackrisson et al in the [scanomatics pipeline](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5015956/) and requires the installation of a hacked SANE driver. See the instructions in their [wiki](https://github.com/Scan-o-Matic/scanomatic/wiki/Installing-scanners) for how to do this.

2. Make sure [ImageMagick](https://imagemagick.org/index.php) is installed and the 'convert' tool can be called from the command line.

3. If the Pyphe toolbox has been installed correctly, you should be able to run pyphe-scan in your terminal. If not, check that the files in the 'bin' directory are executable and the bin folder has been added to your path variable.

4. With a laser cutter, make a fixture to hold your plates in place. We provide an svg file with the cutting shape in the Documentation directory. Use tape to hold your fixture into place, it should be pushed against the back of the scanner (where the cables are) with the top of the plates facing left. Pyphe-scan and pyphe-quantify come pre-configured for using the provided fixture on an Epson V800 scanner but it is easy to add your own fixture and cropping settings. If you want to use your own fixture, see below of how to add the geometry information to pyphe-scan. 

### Scan plates 

1. Open the file manager and navigate to the folder in which you want to save your images. The script will create a sub-folder that begins with the current date to save all your images. 

2. Right click and select 'Open in Terminal'

3. Run scanplates with the options as detaild below. 

```
usage: pyphe-scan [-h] [--nplates NPLATES] [--start START] [--prefix PREFIX]
                  [--postfix POSTFIX] [--fixture {som3_edge,som3}]
                  [--resolution {150,300,600,900,1200}] [--scanner {1,2,3}]
                  [--mode {Gray,Color}]

Welcome to pyphe-scan, part of the pyphe toolbox. Written by
stephan.kamrad@crick.ac.uk and maintained at https://github.com/Bahler-
Lab/pyphe

optional arguments:
  -h, --help            show this help message and exit
  --nplates NPLATES     Number of plates to scan. This defaults to 100 and the
                        script can be terminated by Ctr+C when done.
  --start START         Where to start numbering from. Defaults to 1.
  --prefix PREFIX       Name prefix for output files. The default is the
                        current date YYYYMMDD.
  --postfix POSTFIX     Name postfix for output files. Defaults to empty
                        string.
  --fixture {som3_edge,som3}
                        ID of the fixture you are using.
  --resolution {150,300,600,900,1200}
                        Resolution for scanning in dpi. Default is 600.
  --scanner {1,2,3}     Which scanner to use. Scanners are not uniquely
                        identified and may switch when turned off/unplugged.
                        This option does not need to be set when only one
                        scanner is connected.
  --mode {Gray,Color}   Which color mode to use for scanning. Defaults to
                        Gray.
```

All arguments except the fixture have default values and are optional. A folder prefix_postfix will be created in your current directory and the program will abort if a folder with this name already exists. 



### Pyphe-scan-timecourse

### Pyphe-growthcurves
This tool performs non-parametric analysis of growth curves. It was written specifically to analyse colony size timeseries data obtained with _pyphe-quantify _timeseries_.

#### Getting started
It is important that your csv with the growth data is in the right format. The file must contain one growth curve per column. The first column must be the timepoints and there must be a header row with unique identifiers for each curve. For example data and expected outputs, check out the files included in this Documentation folder. Sensible default parameters are set for all options but, depending on your data, you may wish to customise these, so check out the help section below.

    python pyphe-growthcurves.py --input example_data.csv --plots
    


#### Interpreting results
Pyphe-growthcurves will produce a csv file with extracted growth parameters. The maximum slope is determined by fitting all possible linear regressions in sliding windows of length n and chosing the one with the highest slope. The lag phase is determined as the first timepoint which exceeds a settable relative or absolute threshold. 

| Parameter        | Explanation  |
| ---------------- |---------------|
|initial biomass|The average of the first n timepoints of the growth curve|
|lag |  Lag phase |
| max_slope| The maximum slope of the growth curve|
| r2 | The R2 parameter of the linear regression that produced the highest maximum slope |
|t_max | Time at which maximum growth slope is reached (center of the sliding window)|
|y-intercept|Y-intercept of the regression which produced the maximum slope|
|x-intercept|X-intercept of the regression which produced the maximum slope. This is interpreted as lag phase by some people|


#### Options
More help is available by running: pyphe-growthcurves --help

    usage: pyphe-growthcurves.py [-h] --input INPUT [--fitrange FITRANGE]
                                 [--lag-method {abs,rel}]
                                 [--lag-threshold LAG_THRESHOLD]
                                 [--t0-fitrange T0_FITRANGE] [--plots]
                                 [--plot-ylim PLOT_YLIM]

    optional arguments:
      -h, --help            show this help message and exit
      --input INPUT         Path to the growth curve file to analyse. This file
                            contains one growth curve per column. The first column
                            must be the timepoints and there must be a header row
                            with unique identifiers for each curve.
      --fitrange FITRANGE   Number of timepoint over which to fit linear
                            regression. Defaults to 4. Please adjust this to the
                            density of your timepoints and use higher values for
                            more noisy data.
      --lag-method {abs,rel}
                            Method to use for determining lag. "abs" will measure
                            time until the defined biomass threshold is crossed.
                            "rel" will fist determine the inital biomass and
                            measure the time until the biomass has passed this
                            value times the threshold. Defaults to "rel".
      --lag-threshold LAG_THRESHOLD
                            Threshold to use for determining lag. With method
                            "abs", this will measure time until the defined
                            biomass threshold is crossed. With "rel" will fist
                            determine the inital biomass and measure the time
                            until the biomass has passed this value times the
                            threshold. Defaults to 2.0, so with method "rel", this
                            will measure the time taken for the first doubling.
      --t0-fitrange T0_FITRANGE
                            Specify the number of timepoint to use at the
                            beginning of the growth curve to determine the initial
                            biomass by averaging them. Defaults to 3.
      --plots               Set this option (no argument required) to produce a
                            plot of all growthcurves as pdf.
      --plot-ylim PLOT_YLIM
                            Specify the upper limit of the y-axis of growth curve
                            plots. Useful if you want curves to be directly
                            comparable. If not set, the axis of each curve is
                            scaled to the data.
                            


### Pyphe-quantify


### Pyphe analyse


## Support and FAQs
If you run into trouble, please check if your problem is discussed below. If not, feel free to send an email to stephan.kamrad@crick.ac.uk or raise an issue here on github. 

- **How do I run command line tools under Windows?** Under Linux, the scripts in the bin folder are automatically copied into a folder in the PATH during installation of the package. This is not supported under Windows, so you need to specify the path manually. Download pyphe from github and place the scripts in the bin folder in a convenient location. Now you can run pyphe scripts by typing 'python folder/with/scripts/pyphe-quantify' followed by all other arguments as usual.
