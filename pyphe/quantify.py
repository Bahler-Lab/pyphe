import os
import numpy as np
import pandas as pd
from warnings import warn
from matplotlib import pyplot as plt
from scipy.spatial import distance

from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects
from skimage.segmentation import clear_border
from skimage.util import invert
from skimage.measure import regionprops, label
from skimage.color import label2rgb


def make_grid(gd):
    '''
    Converts a grid definition to a list (x,y positions) of all vertices in the grid.
    '''
    
    rows, cols, x1, y1, x2, y2 = gd
    xpos = np.linspace(x1, x2, num=cols)
    ypos = np.linspace(y1, y2, num=rows)
    
    griddistx = xpos[1] - xpos[0]
    griddisty = ypos[1] - ypos[0]
    
    #Check if spacing similar
    if (abs(griddistx-griddisty)/(0.5*(griddistx+griddisty))) > 0.1:
        warn('Uneven spacing between rows and columns. Are you sure this is intended?')
   
    #Make dictionary of grid positions
    grid = {}
    for r in range(rows):
        for c in range(cols):
            grid[(r+1,c+1)] = (ypos[r], xpos[c])
            
    return grid, 0.5*(griddistx+griddisty)


def match_to_grid(labels, centroids, grid, griddist, d=3, reportAll=False):
    '''
    From a list of grid positions and a list of centroids, construct a distance matrix between all pairs and return the best fits as a dictionary.
    '''
    
    #Construct distance matrix as pandas table
    dm = distance.cdist(np.array(list(centroids)), np.array(list(grid.values())), metric='euclidean')
    dm = pd.DataFrame(dm, index=labels, columns=map(lambda x: '-'.join(map(str,x)),grid.keys()))
            
    #Select matches
    dm[dm>(griddist/d)] = np.nan

    if not reportAll:
        #Find best match for each grid position
        dm = dm.idxmin(axis=0)
        dm = dm.dropna().astype(int)
        #Swap index and values
        #There should never be a blob associated to two blob positions since d>2 is enforced in the command line interface
        dm = pd.Series(dm.index.values, index=dm)
        dm = dm.to_dict()        
        
    else:
        #Find best match for each blob
        dm = dm.idxmin(axis=1)
        dm = dm.dropna()
        dm = dm.to_dict()
            
    return dm


def make_mask(image, t=1, s=1, hardImageThreshold=None, hardSizeThreshold=None):
    '''
    Identifies suitable morphological components from image by thresholding.
    '''
    
    if hardImageThreshold:
        thresh = hardImageThreshold
    else:
        thresh = t*threshold_otsu(image)
        
    mask = image>thresh
    
    #Filter small components. The default threshold is 0.0001% of the image area 
    if hardSizeThreshold:
        size_thresh = hardSizeThreshold
    else:
        size_thresh = s * image.shape[0] * image.shape[1] * 0.000001
    mask = remove_small_objects(mask, min_size=size_thresh)
    
    #Fill holes?? In future
    
    #Clear border
    mask = clear_border(mask)
    
    #Label connected components
    mask = label(mask)
    
    return mask
    

def quantify_single_image_fromBatch(orig_image, grid, griddist, t=1, d=3, s=1, negate=True, reportAll=False, hardImageThreshold=None, hardSizeThreshold=None):
    
    image = np.copy(orig_image)
    
    #Check if images are grayscale and convert if necessary
    if len(image.shape) == 3:
        warn('The following is not a greyscale image and will be converted before processing: %s'%images.files[i])
        image = image[:,:,0] + image[:,:,1] + image[:,:,2]

    #Convert to float and re-scale to [0,1]            
    image = image.astype(float)
    image = image / 255.0
    
    #Negate images if required
    if negate:
        image = invert(image)
        
    #Make mask and label
    mask = make_mask(image, t=t, s=s, hardImageThreshold=hardImageThreshold, hardSizeThreshold=hardSizeThreshold)
    
    #Measure regionprobs
    data = {r.label : {p : r[p] for p in ['label', 'area', 'centroid', 'mean_intensity', 'perimeter']} for r in regionprops(mask, intensity_image=image)}
    data = pd.DataFrame(data).transpose()
    
    blob_to_pos = match_to_grid(data['label'], data['centroid'], grid, griddist, d=d, reportAll=reportAll)
    
    #Select only those blobs which have a corresponding grid position
    data = data.loc[[l in blob_to_pos for l in data['label']]]
    #Add grid position information to table
    data['row'] = data['label'].map(lambda x: blob_to_pos[x].split('-')[0])
    data['column'] = data['label'].map(lambda x: blob_to_pos[x].split('-')[1])
    
    #Make qc image
    qc = label2rgb(mask, image=orig_image, bg_label=0)

    return (data, qc)
    
def quantify_batch(images, grid, griddist, qc='qc_images', out='pyphe_quant', t=1, d=3, s=1, negate=True, reportAll=False, hardImageThreshold=None, hardSizeThreshold=None):
    '''
    Analyse batches of plates.
    '''

    for fname, im in zip(images.files, images):
        data, qc_image = quantify_single_image_fromBatch(np.copy(im), grid, griddist, t=t, d=d, s=s, negate=negate, reportAll=reportAll, hardImageThreshold=hardImageThreshold, hardSizeThreshold=hardSizeThreshold)
        data = data.drop('label', axis=1)
        data.to_csv(os.path.join(out, fname+'.csv'))
    
        #Add labels and grid positions to qc image and save
        fig, ax = plt.subplots()
        ax.imshow(qc_image)
        for i,r in data.iterrows():
            ax.text(r['centroid'][1], r['centroid'][0], str(r['row'])+'-'+str(r['column']), fontdict={'size':1, 'color':'w'})
        #Maybe add lines for grid positions later
        plt.savefig(os.path.join(qc, 'qc_'+fname+'.png'), dpi=900)
        plt.clf()
        plt.close()
        
def quantify_timecourse(images, grid, griddist, t=1, d=1, s=1, negate=True, reportAll=True, hardImageThreshold=None, hardSizeThreshold=None):
    pass

    #Check if images are grayscale

def quantify_redness(images, grid, griddist, t=1, d=1, s=1, negate=False, reportAll=True, hardImageThreshold=None, hardSizeThreshold=None):
    pass