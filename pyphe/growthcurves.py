import pandas as pd
import numpy as np
from scipy import stats

def analyse_growthcurve(gdata, fitrange, t0_fitrange, lag_method, lag_threshold, plots, plot_ylim, outdir, in_baseStr, plot_individual_data):
    '''
    Function for analysing a csv containing growthcurves.
    
    Arguments:
    gdata (pandas.DataFrame) -- DataFrame containing growth data. The index must be the timepoints and column IDs must be unique.
    fitrange (int) -- The number of timepoints over which to fit the linear regression.
    t0_fitrange (int) -- The number of timepoints to use to estimate the initial biomass which is the mean over those timepoints.
    lag_method (str) -- Method to use to determine lag phase. Currently supported: rel_threshold and abs_threshold.
    lag_threshold (float) -- The threshold value to use. The lag phase will be determined as the time it takes for the biomass to exceed this value (for abs_threshold) or t0*threshold for rel_threshold.
    plots (bool) --  Produce pdf document of growth curve plots.
    plot_ylim (float) -- Set plot upper limits of y-axis.
    '''
    
    t = gdata.index.tolist()
    
    def find_lag(x):
        '''Find the lag phase for a single growthcurve.
        Required arguments:
        x (array-like) -- 1D array-like containing the population/colony sizes
        t (array-like) -- 1D array-like containing the timepoints, must have same dimensions as x
        t0 (float) -- Inoculation biomass
        method (str) -- method to use to determine lag phase. Currently supported: rel_threshold and abs_threshold.
        thresh (float) -- The threshold value to use. The lag phase will be determined as the time it takes for the biomass to exceed this value (for abs_threshold) or t0*threshold for rel_threshold.
        Returns:
        lag (float) -- lag time
        '''
        t0 = np.array(x)[0:t0_fitrange].mean()

        if lag_method=='rel':
            for i, val in enumerate(x):
                if val > lag_threshold*t0:
                    return pd.Series([t0, t[i]], index=['initial biomass', 'lag'])

        elif lag_method=='abs':
            for i, val in enumerate(x):
                if val > lag_threshold:
                    return pd.Series([t0, t[i]], index=['initial biomass', 'lag'])              

        else:
            raise ValueError('Unknown lag method %s' %method)

    #Analyse lags
    lags = gdata.apply(find_lag)
    
    def find_max_slope(x, find_min_instead=False):
        '''Find max_slope, t_max, intercept and r2 for a single growthcurve. The regression is aware of the timepoints so this will work with unevenly samples growthcurves.
        Required arguments:
        x (array-like) -- 1D array-like containing the population/colony sizes
        t (array-like) -- 1D array-like containing the timepoints, must have same dimensions as x
        reg_fitrange (int) -- The number of timepoints over which to fit the linear regression
        Returns:
        {
        max_slope -- The slope of the regression
        t_max -- The mid-point of the fitrange of the regression
        intercept -- The y-inyercept of the regression
        r2 -- The R^2 value of the regression
        }
        '''
        regression_results = []
        x = x.tolist()
        
        for i in range(len(x)-fitrange):
            slope, intercept, r_value, p_value, std_err = stats.linregress(t[i:i+fitrange], x[i:i+fitrange])
            regression_results.append({'t_max':np.mean(t[i:i+fitrange]), 'max_slope':slope, 'r2':r_value**2, 'y-intercept':intercept})
            
        if find_min_instead:
            slope_result = pd.Series(min(regression_results, key=lambda x: x['max_slope']))
        else:
            slope_result = pd.Series(max(regression_results, key=lambda x: x['max_slope']))
            
        slope_result['x-intercept'] = -slope_result['y-intercept']/slope_result['max_slope']
        return slope_result
        
    #Get max slopes    
    slopes = gdata.apply(find_max_slope)
    
    
    #Get area under the curve (AUC)
    aucs = gdata.sum()
    aucs.name = 'sum of values (AUC)'
    aucs = pd.DataFrame(aucs).transpose()

    #Get maximum value
    maxgrowth = gdata.max()
    maxgrowth.name = 'maximum'
    maxgrowth = pd.DataFrame(maxgrowth).transpose()

    
    ###Perform some simple QC
    #flag cases where min slope is < - 7.5% of max slope in entire input data
    min_slopes = gdata.apply(find_max_slope, find_min_instead=True)
    min_slopes = min_slopes.loc['max_slope']   
    neg_slope_warning = min_slopes < -(slopes.loc['max_slope'].max() * 0.075)
    neg_slope_warning.name = 'warning_negative_slope'
    if neg_slope_warning.sum() > 0:
        print('The following growth curves appear to have significant negative slopes. This is also flagged in the output file:  %s)'%','.join(neg_slope_warning[neg_slope_warning].index))
    neg_slope_warning = pd.DataFrame(neg_slope_warning).transpose()
    neg_slope_warning.loc['warning_negative_slope'] = neg_slope_warning.loc['warning_negative_slope'].map({True:'WARNING', False:''})

    #flag cases where the tangent fit is poor (R^2<0.95)
    r2_warning = slopes.loc['r2'] < 0.95
    r2_warning.name = 'warning_bad_fit'
    if r2_warning.sum() > 0:
        print('For the following growth curves the R^2 of the fitted tangent is < 0.95. This is also flagged in the output file:  %s)'%','.join(r2_warning[r2_warning].index))
    r2_warning = pd.DataFrame(r2_warning).transpose()
    r2_warning.loc['warning_bad_fit'] = r2_warning.loc['warning_bad_fit'].map({True:'WARNING', False:''})

    ###Plotting
    if plots:
        from matplotlib import pyplot as plt
        import seaborn as sns
        sns.set(style='ticks', font_scale=0.75)
        plt.rcParams['svg.fonttype'] = 'none'
        from matplotlib.backends.backend_pdf import PdfPages
        
        with PdfPages(outdir + '/' + in_baseStr + '_curves.pdf') as pdf:
            layout=(8,4)
            raw_kwargs={'color':'C0', 'linewidth':1}
            smoothed_kwargs={'color':'r', 'linewidth':0.5}
            regr_kwargs={'color':'k', 'linewidth':0.5, 'linestyle':'--'}
            
            toPlot = list(gdata)
            while toPlot:
                fig, ax = plt.subplots(layout[0], layout[1], figsize=(8.27,11.69))
                for a in ax.flat:
                    
                    a.plot(t, gdata[toPlot[0]], **raw_kwargs, zorder=1)
                    if plot_individual_data:
                        a.scatter(t, gdata[toPlot[0]], color='k', marker='.', s=1, zorder=2)
                    #Get ylim
                    ylim = a.get_ylim()

                    tmax = slopes.loc['t_max', toPlot[0]]
                    maxslope = slopes.loc['max_slope', toPlot[0]] 
                    intercept = slopes.loc['y-intercept', toPlot[0]]
                    if not pd.isnull([tmax, maxslope, intercept]).any():
                        x = np.array(t)
                        y = x*maxslope + intercept
                        a.plot(x, y, **regr_kwargs)

                    t0 = lags.loc['initial biomass', toPlot[0]]
                    lag = lags.loc['lag', toPlot[0]]
                    if not pd.isnull([t0, lag]).any():
                        a.axhline(t0, color='k', xmin=0, xmax=lag, linewidth=0.75, alpha=0.6)
                        a.axvline(lag, color='k', linewidth=0.75, alpha=0.6)
                        if 'lag_method' == 'abs':
                            a.axhline(lag_threshold, color='k', xmin=0, xmax=lag, linewidth=0.75, alpha=0.6)
                        else:
                            a.axhline(lag_threshold * t0, color='k', xmin=0, xmax=lag, linewidth=0.75, alpha=0.6)
                        
                    a.set_title(str(toPlot[0]))
                    if plot_ylim:
                        a.set_ylim([0,plot_ylim])
                    else: 
                        a.set_ylim(ylim)
                    toPlot.pop(0)
                    if not toPlot:
                        break
                        
                plt.tight_layout()                    
                pdf.savefig()
                plt.close()
                plt.clf()

    return pd.concat([lags, slopes, aucs, maxgrowth, neg_slope_warning, r2_warning], axis=0)
