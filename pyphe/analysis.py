import pandas as pd
from warnings import warn
import os
from scipy import interpolate
import numpy as np

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt
import seaborn as sns
sns.set_style('white')

class Experiment():
    '''
A pyphe Experiment object facilitates working with a large number of plates/images at the same time. The constructor takes a single argument which is a pandas DataFrame containing some basic information about your experiment. This table should have one line per plate image and should normally contain at least two columns (although column names are not strictly enforced): Assay_plate (which specifies the layout of the plate which we will later read in from a different file) and Image_path (the relative or absolute path to the image file). Normally this file will have additional columns which you can use to keep track of any additional information about the plates, e.g. batch numbers, dates, condition. This information will be retained and propagated into the final output file.  
It is highly advisable to use a meaningful and unique index for this DataFrame which we can later be used to easily identify individual plots. Alternatively, the pandas default of using interger ranges as index can be used.

Required arguments for creating an Experiment object:
exp_data (DataFrame) - A DataFrame holding experiment meta-data

An Experiment object has the following attributes:
exp_data - A DataFrame holding experiment meta-data
plates - A pandas Series of Plate objects, the index is identical to exp_data
    '''

    def __init__(self, exp_data):
        assert not exp_data.index.duplicated().any(), 'Plate IDs must be unique'
        self.exp_data = exp_data

        self.plates = pd.Series({i : Plate(plateid=i, meta_data=r) for i, r in self.exp_data.iterrows()})

    def update_meta_data(self):
        '''Update plate meta_data when exp_data has been modified. This is not ideal and could pose a risk of information being overwritten if the user manually edits plate meta-data.'''
        for i,p in self.plates.iteritems():
            p.meta_data = self.exp_data.loc[i]

    def generate_long_data(self):
        '''Make a summary table with all data from all Plates for stats and plotting.
        Returns:
        summary_long (pandas DataFrame)
        '''

        longs = []
        for i,p in self.plates.iteritems():
            p_long = p.make_long_data()

            for m in self.exp_data:
                p_long[m] = [self.exp_data.loc[i,m] for l in p_long.index]

            p_long['Plate'] = i
            longs.append(p_long)

        summary_long = pd.concat(longs)
        summary_long.index = range(len(summary_long.index))

        return summary_long

    def batch_gitter(self, plate_format, grid_image_folder='grid_images', dat_file_folder='dat_files', inverse='TRUE', remove_noise='TRUE', autorotate='FALSE', gitter_script_name='gitter_script.R'):
        '''
        Wrapper script for gitter. The Experiment object's exp_data must have an Image_path column for this to work.
        This will write a gitter script into the current directory, which you can execute with Rscr

        Required arguments:
        plate_format (int) - Plate format in gitter convention 96/384/1536

        Keyword arguments:
        grid_image_folder (str) - Path of the folder to save the grid images in. Defaults to grid_images
        dat_file_folder (str) - Path of the folder to save the dat files in. Defaults to dat_files
        gitter_script_name (str) - Path of the gitter script to be outputted. Defaults to gitter_script.R
        inverse (str) - Has to be TRUE/FALSE. Invert image before analysis (reuqired for transmission scanning). See gitter documentation.
        remove_noise (str) - Has to be TRUE/FALSE. Reduce image noise before analysis. See gitter documentation.

        Returns:
        None
        '''
        check_mkdir(grid_image_folder)
        check_mkdir(dat_file_folder)

        with open(gitter_script_name, 'w') as gs:
            gs.write('library("gitter")\n')
            for fpath in self.exp_data['Image_path']:
                gitter_cmd = 'gitter("%s", plate.format=%i, inverse="%s", remove.noise="%s", grid.save="%s", dat.save="%s", autorotate="%s")'%(fpath, plate_format, inverse, remove_noise, grid_image_folder, dat_file_folder, autorotate)
                gs.write(gitter_cmd+'\n')

        self.exp_data['Data_path'] = dat_file_folder + '/' + self.exp_data['Image_path'].map(lambda x: x.split('/')[-1]) + '.dat'
        self.exp_data['Gitter_grid_path'] = grid_image_folder + '/gridded_' + self.exp_data['Image_path'].map(lambda x: x.split('/')[-1])

        self.update_meta_data()

        print('Gitter script created, please run the following command: Rscript %s'%gitter_script_name)


