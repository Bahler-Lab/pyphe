![pyphe logo](https://github.com/Bahler-Lab/pyphe/blob/master/icons/toolbox-72dpi_white.png)

# Welcome to the pyphe toolbox
A python toolbox for phenotype analysis of arrayed microbial colonies written by Stephan Kamrad (stephan.kamrad at crick.ac.uk).

For a quick overview, please see our [10 minute video tutorial](https://www.youtube.com/watch?v=lQ3lXIdhA1c&t=5s).

For a more detailed protocol, including growth curves and viability assays, please see our [protocol preprint](https://www.researchsquare.com/article/rs-401914/v1).

For more background information, please see our [_eLife_ paper](https://elifesciences.org/articles/55160).

Please cite as:
> Kamrad, S., Rodríguez-López, M., Cotobal, C., Correia-Melo, C., Ralser M., Bähler J. (2020). Pyphe, a python toolbox for assessing microbial growth and cell viability in high-throughput colony screens. eLife 9:e55160

## Installation
1. Most tools are cross-platform compatible but scanning will only work on a Linux OS. The scanners need to be accessible by [SANE](http://www.sane-project.org/) and [ImageMagick](https://imagemagick.org/) needs to be installed and accessible from the command line.
2. Pyphe requires Python 3 and a few common packages, available through the [anaconda distribution](https://www.anaconda.com/distribution/).
3. Install pyphe by running 'pip install pyphe' in your terminal.
4. Open a new terminal and try and run 'pyphe-quantify -h' which should show the help page of one of pyphe's command line tools. On Windows, make sure you are using the Anaconda Prompt, not the Anaconda Powershell Prompt.


## Overview
A typical fitness screen with pyphe will involve:
1. Image acquisition with [_pyphe-scan_](#pyphe-scan), or [_pyphe-scan-timecourse_](#pyphe-scan-timecourse)
2. Quantification of colony properties from images using [_pyphe-quantify_](#pyphe-quantify). In the case of growth curves, parameters are additionally extracted with [_pyphe-growthcurves_](#pyphe-growthcurves).
3. Normalisation and data aggregation using [_pyphe-analyse_](#pyphe-analyse).
4. Statistics and hit calling using [_pyphe-interpret_](#pyphe-interpret)
Please see our paper for a detailed protocol and explanations of the algorithms.


## Support
Please check the manuals below carefully, they are also available in the terminal by running the command with the -h option only. If things are still not working, please email me (stephan.kamrad@gmail.com) and I will try and help. If you think you have discovered a bug, or would like to request a new feature, please raise an issue on www.github.com/Bahler-Lab/pyphe.

If you get an error like this, make sure you are not using the Anaconda Powershell Prompt:
```python: can't open file 'C:\Users\user1\Anaconda3\Scripts"C:\Users\user1\Anaconda3\Scripts\pyphe-quantify.bat  -h ': [Errno 22] Invalid argument```

## Manual

All pyphe tools have a similar command line interface, based on the python argparse package. Generally, parameters are set using --<parameter_name> optionally followed by a value. All _pyphe_ tools can be used with relative file paths so make sure to navigate to the correct working directory before running a _pyphe_ command.

 
### Pyphe-scan
This tools allows you to take consecutive scans of sets of plates, which are then automatically cropped, rotated and named in in a continuos filename scheme of your choice. 

#### Prerequisites
1. This tool will only run on Linux operating systems and uses the SANE library for image acquisition.

2. Make sure your scanner is installed correctly and you can acquire images using the scanimage command. The Gray mode will only work on Epson V800 and V850 scanners (potentially the V700 and V750 model as well) and the TPU8x10 transmission scanning source must be enabled. This should work by default if you are using the V800/850 model and a recent Linux OS. Otherwise, there is excellent documentation available from Zackrisson et al. and the [scanomatics pipeline](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5015956/) for how to make this work using a hacked SANE driver. Please see the instructions in their [wiki](https://github.com/Scan-o-Matic/scanomatic/wiki/Installing-scanners).

2. Make sure [ImageMagick](https://imagemagick.org/index.php) is installed and the 'convert' tool can be called from the command line.

3. If the Pyphe toolbox has been installed correctly, you should be able to run _pyphe-scan_ in your terminal. 

4. With a laser cutter, make a fixture to hold your plates in place. We provide an svg file with the cutting shape in the Documentation directory. Use tape to hold your fixture into place, it should be pushed against the back of the scanner (where the cables are) with the top of the plates facing left. Pyphe-scan and pyphe-quantify come pre-configured for using the provided fixture on an Epson V800/V850 scanner but it is easy to add your own fixture and cropping settings. If you want to use your own fixture, see below of how to add the geometry information to pyphe-scan. 

#### Scanning plate batches

1. Open the file manager and navigate to the folder in which you want to save your images. The script will create a sub-folder that begins with the current date to save all your images. 

2. Right click and select 'Open in Terminal'

3. Run scanplates with the options as detaild below. 

```
usage: pyphe-scan [-h] [--nplates NPLATES] [--start START] [--prefix PREFIX]
                  [--postfix POSTFIX] [--fixture {som3_edge,som3}]
                  [--resolution {150,300,600,900,1200}] [--scanner {1,2,3}]
                  [--mode {Gray,Color}]


optional arguments:
  -h, --help            show this help message and exit
  --nplates NPLATES     Number of plates to scan. This defaults to 100 and the
                        script can be terminated by Ctr+C when done.
  --start START         Where to start numbering from. Defaults to 1.
  --prefix PREFIX       Name prefix for output files. The default is the
                        current date YYYYMMDD.
  --postfix POSTFIX     Name postfix for output files. Defaults to empty
                        string.
  --fixture {som3_edge,som3,som3-color}
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

This tool acquires image timeseries by scanning in fixed time intervals. For each position in the fixture, a folder is created. Image names contain number of scan. Other options for this tool are similar to [_pyphe-scan_](#pyphe-scan). More than one scanner can be connected and used at the same time. Scanner numbers are defined by the order in which they are connected to the computer. Proceed as follows: (1) disconnect all scanners, (2) prepare the first scanner with plates, connect it and turn it on. (3) start scanning with --scanner 1 option, (4) prepare the second scanner, connect it and turn it on, (5) start scanning with --scanner 2 option. Repeat step (4) and (5), each time incrementing the --scanner argument. 

```
usage: pyphe-scan-timecourse [-h] [--nscans NSCANS] [--interval INTERVAL]
                             [--prefix PREFIX] [--postfix POSTFIX]
                             [--fixture {som3_edge,som3}]
                             [--resolution {150,300,600,900,1200}]
                             [--scanner {1,2,3}] [--mode {Gray,Color}]

optional arguments:
  -h, --help            show this help message and exit
  --nscans NSCANS       Number of time points to scan. This defaults to 100
                        and the script can be terminated by Ctr+C when done.
  --interval INTERVAL   Time in minutes between scans. Defaults to 20.
  --prefix PREFIX       Name prefix for output files. The default is the
                        current date YYYYMMDD.
  --postfix POSTFIX     Name postfix for output files. Defaults to empty
                        string.
  --fixture {som3_edge,som3,som3-color}
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


### Pyphe-growthcurves
This tool performs non-parametric analysis of growth curves. It was written specifically to analyse colony size timeseries data obtained with _pyphe-quantify_ _timeseries_.

It is important that your csv with the growth data is in the right format. The file must contain one growth curve per column. The first column must be the timepoints and there must be a header row with unique identifiers for each curve. For example data and expected outputs, check out the files included in this Documentation folder. Sensible default parameters are set for all options but, depending on your data, you may wish to customise these, so check out the help section below. 

```
usage: pyphe-growthcurves [-h] --input INPUT [--fitrange FITRANGE]
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
```


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

                            

### Pyphe-quantify

Pyphe quantify extracts colony parameters from images. In can operate in three distinct modes analysing colony sizes for each image individually (batch mode), analysing redness for each image individually (redness mode) or obtaining a growth curve from an image timeseries (timeseries mode).
The --grid parameter is required define the position of colonies on the plate. You can either use automatic grid detection, one of our preconfigured positions if you are using the pp3 fixture or define your own (see the manual below). Images can be in any format (e.g. jpg, tiff, png). Images should be cropped closely to the colonies (this is important for good thresholding and automatic grid detection), i.e. not contain parts of the plate edges or surroundings. In batch and timecourse mode, pyphe-quantify assumes that images were acquired using transmission scanning, where colonies appear darker then the surrounding agar. If this is not the case and you took images by reflective scanning or with a camera, use --negate False. In batch and timecourse mode, images are epxected to be grayscale. If they are not, they will be converted (by simply summing all channels) and a warning will be thrown. 


```
usage: pyphe-quantify [-h] --grid GRID [--pattern PATTERN] [--t T] [--d D]
                      [--s S] [--negate NEGATE] [--localThresh] [--convexhull]
                      [--reportAll] [--reportFileNames]
                      [--hardImageThreshold HARDIMAGETHRESHOLD]
                      [--hardSizeThreshold HARDSIZETHRESHOLD] [--qc QC]
                      [--calibrate CALIBRATE] [--timepoints TIMEPOINTS]
                      [--out OUT]
                      {batch,timecourse,redness}

Welcome to pyphe-quantify, part of the pyphe toolbox. Written by
stephan.kamrad@crick.ac.uk and maintained at https://github.com/Bahler-
Lab/pyphe

positional arguments:
  {batch,timecourse,redness}
                        Pyphe-quantify can be run in three different modes. In
                        batch mode, it quantifies colony sizes for all images
                        matching the pattern individually. A separate results
                        table and qc image is produced for each. Redness mode
                        is similar except that the redness of each colony is
                        quantified. In timecourse mode, all images matching
                        the pattern are analysed jointly. The final image
                        matching the pattern is used to create a mask of where
                        the colonies are and this mask is then applied to all
                        previous images in the timeseries. A single output
                        table, where the timepoints are the rows and each
                        individual colony is a row.

optional arguments:
  -h, --help            show this help message and exit
  --grid GRID           This option is required (all others have defaults set)
                        and specifies the grid in which the colonies are
                        arranged. You can use automatic grid detection using
                        one of the following parameters: auto_96, auto_384 or
                        auto_1536. Automatic grid correction will not work if
                        the colony grid is not aligned with the image borders.
                        Images should contain only agar and colonies, avaoid
                        having borders. It might fail or produce unexpected
                        results if there are whole rows/columns missing. In
                        those cases, it is easy to define hard-wired grid
                        positions. If you are using the fixture provided with
                        pyphe, we have preconfigured these for you. Depending
                        on the pinning density, use pp3_96, pp3_384 or
                        pp3_1536. Otherwise, the argument has to be in the
                        form of 6 integer numbers separated by "-": <number of
                        colony rows>-<number of colony columns>-<x-position of
                        the top left colony>-<y-position of the top left
                        colony>-<x-position of the bottom right
                        colony>-<y-position of the bottom right colony>.
                        Positions must be integers and are the distance in
                        number of pixels from the image origin in each
                        dimension (x is width dimension, y is height
                        dimension). The image origin is, in line with scikit-
                        image, in the top left corner. Pixel positions are
                        easily determined using programs such as Microsoft
                        Paint, by simply hovering the mouse over a position.
  --pattern PATTERN     Pattern describing files to analyse. This follows
                        standard unix convention and can be used to specify
                        subfolders in which to look for images
                        (<subfolder>/*.jpg) or the image format (*.tiff,
                        *.png, etc.). By default, all jpg images in the
                        working directory are analysed.
  --t T                 By default the intensity threshold to distinguish
                        colonies from the background is determined by the Otsu
                        method. The determined value will be multiplied by
                        this argument to give the final threshold. Useful for
                        easily fine-tuning colony detection.
  --d D                 The distance between two grid positions will be
                        divided by this number to compute the maximum distance
                        a putative colony can be away from its reference grid
                        position. Decreasing this number towards 2 makes
                        colony-to-grid-matching more permissive (might help
                        when some of your plates are at a slight angle or out
                        of position).
  --s S                 Detected putative colonies will be filtered by size
                        and small components (usually image noise) will be
                        excluded. The default threshold is the image
                        area*0.00005 and is therefore independent of scanning
                        resolution. This default is then multiplied by this
                        argument to give the final threshold. Useful for when
                        colonies have unusual sizes.
  --negate NEGATE       In images acquired by transmission scanning, the
                        colonies are darker than the background. Before
                        thresholding, the image needs to be inverted/negated.
                        Defaults to True in timecourse and batch mode, ignored
                        in redness mode.
  --localThresh         Use local thresholding in batch and timecourse mode.
                        This can help when image brightness is very uneven.
                        Ignored in redness mode where local thresholding is
                        always applied.
  --convexhull          Apply convex hull transformation to identified
                        colonies to fill holes. Useful when working with spots
                        rather than colonies. Ignored in redness mode.
                        WARNING: Using this options results in much longer
                        analysis times.
  --reportAll           Sometimes, two putative colonies are identified that
                        are within the distance threshold of a grid position.
                        By default, only the closest colony is reported. This
                        can be changed by setting this option (without
                        parameter). This option allows pyphe quantify to be
                        used even if colonies are not arrayed in a regular
                        grid (you still need to provide a grid parameter
                        though that spans the colonies you are interested i).
  --reportFileNames     Only for timecourse mode, otherwise ignored. Use
                        filenames as index for output table instead of
                        timepoints. Useful when the ordering of timepoints is
                        not the same as returned by the pattern. Setting this
                        option overrides the --timepoints argument.
  --hardImageThreshold HARDIMAGETHRESHOLD
                        Allows a hard (fixed) intensity threshold in the range
                        [0,1] to be used instead of Otsu thresholding. Images
                        intensities are re-scaled to [0,1] before
                        thresholding. Ignored in timecourse mode.
  --hardSizeThreshold HARDSIZETHRESHOLD
                        Allows a hard (fixed) size threshold [number of
                        pixels] to be used for filtering small colonies.
  --qc QC               Directory to save qc images in. Defaults to
                        "qc_images".
  --calibrate CALIBRATE
                        Transform background subtracted intensity values by
                        this function. Function needs to be a single term with
                        x as the variable and that is valid python code. E.g.
                        use "2*x**2+1" to square each pixels intensity,
                        multiply by two and add 1. Defaults to "x", i.e. use
                        of no calibration. Used only in timecourse mode.
  --timepoints TIMEPOINTS
                        In timecourse mode only. Path to a file that specifies
                        the timepoints of all images in the timeseries. This
                        is usually the timepoints.txt file created by pyphe-
                        scan-timecourse. It must contain one entry per line
                        and have the same number of lines as number of images.
  --out OUT             Directory to save output files in. Defaults to
                        "pyphe_quant".
```



### Pyphe-analyse
_Pyphe-analyse_ is a tool for spatial normalisation and data aggregation across many plates. It implements a grid normalisation based on the concept proposed by [Zackrisson et al. 2016](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5015956/) and row/column median normalisation. Please see our paper and the protocol in it to find out more. _Pyphe-analyse_ can be run from the command line, with options below, or using the graphical user interface by running _pyphe-analyse-gui_.


```
usage: pyphe-analyse.txt [-h] --edt EDT --format
                         {gitter,pyphe-redness,pyphe-growthcurves} [--out OUT]
                         [--load_layouts]
                         [--gridnorm {standard384,standard1536}]
                         [--extrapolate_corners] [--rcmedian] [--check CHECK]
                         [--qc_plots QC_PLOTS]

Welcome to pyphe-analyse, part of the pyphe toolbox. Written by
stephan.kamrad@crick.ac.uk and maintained at https://github.com/Bahler-
Lab/pyphe

optional arguments:
  -h, --help            show this help message and exit
  --edt EDT             Path to the Experimental Design Table (EDT) listing
                        all plates of the experiment. The table must be in csv
                        format, the first column must contain unique plate IDs
                        and there must be a column named 'Data_path' that
                        contains abolute or relative file paths to each
                        plate's data file. A 'Layout_path' column can be
                        included, see below. Any additional columns included
                        in this file will bestored in each plate's meta-data
                        and included in the final data output.
  --format {gitter,pyphe-redness,pyphe-growthcurves}
                        Type of inout data.
  --out OUT             Specifies the path where to save the output data
                        result. By default, the data report is saved in the
                        working directory as "pyphe-analyse_data_report.csv"
                        and will overwrite the file if it exists.
  --load_layouts        Set this option (without parameters) to load layouts
                        (requires Layout_path column in the EDT).
  --gridnorm {standard384,standard1536,1536with384grid}
                        Perform reference grid normalisation. Standard384
                        refers to plates which are in 384 (16x24) format with
                        the reference grid in 96 format in the top left
                        corner. Standard1536 refers to plates in 1536 format
                        (32x48( with two 96 reference grids in the top left
                        and bottom right corners. 1536with384grid refers to
                        plates in 1536 format with a 384 reference grid in
                        the top left position.
  --extrapolate_corners
                        If working in standard1536 format, set this option to
                        extrapolate the reference grid in the bottom left and
                        top right corner. A linear regression will be trained
                        across all top left and bottom right corners on plates
                        in the experiment to predict hypothetical grid colony
                        sizes in the other two corners.
  --rcmedian            Perform row/column median normalisation. If --gridnorm
                        will be performed first if both parameters are set.
  --check CHECK         Check colony sizes after normalisation for negative
                        and infinite colony sizes *(normalisation artefacts),
                        throw a warning and set to NA.
  --qc_plots QC_PLOTS   Specify a folder in which to save qc plots for each
                        plate.

```


### Pyphe-interpret

Pyphe-interpret reports summary statistics and tests for differential fitness using t-tests. It is flexible and can in theory be used with any dataset in tidy format.

```
usage: pyphe-interpret [-h] --ld LD [--out OUT] --grouping_column
                       GROUPING_COLUMN --axis_column AXIS_COLUMN
                       [--values_column VALUES_COLUMN] --control CONTROL
                       [--ld_encoding LD_ENCODING] [--circularity CIRCULARITY]
                       [--set_missing_na]

Welcome to pyphe-interpret, part of the pyphe toolbox. Written by
stephan.kamrad@crick.ac.uk and maintained at https://github.com/Bahler-
Lab/pyphe. Pyphe-interpret calculates summary statistics and p-values from the
data reports generated by pyphe-analyse. For this, specifiying your column
names correctly is crucial. Let us assume you have measured many strains in
many conditions. Now you would like to know for each strain in each condition
(for each condition-strain pair) if it is "significant". There are essentially
two ways of doing this, asking different biological questions. (1) Check for
each condition separately (--grouping_column <condition_column>) if there is a
significant difference in means between a mutant strain and a control strain
(--axis_column <strain_id_column>). Or (2) Check for each strain separately
(--grouping_column <strain_id_column>) if there is a significant difference in
the means of the strain in the assay condition versus the control condition
(--axis_column <condition_column>). The second option tests for condition-
specific growth effects (i.e. is does not return significant results if a
strain is always faster or always slower growing than the grid strain). In
both cases you need to specify the control against which to test using
--control and this has to be a value that appears in the axis column. You
should define the dependent variable of the t-test using --values_column. FDR
correction with the Benjamini-Hochberg method will be applied on each level
set of the grouping_column separately, ie for case (1) p-values will be
corrected across each strain separately, ie more conditions means more
stringent correction, and for case (2) p-values will be corrected for each
condition separately, ie more strains means mpre stringent correction.

optional arguments:
  -h, --help            show this help message and exit
  --ld LD               Path to the Data Report Table produced by pyphe-
                        analyse.
  --out OUT             Specifies the path where to save the output data
                        result. By default, a table with all replicates will
                        be saved as pyphe-interpret-report_reps.csv and the
                        statistic table will be saved as pyphe-interpret-
                        report_summaryStats.csv in the current working
                        directory. Existing files will be overwritten.
  --grouping_column GROUPING_COLUMN
                        Name of the column in the data report to use for
                        forming groups on which to perform independent sets of
                        t-tests.
  --axis_column AXIS_COLUMN
                        Name of the column in the data report to repeat
                        t-tests along within each group. Levels in this column
                        will be the explanatory/independent variable used for
                        t-tests.
  --values_column VALUES_COLUMN
                        Name of the column in the data report to use as
                        fitness values. This will be the dependent variable
                        for t-tests. Defaults to "Colony_size_corr_checked".
  --control CONTROL     Name of the control to compare against. This must be a
                        value found in the axis column.
  --ld_encoding LD_ENCODING
                        Encoding of the data report table to be passed to
                        pandas.read_csv().
  --circularity CIRCULARITY
                        Exclude colonies from the analysis with a circularity
                        below the one specified. A circularity of 1
                        corresponds to a perfect circle. We recommend a
                        threshold around 0.85.
  --set_missing_na      Set 0-sized colonies to NA. This is recommended if you
                        expect no missing colonies in your data, which means
                        these are probably due to pinning errors.
```

