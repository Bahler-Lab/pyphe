import pandas as pd
from scipy.stats import ttest_ind
import numpy as np
from statsmodels.stats.multitest import multipletests as multit

def count_reps(inseries):
    inseries = inseries.tolist()
    counts = {k:0 for k in list(set(inseries))}
    out = [878 for i in range(len(inseries))]
    for ind, ite in enumerate(inseries):
        out[ind] = counts[ite]
        counts[ite] += 1
    return out
    
    from scipy import special
    

def interpret(ldpath, condition_column, strain_column, values_column, control_condition, out_prefix, ld_encoding='utf-8'):
    '''
    Interpret experimental data report produced by pyphe-analyse. 
    '''
    
    ###Import experimental report
    ld = pd.read_csv(ldpath, index_col=0, encoding=ld_encoding)

    ###Check if essential columns exist
    print('Checking input table')
    print('Checking if condition_column exists')
    if condition_column not in list(ld):
        raise NameError('condition_column not found in table.')
    print('....OK')

    print('Checking if strain_column exists')
    if strain_column not in list(ld):
        raise NameError('strain_column not found in table.')
    print('....OK')

    print('Checking if values_column exists')
    if values_column not in list(ld):
        raise NameError('values_column not found in table.')
    print('....OK')

    print('Checking if control_condition exists in condition_column')
    if control_condition not in ld[condition_column]:
        raise NameError('condition_column not found in condition_column.')
    print('....OK')

    
    ###Report some simple numbers
    print('Data report loaded successfully')
    
    conditions = ld[condition_column].unique()
    print('Number of conditions: %i'%len(conditions))
    
    strains = ld[strain_column].unique()
    print('Number of strains: %i'%len(strains))
    
    print('Number of plates: %i'%len(ld['Plate'].unique()))

    print('Number of non-NA data points: %i'%len(ld.loc[ld[~values_column].insull()].index))
    
    ###Group by replicates
    ld_stats = ld.copy()
    ld_stats['condition---strain'] = ld_stats[condition_column] + '---' + ld_stats[strain_column]
    ld_stats['rep'] = count_reps(ld_stats['condition---strain'])
    
    #Pivot this into wide format
    ld_stats_piv = ld_stats.pivot_table(index=strain_column, columns=[condition_column,'rep'], values=values_column)

    #assert that there are no duplicates, i.e. that count_reps() worked as expected
    assert (ld_stats.pivot_table(index=strain_column, columns=[condition_column,'rep'], values=values_column, aggfunc=len).unstack().dropna()==1.0).all()
    
    #Save this table:
    ld_stats.to_csv(out_prefix+'_reps.csv')
    
    ###Compute summary stats
    mean_fitness = ld_stats_piv.mean(axis=1, level=1)
    median_fitness = ld_stats_piv.median(axis=1, level=1)
    fitness_stdev = ld_stats_piv.std(axis=1, level=1)
    obs_count = ld_stats_piv.count(axis=1, level=1)
    
    #Compute effect sizes
    median_effect_size = median_fitness.div(median_fitness[control_condition], axis=0)
    mean_effect_size = mean_fitness[v].div(mean_fitness[control_condition], axis=0)
   
    ###run Welch's t-test
    print('Running t-tests')
    p_Welch = {}
    for co in conditions:
        pvals_temp = ttest_ind(ld_stats_piv.xs(co, axis=1, level=1).values, ld_stats_piv.xs(ctr_cond, axis=1, level=1).values, axis=1, nan_policy='omit', equal_var=False)[1].filled(np.nan)
        p_Welch[co] = pd.Series(pvals_temp, index=ld_stats_piv.index)
    p_Welch = pd.concat(p_Welch, axis=1)

    #multiple testing correction by BH
    p_Welch_BH = p_Welch.copy()
    for c in p_Welch_BH:
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
        

