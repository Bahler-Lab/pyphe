import pandas as pd
from scipy.stats import ttest.ind

def interpret(ldpath, condition_column, strain_column, values_column, control_condition, ttest, save_replicates):
    '''
    Interpret experimental data report produced by pyphe-analyse. 
    '''
    
    #Import experimental report
    ld = pd.read_csv(ldpath, index_col=0)
    
    #Compute summary stats
    means = 
    medians = 
    stdev = 
    n = 
    
    #Compute effect sizes
    es = means/means[control_condition]
    
    #aggregate replicates
    ld['condition_strain'] = ld[condition_column] + '_' + ld[strain_column]
    ld['rep'] = count_reps(ld['condition_strain'])
    ld_piv = ld.pivot_table(index=strain_column, columns=[condition_column,'rep'], values='size_corr')
    
    if save_replicates:
        ld_piv.to_csv(save_replicates)
        
    #run ttest
    
    
    #aggregate data in table
    
    
    
    
def count_reps(inseries):
    inseries = inseries.tolist()
    counts = {k:0 for k in list(set(inseries))}
    out = [878 for i in range(len(inseries))]
    for ind, ite in enumerate(inseries):
        out[ind] = counts[ite]
        counts[ite] += 1
    return out
    
    from scipy import special
    
    
def custom_nan_welch_reg(a, b, mva, mvb, axis=0):
    
    (a, b) = (np.ma.masked_invalid(a), np.ma.masked_invalid(b))

    if a.size == 0 or b.size == 0:
        return (np.nan, np.nan)

    (x1, x2) = (a.mean(axis), b.mean(axis))
    (v1, v2) = (a.var(axis=axis, ddof=1), b.var(axis=axis, ddof=1))
    (v1, v2) = (np.maximum(v1,mva), np.maximum(v2, mvb))
    (n1, n2) = (a.count(axis), b.count(axis))

    vn1 = v1/n1
    vn2 = v2/n2
    with np.errstate(divide='ignore', invalid='ignore'):
        df = (vn1 + vn2)**2 / (vn1**2 / (n1 - 1) + vn2**2 / (n2 - 1))

    # If df is undefined, variances are zero.
    # It doesn't matter what df is as long as it is not NaN.
    df = np.where(np.isnan(df), 1, df)
    denom = np.ma.sqrt(vn1 + vn2)

    with np.errstate(divide='ignore', invalid='ignore'):
        t = (x1-x2) / denom
    probs = special.betainc(0.5*df, 0.5, df/(df + t*t)).reshape(t.shape)

    return (t, probs.squeeze())
