import os
import numpy as np
import pandas as pd
import math
from warnings import warn
from matplotlib import pyplot as plt
from scipy.spatial import distance
from scipy.signal import find_peaks
from scipy.stats import trim_mean
import math

from skimage.filters import threshold_otsu, gaussian, threshold_local
from skimage.morphology import remove_small_objects, convex_hull_object
from skimage.segmentation import clear_border
from skimage.util import invert
from skimage.measure import regionprops, label
from skimage.color import label2rgb
from skimage.draw import rectangle_perimeter

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


def make_grid_auto(im, grid):

    nrows, ncols = map(int,grid.split('-'))
    
    def find_grid_positions_1d(image, axis, n):

        #extract means across axis
        imvals = image.mean(axis=axis)
        imvals = imvals - imvals.min()
        imvals = imvals / imvals.max()

        #find peaks. Define minimum distance based on image dimension
        peaks = find_peaks(imvals, distance=(len(imvals)-0.2*len(imvals))/n)[0]

        #find distance between colonies. Use trimmed mean which is robust to outliers. Median is not precise enough (need sub-pixel resolution)
        med = trim_mean(peaks[1:] - peaks[:-1], 0.2)
        #for bad input images the distance between colonies times the number of rows/columns can exceed image dimensions. 
        #In this case, guess the distance based on image dimensions and number of colonies
        if med*(n-1) > len(imvals):
            print('Could not detect enough peaks. Guessing grid positions. Please check QC images carefully.')
            med = (len(imvals)-0.1*len(imvals))/(n-1)

        #create hypothetical, ideal grid based on mean distance
        to_fit = np.linspace(0, med*(n-1),n)

        #Find the maximum offset and all offset positions to try
        max_offset = len(imvals)-to_fit[-1]
        pos_to_try = np.linspace(0,int(max_offset),int(max_offset)+1)

        #Make a cosine function with the same period as the mean distance between colonies
        b = 2 * math.pi / med
        x = np.linspace(0,(n-1)*med,int((n-1)*med))
        y = (1+np.cos(x*b))/2#scale roughly to data
        errors = [((y - imvals[o:len(y)+o])**2).sum() for o in pos_to_try.astype(int)]

        return to_fit + np.argmin(errors), med

    cols, colmed = find_grid_positions_1d(im,0,ncols)
    rows, rowmed = find_grid_positions_1d(im,1,nrows)

    grid = {}
    for ri,r in enumerate(rows):
        for ci,c in enumerate(cols):
            grid[(ri+1, ci+1)] = (r, c)
               
    return grid, 0.5*(colmed+rowmed)
    

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


def make_mask(image, t=1, s=1, hardImageThreshold=None, hardSizeThreshold=None, local=False, convexhull=False):
    '''
    Identifies suitable morphological components from image by thresholding.
    '''
    
    if local:
        mask = image > t*threshold_local(image, 151)

    else:
        if hardImageThreshold:
            thresh = hardImageThreshold
        else:
            thresh = t*threshold_otsu(image)
            
        mask = image>thresh
    
    #Fill holes. Warning: takes a long time
    if convexhull:
        mask = convex_hull_object(mask)
        
    #Filter small components. The default threshold is 0.00005 of the image area 
    if hardSizeThreshold:
        size_thresh = hardSizeThreshold
    else:
        size_thresh = s * np.prod(image.shape) * 0.00005
    mask = remove_small_objects(mask, min_size=size_thresh)
    
    
    #Clear border
    mask = clear_border(mask)
    
    #Label connected components
    mask = label(mask)
    
    return mask

def check_and_negate(orig_image, negate=True):
    '''
    Check if image is greyscale, convert if it isn't. Convert to float and invert intensities.
    '''
    image = np.copy(orig_image)
    
    #Check if images are grayscale and convert if necessary
    if len(image.shape) == 3:
        warn('Image is not in greyscale, converting before processing')
        image = image.astype(int).mean(axis=2)

    #Convert to float and re-scale to [0,1]            
    image = image.astype(float)
    image = image / 255.0
    
    #Negate images if required
    if negate:
        image = invert(image)
        
    return image

def quantify_single_image_size(orig_image, grid, auto, t=1, d=3, s=1, negate=True, reportAll=False, hardImageThreshold=None, hardSizeThreshold=None, localThresh=None, convexhull=False):
    '''
    Process a single image to extract colony sizes.
    '''
    
    #Prepare image
    image = check_and_negate(orig_image, negate=negate)
    
    #Create grid
    if auto:
        grid, griddist = make_grid_auto(image, grid)
    else:
        grid, griddist = make_grid(grid)
        
    #Make mask
    mask = make_mask(image, t=t, s=s, hardImageThreshold=hardImageThreshold, hardSizeThreshold=hardSizeThreshold, local=localThresh, convexhull=convexhull)
    
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

def quantify_single_image_redness(orig_image, grid, auto, t=1, d=3, s=1, negate=True, reportAll=False, hardImageThreshold=None, hardSizeThreshold=None):
    '''
    Process a single image (phloxine mode).
    '''
    
    #Prepare image
    image = prepare_redness_image(orig_image)
    
    #Create grid
    if auto:
        grid, griddist = make_grid_auto(image, grid)
    else:
        grid, griddist = make_grid(grid)
    
    #Make mask
    #Adjust threshold for redness images slightly, just what works in practise. t parameter is still applied as additional coefficient
    mask = make_mask(image, t=1.02*t, s=s, hardImageThreshold=hardImageThreshold, hardSizeThreshold=hardSizeThreshold, local=True)
    
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
    
    #Make qc image, add bounding boxes to blobs with grid assigned
    qc = np.copy(orig_image)
    for region in regionprops(mask):
        if region.label in data['label']: 
            minr, minc, maxr, maxc = region.bbox
            bboxrows, bboxcols = rectangle_perimeter([minr, minc], end=[maxr, maxc], shape=image.shape, clip=True)
            qc[bboxrows, bboxcols,:] = np.array((255,255,255))

    return (data, qc)
    