class Plate():
    '''This object holds all data for a single plate. Two empty, all-purpose pandas series are initilased to hold the bulk of the data associated with the Plate object: Plate.meta_data can be used to store meta data of all sorts and these will be included in the output report. Plate.pos_data is used to store pandas dataframes that have the same shape as the gridformat and are used to store actual growth data and analysis results.
    Keyword arguments:
    meta_data (Series) - A pandas series containing meta-information about the plate.
    '''
    
    def __init__(self, meta_data=None, plateid=None):
        self.plateid = plateid
        self.meta_data = meta_data
        self.pos_data = pd.Series()

    def read_gitter_single_image(self):
        '''Read gitter data from file. Adds two new DataFrames to the Plate's pos_data Series, for colony size and one for circularity. The path of the dat file is taken from the PLate's meta_data.'''

        dat = pd.read_csv(self.meta_data['Data_path'], comment='#', header=None, names=['row', 'col', 'size', 'circularity', 'flags'], sep='\t')
        
        size = dat.pivot(index='row', columns='col', values='size')
        size.index.name = None
        size.index = size.index.map(str)
        size.columns.name = None
        size.columns = size.columns.map(str)
        self.pos_data['Colony_size'] = size
        
        circularity = dat.pivot(index='row', columns='col', values='circularity')
        circularity.index.name = None
        circularity.index = circularity.index.map(str)
        circularity.columns.name = None
        circularity.columns = circularity.columns.map(str)
        self.pos_data['Colony_circularity'] = circularity
        
    def read_pypheredness_single_image(self):
        '''Read  column from pyphe-quantify redness output file'''
        
        dat = pd.read_csv(self.meta_data['Data_path'])

        size = dat.pivot(index='row', columns='column', values='mean_intensity')
        size.index.name = None
        size.index = size.index.map(str)
        size.columns.name = None
        size.columns = size.columns.map(str)
        self.pos_data['Colony_size'] = size

        circularity = dat.pivot(index='row', columns='column', values='circularity')
        circularity.index.name = None
        circularity.index = circularity.index.map(str)
        circularity.columns.name = None
        circularity.columns = circularity.columns.map(str)
        self.pos_data['Colony_circularity'] = circularity
    
    def read_pyphebatch_single_image(self):
        '''Read  column from pyphe-quantify redness output file'''
        
        dat = pd.read_csv(self.meta_data['Data_path'])

        size = dat.pivot(index='row', columns='column', values='area')
        size.index.name = None
        size.index = size.index.map(str)
        size.columns.name = None
        size.columns = size.columns.map(str)        
        self.pos_data['Colony_size'] = size
             
        circularity = dat.pivot(index='row', columns='column', values='circularity')
        circularity.index.name = None
        circularity.index = circularity.index.map(str)
        circularity.columns.name = None
        circularity.columns = circularity.columns.map(str)
        self.pos_data['Colony_circularity'] = circularity
        
    def read_pgc_single_image(self):
        '''Read pyphe-growthcurves output file'''
        
        dat = pd.read_csv(self.meta_data['Data_path'], index_col=0).transpose()
        
        dat['Row'] = dat.index.map(lambda x: int(x.split('-')[0]))
        dat['Column'] = dat.index.map(lambda x: int(x.split('-')[1]))

        resvars = ['initial biomass', 'lag', 'r2', 't_max', 'y-intercept', 'x-intercept', 'max_slope', 'sum of values (AUC)', 'maximum']
        resvars = [s for s in resvars if s in dat.columns]
        
        for c in resvars:
            tf = dat.pivot(index='Row', columns='Column', values=c)
            tf = tf.sort_index().sort_index(axis=1)
            tf.index = tf.index.map(str)
            tf.columns = tf.columns.map(str)
            
            if c == 'max_slope':
                self.pos_data['Colony_size'] = tf.astype(float)
            else:
                self.pos_data[c] = tf.astype(float)
                
        
    def read_layout_single_plate(self, kwargs={'header':None}):
        '''Read the layout of a single file in wide format. This is essentially a wrapper for pandas' read_csv() function which will store returned DataFrame in the pos_data Series of the plate instance. The path of the layout file needs to be provided in the exp_data file in a column named Layout_path. The layout file should not have any header or index information but this can be overriden by supplying keyword arguments as a dictionary to the kwargs argument. Any keyword arguments provided will be passed to pandas' read_csv() function.'''
        
        imported = pd.read_csv(self.meta_data['Layout_path'], **kwargs)
        imported.index = map(str, range(1, len(imported.index)+1))
        imported.columns = map(str, range(1, len(imported.columns)+1))

        self.pos_data['Strain'] = imported
        
    def rcmedian_normalisation(self, inkey='Colony_size', outkey='Colony_size_corr'):
        '''This function implements row/column median normalisation with smoothing of row/column medians across plates.

        Required aguments:
        inkey (str) -- The key in pos_data which to use as input
        outkey (str) -- The key in pos_data under which to store the result
        Returns:
        None
        '''

        col_medians = self.pos_data[inkey].median(axis=0)
        row_medians = self.pos_data[inkey].median(axis=1)

        normed = self.pos_data[inkey].div(row_medians, axis='index')
        normed = normed.div(col_medians, axis='columns')
        normed = normed/normed.stack().median()
        self.pos_data[outkey] = normed

    def grid_normalisation(self, gridpos_list, inkey='Colony_size', outkey='Colony_size_corr', set_missing_nan=True, remove_grid_outliers=False, k=3, extrapolate_corners=False, horizontal_neighbour_coeff=None, vertical_neighbour_coeff=None,  intercept_coeff=None):
        
        '''Apply reference-grid normalisation to quantitative colony data stored in pos_data. First, the data of the grid colonies is extracted from pos_data[inkey], based on the provided list of control positions. There is an option to filter out extreme grid outliers (e.g. due to pinning errors) using a z-score cut-off based on the overall distribution of grid colony values. In this implementation of the grid normalisation it is only possible to extrapolate the lower left and upper right corners of 1536 plates. The grid must be placed as two 96 grids, in the upper left and lower right corner. Please do not use this option if those conditions are not met. Finally, the grid is interpolated using 2d cubic interpolation as implemented in scipy's interpolate.griddata() function. The corrected values are computed by dividing the acutal colony value by the expected (interpolated) value and the result is stored as a new DataFrame in the plate's pos_data.

        Required arguments:

        gridpos_list (list) -- list of two-length tuples, containing row and column positions as integers)
        remove_grid_outliers (bool) -- Should extreme outliers in reference grid be removed? This leads to loss of data if positions are on edge of grid.  

        Keyword arguments:
        set_missing_nan (bool) - Set colonies near grid positions which are 0 or nan (usually indicating pinning errors) to nan (Recommended).
        inkey (str) -- The key in pos_data which to use as input. Defaults to Colony_size.
        outkey (str) -- The key in pos_data under which to store the result. Defaults to Colony_size_corr.
        remove_outliers (bool) -- Reemove grid outliers with a z-score of more than k, if they are not on the edge.
        k (float) -- Grid positions with a Z-score of greater than k will be removed from grid. Only required when remove_grid_outliers is True, otherwise ignored.

        Returns:
        None
        '''
            
        grid = pd.DataFrame(index=self.pos_data[inkey].index, columns=self.pos_data[inkey].columns, dtype=float)
        for row, col in gridpos_list:
            grid.loc[str(row), str(col)] = self.pos_data[inkey].loc[str(row), str(col)]

        #Look for areas where the grid is nan or 0
        na_mask = pd.DataFrame(False, index=self.pos_data[inkey].index, columns=self.pos_data[inkey].columns, dtype=bool)
        nan_zero_count = 0
        for row, col in gridpos_list:
            if (pd.isnull(grid.loc[str(row), str(col)])) or (grid.loc[str(row), str(col)] == 0.0):
                nan_zero_count += 1
                
                #Set this to NA in the grid itself
                grid.loc[str(row), str(col)] = np.nan

                #Set the neighbours and the field itself in the NA_mask to NAN
                na_mask.loc[str(row), str(col)] = True
                na_mask.loc[str(row), str(col+1)] = True
                na_mask.loc[str(row), str(col-1)] = True
                na_mask.loc[str(row+1), str(col)] = True
                na_mask.loc[str(row-1), str(col)] = True
                na_mask.loc[str(row+1), str(col+1)] = True
                na_mask.loc[str(row-1), str(col+1)] = True
                na_mask.loc[str(row+1), str(col-1)] = True
                na_mask.loc[str(row-1), str(col-1)] = True
                
        #Need to remove any new columns/rows added on the edge and need to recast type to bool
        na_mask = na_mask.loc[self.pos_data[inkey].index, self.pos_data[inkey].columns].astype(bool)
                
        self.pos_data['Near_missing_grid'] = pd.DataFrame(na_mask, index=self.pos_data[inkey].index, columns=self.pos_data[inkey].columns, dtype=bool)

        if nan_zero_count > 0:
            if set_missing_nan:
                #Check for grid colonies that didn't grow and report
                print('Plate %s: %i grid colonies have size 0, probably due to pinning errors. These and neighbouring colonies will be set to nan.'%(self.plateid, nan_zero_count))
            else:
                #Check for grid colonies that didn't grow and throw a warning
                print('Plate %s: %i grid colonies have size 0, probably due to pinning errors. I will ignore this for now and interpolate grid values based on surrounding grid colonies. However, it is recommended that you set these to nan. Affected colonies are marked in the Near_missing_grid column.'%(self.plateid, nan_zero_count))

        if remove_grid_outliers:
            #Calculate z-scores
            sigma = grid.unstack().std()  # std dev of all ref colonies
            mu = grid.unstack().mean()    # mean  of all ref colonies

            z_scores = grid - mu
            z_scores = z_scores / sigma
            z_score_mask = z_scores.abs()>k

            #Whatever the z-score, dont remove grid positions on edges of plate, this leads to missing data and these are more variable in general
            z_score_mask.iloc[:,0] = False
            z_score_mask.iloc[0,:] = False
            z_score_mask.iloc[:,-1] = False
            z_score_mask.iloc[-1,:] = False

            grid[z_score_mask] = np.nan
            print('Plate %s: Removed %i outlier grid colonies'%(self.plateid, z_score_mask.unstack().sum()))

        if extrapolate_corners:
            #warn('In this implementation of the grid normalisation it is only possible to extrapolate the lower left and upper right corners of 1536 plates. The grid must be placed as two 96 grids, in the upper left and lower right corner. Please do not use this option if those conditions are not met.')
            grid.loc['32','1'] = intercept_coeff + horizontal_neighbour_coeff*grid.loc['32','4'] + vertical_neighbour_coeff*grid.loc['29','1']
            grid.loc['1','48'] = intercept_coeff + horizontal_neighbour_coeff*grid.loc['1','45'] + vertical_neighbour_coeff*grid.loc['4','48']


        self.pos_data['Grid'] = grid


        #Calculate reference surface
        #Get new list of grid positions after extrapolation and noise filtering
        grid_us = grid.unstack().dropna().reset_index()
        grid_us.columns = ['col', 'row', 'val']
        gridpos_list_new = grid_us[['row', 'col']].values
        values = grid_us['val'].values

        #Points to interpolate
        xi = grid.unstack()
        xi = xi[pd.isnull(xi)]
        xi = xi.reset_index()
        xi.columns = ['col', 'row', 'val']
        xi = xi[['row', 'col']].values

        #interpolate
        interpolated = interpolate.griddata(gridpos_list_new, values, xi, method='cubic')

        ref_surface = pd.DataFrame(index=self.pos_data[inkey].index, columns=self.pos_data[inkey].columns, dtype=float)
        for i,p in enumerate(gridpos_list_new):
            ref_surface.loc[str(p[0]), str(p[1])] = grid.loc[str(p[0]), str(p[1])]
        for i,p in enumerate(xi):
            ref_surface.loc[str(p[0]), str(p[1])] = interpolated[i]
        self.pos_data['Reference_surface'] = ref_surface

        #Get ratio of max slope to wild type
        corr_data = self.pos_data[inkey]/ref_surface
        if set_missing_nan:
            corr_data[na_mask] = np.nan
        self.pos_data[outkey] = corr_data
        
    def plot_pos_data(self, pdf_path=None, toPlot=None):
        '''Plot DataFrames containing numerical values as heatmaps using seaborn and matplotlib.
        Keyword arguments:
        pdf_path -- This option is highly recommended when you are dealing with large batches of Plates. It saves figures to pdf and then closes them so that they do not build up in memory. Please provide the name of a folder to save pdfs in, the filename is identical to the plateid.
        toPlot (list) -- List of data to plot. Must be keys of Plate.pos_data. If not set, all DataFrames in pos_data which contain numeric values will be plotted.

        Returns:
        None
        '''
        
        if not toPlot:
            toPlot = []
            for i, fr in self.pos_data.iteritems():
                try:
                    fr.astype(float)#Select only DataFrames which can be cast to numeric.
                    toPlot.append(i)
                except Exception:
                    pass

        if pdf_path:
            pdf = PdfPages(os.path.join(pdf_path, str(self.plateid))+'.pdf')

        for key in toPlot:
            fig, ax = plt.subplots()
            sns.heatmap(data=self.pos_data[key], ax=ax)
            ax.set_title(key)
            if pdf:
                pdf.savefig()
                fig.clf()
                plt.close(fig)
                
        if pdf_path:
            pdf.close()
            
    def check_values(self, inkey='Colony_size_corr', outkey='Colony_size_corr_checked', negative_action=0, inf_action=10):
        ''' This function checks for invalid values in plate pos data. Normalisation procedures can produce invalid values 
        as side effect, such as negative or infinite fitness values. This function detects those and deals with them in 
        a custamisable way.

        Keyworkd arguments:
        inkey (str) -- The data to use (must be a key in exp.plates.pos_data)
        negative_action (float) -- Value to assign to negative fitness. Defaults to 0. np.nan is allowed too. Set to None if no action required.
        inf_action (float) -- Value to assign to inf values. Defaults to 10. np.nan is allowed too. Set to None if no action required.

        Returns:
        None (exp.plates.pos_data is modified in place)
        '''

        data = self.pos_data[inkey]
        ##In some rare cases the input DataFrame can be empty. In that case, just set to an empty DataFrame
        if data.empty:
            self.pos_data[outkey] = pd.DataFrame([[]])
            return None
        data = data.unstack()

        #Ignore na
        data = data.dropna()

        #Check for inf
        isneginf = data[np.isneginf(data.values)]
        if len(isneginf.index) != 0:
            print('Plate %s - The following positions are minus infinity: %s'%(self.plateid, str(dict(isneginf))))
        isposinf = data[np.isposinf(data.values)]
        if len(isposinf.index) != 0:
            print('Plate %s - The following positions are plus infinity: %s'%(self.plateid, str(dict(isposinf))))

        #Check for negative
        neg = data[~np.isinf(data.values)]
        neg = neg[neg<0]
        if len(neg.index) != 0:
            print('Plate %s - The following positions are negative: %s'%(self.plateid, str(dict(neg))))

        #Actions
        if inf_action is not None:
            inf_action = float(inf_action)            
            if pd.isnull(inf_action):
                self.pos_data[inkey][np.isinf(self.pos_data[inkey])] = inf_action
            else:
                self.pos_data[inkey][np.isneginf(self.pos_data[inkey])] = -inf_action
                self.pos_data[inkey][np.isposinf(self.pos_data[inkey])] = inf_action

        if negative_action is not None:
            negative_action = float(negative_action)
            self.pos_data[outkey] = self.pos_data[inkey].copy()
            self.pos_data[outkey][self.pos_data[outkey].replace(-np.inf, 1).replace(np.inf, 1).replace(np.nan, 1)<0] = negative_action



    def make_long_data(self):
        '''Generate a summary table of all Data stored in this Plate object.
        Returns:
        long_data (pandas DataFrame)
        '''
        unstacked = []
        for k, frame in self.pos_data.iteritems():
            if frame.empty:
                continue
            l_unstacked = frame.copy()
            l_unstacked.columns.name = 'Column'
            l_unstacked.index.name = 'Row'
            l_unstacked = l_unstacked.unstack()
            l_unstacked.name = k
            unstacked.append(l_unstacked)
        if len(unstacked) == 0:
            warn('No data associated with Plate %s. Please check input data'%self.plateid)
            return pd.DataFrame([[]])
        else:
            long_data = pd.concat(unstacked, axis=1)
            long_data = long_data.reset_index()

        return long_data

