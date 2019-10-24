# pyphe-growthcurves
Python module for non-parametric characterisation of microbial growth curves written by Stephan Kamrad (stephan.kamrad@crick.ac.uk) and part of the pyphe toolbox (maintained at https://github.com/Bahler-Lab/pyphe).

### Getting started
Pyphe-growthcurves is written in Python and is compatible with Python 2 and 3. It should run on pretty much any machine (Windows/Linux/Mac) and only requires the commonly used packages argparse, numpy, scipy and pandas, and matplotlib if you are using the plotting option. If you do not have python installed check out https://www.anaconda.com/distribution/. To get started, and to use standard options, use the following command line call:

    python pyphe-growthcurves.py --input example_data.csv --plots
    
It is important that your csv with the growth data is in the right format. The file must contain one growth curve per column. The first column must be the timepoints and there must be a header row with unique identifiers for each curve. For example data adn expected outputs, check out the files included in this repository. Sensible default parameters are set for all options but, depending on your data, you may wish to customise these, so check out the help section below.

### Results
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


### Help    
More help is available by running: python pyphe-growthcurves --help

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
                            
### Issues
This code has not been thoroughly tested yet, please use with caution and look at the results in detail. Please raise any issues on github or by email to stephan.kamrad@crick.ac.uk.
