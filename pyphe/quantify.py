import os
import numpy as np
import pandas as pd
import math
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


def check_and_negate(orig_image, negate=True):
    
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
        
    return image

def quantify_single_image_fromBatch(orig_image, grid, griddist, t=1, d=3, s=1, negate=True, reportAll=False, hardImageThreshold=None, hardSizeThreshold=None):
    
    #Check and negate image
    image = check_and_negate(orig_image, negate=negate)
        
    #Make mask
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
    
    #Add circularity
    data['circularity'] = (4 * math.pi * data['area']) / (data['perimeter']**2)
    
    #Make qc image
    qc = label2rgb(mask, image=orig_image, bg_label=0)

    return (data, qc)
    
def quantify_batch(images, grid, griddist, qc='qc_images', out='pyphe_quant', t=1, d=3, s=1, negate=True, reportAll=False, hardImageThreshold=None, hardSizeThreshold=None):
    '''
    Analyse batches of plates.
    '''

    for fname, im in zip(images.files, images):
        data, qc_image = quantify_single_image_fromBatch(np.copy(im), grid, griddist, t=t, d=d, s=s, negate=negate, reportAll=reportAll, hardImageThreshold=hardImageThreshold, hardSizeThreshold=hardSizeThreshold)
        if not reportAll:
            data = data.drop('label', axis=1)
        
        image_name = os.path.basename(fname)
        data.to_csv(os.path.join(out, image_name+'.csv'))
    
        #Add labels and grid positions to qc image and save
        fig, ax = plt.subplots()
        ax.imshow(qc_image)
        if not reportAll:
            for i,r in data.iterrows():
                ax.text(r['centroid'][1], r['centroid'][0], str(r['row'])+'-'+str(r['column']), fontdict={'size':1, 'color':'w'})
        else:
            for i,r in data.iterrows():
                ax.text(r['centroid'][1], r['centroid'][0], str(r['label']), fontdict={'size':1.5, 'color':'w'})
        
        plt.savefig(os.path.join(qc, 'qc_'+image_name+'.png'), dpi=900)
        plt.clf()
        plt.close()

def quantify_single_image_fromTimecourse(orig_image, mask, negate=True):
    
    #Check and negate  image
    image = check_and_negate(orig_image, negate=negate)

    #Get background intensity
    bgmask = (mask==0).astype(int)
    bgdata = {r.label : r['mean_intensity'] for r in regionprops(bgmask, intensity_image=image)}
    bgmean = bgdata[1]
    #subtract mean background from image, floor again to avoid rare case of negative values
    image = image - bgmean
    image[image<0] = 0

    #Get intensity data for each blob
    data = {r.label : r['mean_intensity'] for r in regionprops(mask, intensity_image=image)}

    return data

        
def quantify_timecourse(images, grid, griddist, qc='qc_images', out='pyphe_quant', t=1, d=3, s=1, negate=True, reportAll=False, hardImageThreshold=None, hardSizeThreshold=None):
    '''
    Analyse a timeseries of images. Make the mask based on the last image and extract intensity information from all previous images based on that.
    '''
    #Check and negate final image
    fimage = check_and_negate(images[-1], negate=negate)
    
    #Make mask
    mask = make_mask(fimage, t=t, s=s, hardImageThreshold=hardImageThreshold, hardSizeThreshold=hardSizeThreshold)
    
    #Make table of intensities over time
    data = {fname : quantify_single_image_fromTimecourse(orig_image, mask, negate=negate) for fname,orig_image in zip(images.files, images)}
    data = pd.DataFrame(data).transpose()
    
    #Get centroids and match to positions
    centroids = {r.label : r['centroid'] for r in regionprops(mask)}
    blob_to_pos = match_to_grid(centroids.keys(), centroids.values(), grid, griddist, d=d, reportAll=reportAll)
    
    #Select only those blobs which have a corresponding grid position
    data = data.loc[:,[l in blob_to_pos for l in data.columns]]
    
    #If not reportAll, replace blobs by grid position information and sort
    if not reportAll:
        data.columns = data.columns.map(lambda x: blob_to_pos[x])
        data = data[sorted(list(data), key=lambda x: 100*int(x.split('-')[0]) + int(x.split('-')[1]))]
    #Save table
    image_name = os.path.basename(images.files[-1])
    data.to_csv(os.path.join(out, image_name+'.csv'))

    #make qc image
    qc_image = label2rgb(mask, image=images[-1], bg_label=0)
    fig, ax = plt.subplots()
    ax.imshow(qc_image)
    if not reportAll:
        for blob in blob_to_pos:
            ax.text(centroids[blob][1], centroids[blob][0], blob_to_pos[blob], fontdict={'size':1.5, 'color':'w'})
    else:
        for blob in blob_to_pos:
            ax.text(centroids[blob][1], centroids[blob][0], blob, fontdict={'size':1.5, 'color':'w'})

    plt.savefig(os.path.join(qc, 'qc_'+image_name+'.png'), dpi=900)
    plt.clf()
    plt.close()
    
    

def quantify_redness(images, grid, griddist, t=1, d=1, s=1, negate=False, reportAll=True, hardImageThreshold=None, hardSizeThreshold=None):
    pass