def check_mkdir(dirPath):
    '''
Create a directory if it does not exist already.

Required arguments:
dirPath (str) - path of the directory to create.
'''

    if os.path.exists(dirPath):
        warn('Directory exist, not doing anything.')
    else:
        os.mkdir(dirPath)



def check_exp_data(exp_data, layouts=False):
    print('Checking exp_data table')
    
    print('Checking if plate IDs (first column) are unique')
    assert not exp_data.index.duplicated().any(), 'Error, Plate IDs are not unique'
    print('....OK')
    
    print('Checking for mandatory columns')
    assert 'Data_path' in exp_data.columns, 'Error, table must have Data_path column'
    if layouts:
        assert 'Layout_path' in exp_data.columns, 'Error, table must have Layout_path column'
    print('....OK')
    
    print('Checking if data files are unique')
    assert not exp_data['Data_path'].duplicated().any(), 'Error, data paths are not unique (plates with the same ID have been assigned the same data file).'
    print('....OK')
    
    print('Checking all data files exist')
    for ip in exp_data['Data_path']:
        if not os.path.isfile(ip):
            raise IOError('Data file does not exist: %s'%ip)
    print('...OK')
    
    if layouts:
        print('Checking all layout files exist')
        for ip in exp_data['Layout_path']:
            if not os.path.isfile(ip):
                raise IOError('Layout file does not exist: %s'%ip)
        print('...OK')