def quantify_batch(images, grid, auto, mode, qc='qc_images', out='pyphe_quant', t=1, d=3, s=1, negate=True, reportAll=False, reportFileNames=None, hardImageThreshold=None, hardSizeThreshold=None, localThresh=None, convexhull=False):
    '''
    Analyse colony size for batch of plates. Depending on mode, either the quantify_single_image_grey or quantify_single_image_redness function is applied to all images.
    '''

    for fname, im in zip(images.files, images):
        
        if mode == 'batch':
            data, qc_image = quantify_single_image_size(np.copy(im), grid, auto, t=t, d=d, s=s, negate=negate, reportAll=reportAll, hardImageThreshold=hardImageThreshold, hardSizeThreshold=hardSizeThreshold, localThresh=localThresh, convexhull=convexhull)
        elif mode == 'redness':
            data, qc_image = quantify_single_image_redness(np.copy(im), grid, auto, t=t, d=d, s=s, negate=negate, reportAll=reportAll, hardImageThreshold=hardImageThreshold, hardSizeThreshold=hardSizeThreshold)
        else:
            raise ValueError('Mode must be batch or redness.')
        
        image_name = os.path.basename(fname)
        if not reportAll:
            data.drop('label', axis=1).to_csv(os.path.join(out, image_name+'.csv'))
        else:
            data.to_csv(os.path.join(out, image_name+'.csv'))
    
        #Add labels and grid positions to qc image and save
        fig, ax = plt.subplots()
        ax.imshow(qc_image)
        if not reportAll:
            data['annot'] = data['row'].astype(str) + '-' + data['column'].astype(str)
        else:
            data['annot'] = data['label']
        if mode == 'redness':
            data['annot'] = data['annot'] + '\n' + data['mean_intensity'].astype(float).round(4).astype(str)
        for i,r in data.iterrows():
            ax.text(r['centroid'][1], r['centroid'][0], r['annot'], fontdict={'size':1.5, 'color':'w'})
                
        plt.savefig(os.path.join(qc, 'qc_'+image_name+'.png'), dpi=900)
        plt.clf()
        plt.close()

def quantify_single_image_fromTimecourse(orig_image, mask, negate=True, calibrate='x'):
    '''
    Apply a previously determined mask to an image from a timeseries.
    '''
    
    #Prepare image. Don't do any scaling. The scaling depends on the maximum and minimum pixel intensity which is not very stable.
    #Negate images if required
    if negate:
        image = invert(orig_image)
    else:
        image = orig_image

    #Get background intensity
    bgmask = (mask==0).astype(int)
    bgdata = {r.label : r['mean_intensity'] for r in regionprops(bgmask, intensity_image=image)}
    bgmean = bgdata[1]
    #subtract mean background from image, floor again to avoid rare case of negative values
    image = image - bgmean
    image[image<0] = 0

    #transform with calibration function
    image_trafo = eval(calibrate.replace('x', 'image'))
    
    #Get intensity data for each blob
    data = {r.label : r['mean_intensity']*r['area'] for r in regionprops(mask, intensity_image=image_trafo)}

    return data

        
def quantify_timecourse(images, grid, auto, qc='qc_images', out='pyphe_quant', t=1, d=3, s=1, negate=True, reportAll=False, reportFileNames=False, hardImageThreshold=None, hardSizeThreshold=None, calibrate='x', timepoints=None, localThresh=None, convexhull=False):
    '''
    Analyse a timeseries of images. Make the mask based on the last image and extract intensity information from all previous images based on that.
    '''
    #Get final image
    if negate:
        fimage = invert(images[-1])   
    else: 
        fimage = images[-1]
    
    #Create grid
    if auto:
        grid, griddist = make_grid_auto(fimage, grid)
    else:
        grid, griddist = make_grid(grid)
    
    #Make mask
    mask = make_mask(fimage, t=t, s=s, hardSizeThreshold=hardSizeThreshold, convexhull=convexhull)
    
    #Make table of intensities over time
    data = {fname : quantify_single_image_fromTimecourse(orig_image, mask, negate=negate, calibrate=calibrate) for fname,orig_image in zip(images.files, images)}
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
    
    #Set correct index
    if not reportFileNames:
        if timepoints:
            with open(timepoints, 'r') as tpfile:
                tps = tpfile.readlines()
                tps = [s.strip() for s in tps]
            if len(tps) == len(data.index):
                data.index = tps
            else:
                warn('Could not read timepoints from file as the file has the wrong number of entries. Falling back to simple numbering.')
                data.index = range(1,len(data.index)+1)
        else:
            data.index = range(1,len(data.index)+1)

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

def prepare_redness_image(orig_image):
    '''
    Prepare image for thresholding and analysis. Channels are weighted by (0, 0.5, 1) and summed. The background is estimated by gaussian blur and subtracted. The image is inverted.
    '''
    image = np.copy(orig_image)

    #Color channel transformations and convert to grey
    image = 0.5*image[:,:,1] + 1*image[:,:,2]
    #Convert to float and rescale to range [0,1]
    #I don't think other fancier methods for histogram normalisation are suitable or required since simple thresholding is applied later

    #Estimate background by gaussian. Scale sigma with image area to compensate for different resolutions
    background = gaussian(image, sigma=np.prod(image.shape)/10000, truncate=4) 
    image = image - background #This may contain some negative values

    #Scale image to [0,1] in invert
    image = image.astype(float)
    image = image - np.min(image)
    image = image/np.max(image)
    image = 1 - image
    
    return image
  

