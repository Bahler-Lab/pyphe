import pandas as pd
from scipy.stats import ttest_ind
import numpy as np
from statsmodels.stats.multitest import multipletests as multit
from warnings import warn

def count_reps(inseries):
    inseries = inseries.tolist()
    counts = {k:0 for k in list(set(inseries))}
    out = [878 for i in range(len(inseries))]
    for ind, ite in enumerate(inseries):
        out[ind] = counts[ite]
        counts[ite] += 1
    return out
    

from scipy.stats import mstats_basic

def interpret(ld, condition_column, strain_column, values_column, control_condition, out_prefix, circularity=None, set_missing_na=False):
    '''
    Interpret experimental data report produced by pyphe-analyse. 
    '''
    
    ###Check if essential columns exist
    print('Checking input table')
    print('Checking if axis_column exists')
    if condition_column not in list(ld):
        raise NameError('Axis_column not found in table.')
    print('....OK')

    print('Checking if grouping_column exists')
    if strain_column not in list(ld):
        raise NameError('grouping_column not found in table.')
    print('....OK')

    print('Checking if values_column exists')
    if values_column not in list(ld):
        raise NameError('values_column not found in table.')
    print('....OK')

    print('Checking if control exists in axis_column')
    if control_condition not in ld[condition_column].unique():
        raise NameError('control not found in axis_column.')
    print('....OK')

    if circularity:
        print('Circularity filter is set. Checking if Colony_circularity column exists')
        if 'Colony_circularity' not in list(ld):
            raise NameError('Input data has no column named Colony_circularity. Cannot apply circularity filter.')


    ###Report some simple numbers
    print('Data report loaded successfully')

    initial_conditions = ld[condition_column].unique()
    print('Number of unique elements in axis column: %i'%len(initial_conditions))

    initial_strains = ld[strain_column].unique()
    print('Number of unique elements in grouping column: %i'%len(initial_strains))

    print('Number of plates: %i'%len(ld['Plate'].unique()))

    print('Number of non-NA data points: %i'%len(ld.loc[~pd.isnull(ld[values_column])].index))

    ###Simple QC filters
    n_datapoints = (~ld[values_column].isnull()).sum()
    if circularity:
        ld.loc[ld['Colony_circularity']<circularity, values_column] = np.nan
        nn_datapoints = (~ld[values_column].isnull()).sum()
        print('Removed %i entries with circularity < %f'%(n_datapoints-nn_datapoints, circularity))
        n_datapoints = nn_datapoints
    if set_missing_na:
        ld.loc[ld[values_column]==0, values_column] = np.nan
        nn_datapoints = (~ld[values_column].isnull()).sum()
        print('Removed %i entries with fitness 0'%(n_datapoints-nn_datapoints))
        n_datapoints = nn_datapoints

    ###Group by replicates
    ld_stats = ld.copy()
    #drop any NA
    ld_stats = ld_stats.loc[~ld_stats[values_column].isnull()]
    #Recompute number of axis and grouping elements
    conditions = ld_stats[condition_column].unique()
    print('Number of unique elements in axis column after filtering: %i'%len(conditions))
    strains = ld_stats[strain_column].unique()
    print('Number of unique elements in grouping column: %i'%len(strains))

    ld_stats['condition---strain'] = ld_stats[condition_column] + '---' + ld_stats[strain_column]
    ld_stats['rep'] = count_reps(ld_stats['condition---strain'])

    #Pivot this into wide format
    ld_stats_piv = ld_stats.pivot_table(index=strain_column, columns=[condition_column,'rep'], values=values_column)

    #assert that there are no duplicates, i.e. that count_reps() worked as expected
    assert (ld_stats.pivot_table(index=strain_column, columns=[condition_column,'rep'], values=values_column, aggfunc=len).unstack().dropna()==1.0).all()

    #Save this table:
    ld_stats_piv.to_csv(out_prefix+'_reps.csv')
    ###Compute summary stats
    mean_fitness = ld_stats_piv.mean(axis=1, level=0)
    median_fitness = ld_stats_piv.median(axis=1, level=0)
    fitness_stdev = ld_stats_piv.std(axis=1, level=0)
    obs_count = ld_stats_piv.count(axis=1, level=0)

    #Compute effect sizes
    median_effect_size = median_fitness.div(median_fitness[control_condition], axis=0)
    mean_effect_size = mean_fitness.div(mean_fitness[control_condition], axis=0)

    ###run Welch's t-test
    print('Running t-tests')
    p_Welch = {}
    b = ld_stats_piv.xs(control_condition,axis=1, level=0).values
    b = np.ma.masked_invalid(b)

    for co in conditions:
        a = ld_stats_piv.xs(co, axis=1, level=0).values
        a = np.ma.masked_invalid(a)
        pvals_temp = mstats_basic.ttest_ind(a, b, axis=1, equal_var=False)[1].filled(np.nan)
        p_Welch[co] = pd.Series(pvals_temp, index=ld_stats_piv.index)
    p_Welch = pd.concat(p_Welch, axis=1)
    #multiple testing correction by BH
    p_Welch_BH = p_Welch.copy()
    for c in p_Welch_BH:
        if p_Welch_BH[c].isnull().all():
            warn('No p-values obtained for %s (probably not enaough replicates)'%c)
        else:
            p_Welch_BH.loc[~p_Welch_BH[c].isnull(), c] = multit(p_Welch_BH.loc[~p_Welch_BH[c].isnull(), c], method='fdr_bh')[1]


    #aggregate data in table and save
    #And join together in one big data frame
    combined_data = pd.concat({'mean_fitness' : mean_fitness,
                               'mean_fitness_log2' : mean_fitness.applymap(np.log2),
                'median_fitness' : median_fitness,
                  'median_fitness_log2' : median_fitness.applymap(np.log2),
                'mean_effect_size' : mean_effect_size,
                'mean_effect_size_log2' : mean_effect_size.applymap(np.log2),
                'median_effect_size' : median_effect_size,
                'median_effect_size_log2' : median_effect_size.applymap(np.log2),
                'observation_count' : obs_count,
               'stdev_fitness' : fitness_stdev,
               'p_Welch' : p_Welch,
                'p_Welch_BH' : p_Welch_BH,
                'p_Welch_BH_-log10' : -p_Welch_BH.applymap(np.log10)}, axis=1)


    combined_data = combined_data.swaplevel(axis=1).sort_index(axis=1)
    combined_data.to_csv(out_prefix+'_summaryStats.csv')
    print('Interpretation completed and results saved.')
    return combined_data
        