def pyphe_cmd(wdirectory=None, grid_norm=None, out_ld=None, qcplots=None, check_setNA=None, qcplot_dir=None, exp_data_path=None, extrapolate_corners=None, grid_pos=None, rcmedian=None, input_type=None, load_layouts=None):
    '''
    This function was written to be called from the GUI script provided. But it can also be used to run the entire standard pipeline in one place.
    '''
    
    print('###Step 1: Load data###')

    #Set working directory
    if wdirectory:
        os.chdir(wdirectory)
        print('Working directory changed to: %s'%wdirectory)
    #Import exp_data
    exp_data = pd.read_csv(exp_data_path, index_col=0)
    check_exp_data(exp_data, layouts=load_layouts)
    print('Table checks completed')
    
    exp = Experiment(exp_data)
    print('Created pyphe experiment object')
    
    #Load the data
    if input_type == 'gitter':
        exp.plates.map(Plate.read_gitter_single_image)

    elif input_type == 'pyphe-quantify-redness':
        exp.plates.map(Plate.read_pypheredness_single_image)
        
    elif input_type == 'pyphe-growthcurves':
        exp.plates.map(Plate.read_pgc_single_image)
        
    elif input_type == 'pyphe-quantify-batch':
                exp.plates.map(Plate.read_pyphebatch_single_image)
    
    else:
        raise ValueError('Unrecignised input_type')
    print('Plate data loaded sucessfully')
    
    
    #Load the layouts
    if load_layouts:
        exp.plates.map(Plate.read_layout_single_plate)
        print('Layouts loaded sucessfully')
    
    #Perform norms
    if grid_norm:
        if input_type == 'pyphe-quantify-redness':
            raise ValueError('Grid normalisation does not make sense for redness input')
            
        print('Performing grid norm')

        if (grid_pos == 'Standard 384 (top left)') or (grid_pos == 'standard384'):
            gridpos_list = [(row, col) for row in range(1, 16, 2) for col in range(1, 24, 2)]
        elif (grid_pos == 'Standard 1536 (top left and bottom right)') or (grid_pos == 'standard1536'):
            gridpos_list = [(row, col) for row in range(1, 32, 4) for col in range(1, 48, 4)]
            gridpos_list += [(row, col) for row in range(4, 33, 4) for col in range(4, 49, 4)]
        elif grid_pos == '1536with384grid':
            gridpos_list = [(row, col) for row in range(1, 32, 2) for col in range(1, 48, 2)]
        else:
            raise ValueError('grid_pos must be one of ["Standard 384 (top left)", "standard384", "Standard 1536 (top left and bottom right)", "standard1536", "1536with384grid"]')


        if extrapolate_corners:
            from sklearn.linear_model import LinearRegression
            #Make a table of  features
            vals = pd.DataFrame(columns=['thisCorner', 'horizontalNeighbour', 'verticalNeighbour'])
            for i,p in exp.plates.iteritems():
                vals.loc[i+'_topLeft'] = [p.pos_data['Colony_size'].loc['1','1'], p.pos_data['Colony_size'].loc['1','5'], p.pos_data['Colony_size'].loc['5','1']]
                vals.loc[i+'_bottomRight'] = [p.pos_data['Colony_size'].loc['32','48'], p.pos_data['Colony_size'].loc['32','44'], p.pos_data['Colony_size'].loc['28','48']]
            mlm = LinearRegression()
            mlm.fit(vals.iloc[:,1:], vals.iloc[:,0])
            print('Extrapolating missing corners based on the following regression: ')
            print('    horizontal_neighbour_coeff: ' +  str(mlm.coef_[0]))
            print('    vertical_neighbour_coeff: ' +  str(mlm.coef_[1]))
            print('    intercept_coeff: ' +  str(mlm.intercept_))
            print('    accuracy: ' +str(mlm.score(vals.iloc[:,1:], vals.iloc[:,0])))
                        
            exp.plates.map(lambda x: x.grid_normalisation(gridpos_list, 
                                                  extrapolate_corners=True, horizontal_neighbour_coeff=mlm.coef_[0], 
                                                  vertical_neighbour_coeff=mlm.coef_[1],  intercept_coeff=mlm.intercept_))
                              
        else:
            exp.plates.map(lambda x: x.grid_normalisation(gridpos_list) )
            
        
    if rcmedian:
        print('Performing row/column median normalisation')
        if grid_norm:
            ikey = 'Colony_size_corr'
            okey = 'Colony_size_corr'
        else:
            ikey = 'Colony_size'
            okey = 'Colony_size_corr'

        exp.plates.map(lambda x: x.rcmedian_normalisation(inkey=ikey, outkey=okey))
    
    #Perform checks and qc
    if check_setNA:
        print('Checking for infinite and negative fitness values')
        if (not grid_norm) and (not rcmedian):
            exp.plates.map(lambda x: x.check_values(inkey='Colony_size', outkey='Colony_size_checked', negative_action=np.nan, inf_action=np.nan))
        else:
            exp.plates.map(lambda x: x.check_values(inkey='Colony_size_corr', outkey='Colony_size_corr_checked', negative_action=np.nan, inf_action=np.nan))
        
    if qcplots:
        print('Making qc plots')
        exp.plates.map(lambda x: x.plot_pos_data(pdf_path=qcplot_dir))
        
    #Export
    print('Exporting data')
    ld = exp.generate_long_data()
    ld.to_csv(out_ld)
    print('Done')
    
    
