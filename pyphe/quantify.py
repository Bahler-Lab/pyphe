
import numpy as np

from warning import warn
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects
from skimage.segmentation import clear_border
from skimage.util import invert


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
    if (abs(griddistx-griddisty)/(0.5*(griddistx+griddisty)) > 0.1:
        warn('Uneven spacing between rows and columns. Are you sure this is intended?')
   
    return zip(xpos,ypos), 0.5*(griddistx+griddisty)


def match_to_grid():
    pass

def make_mask(image, t=1, s=1, hardImageThreshold=None, hardSizeThreshold=None):
    '''
    Identifies suitable morphological components from image by thresholding.
    '''
    
    if hardImageThreshold:
        thresh = hardImageThreshold
    else:
        thresh = t*threshold_otsu
        
    mask = image>thresh
    
    #Filter small components. The default threshold is 0.001% of the image area 
    if hardSizeThreshold:
        size_thresh = hardSizeThreshold
    else:
        size_thresh = s * image.shape[0] * image.shape[1] * 0.00001
    mask = remove_small_objects(mask, min_size=size_thresh)
    
    #Fill holes?? In future
    
    #Clear border
    mask = clear_border(mask)
    
    return mask
    
def single_image_batchMode(image):
    
    
    
def quantify_batch(images, grid, griddist, t=1, d=1, s=1, negate=True, onlyNearestQ=True, hardImageThreshold=None, hardSizeThreshold=None):
	

    for i,im in enumerate(images):
        
        #Check if images are grayscale and convert if necessary
        if len(im.shape) == 3:
            warn('The following is not a greyscale image and will be converted before processing: %s'%images.files[i])
            images[i] = images[i][:,:,0] + images[i][:,:,1] + images[i][:,:,2]

        #Convert to float and re-scale to [0,1]            
        images[i] = images[i].astype(float)
        images[i] = images[i] - np.min(images[i])
        images[i] = images[i] / np.max(images[i])
        
        #Negate images if required
        images[i] = invert(images[i])

    

    
    
    
	Batch[toAnalyse_] :=
    Module[{analyse},
        analyse[imagePath_] := 
            Module[{image, mask, posDict, headers, data, baseStr, background, backgroundInt, gtlAssoc, areas, intensities}, 
                baseStr = StringSplit[StringSplit[imagePath, "/"][[-1]], "."][[;;-2]];
            
                image = If[negateQ, ColorNegate[Import[imagePath]], Import[imagePath]];
                mask = MakeMask[image];
                posDict = MatchComponentsToGrid[mask, baseStr][[1]];
                gtlAssoc = MatchComponentsToGrid[mask, baseStr][[2]];

                (*Find background intensitiy*)
                background = Table[1, {i, Dimensions[mask][[1]]}, {j, Dimensions[mask][[2]]}] - Unitize[mask];
                backgroundInt = ComponentMeasurements[{background, image}, "MeanIntensity"];
                
                (*Measure area and intensities*)
                areas = Association[ComponentMeasurements[{mask, image}, "Area"]];
                intensities = ComponentMeasurements[{mask, image}, "IntensityData"];
                intensities[[All, 2]] = intensities[[All, 2]] - backgroundInt[[1, 2]];
                intensities = Map[Total, Association[intensities]];

		(*Measure other things*)
		perimeters = Association[ComponentMeasurements[{mask, image}, "PerimeterLength"]];
		circularities = Association[ComponentMeasurements[{mask, image}, "Circularity"]];
                centroids = Association[ComponentMeasurements[{mask, image}, "Centroid"]];
		centroidsx = Map[(#[[1]])&,centroids];
		centroidsy = Map[(#[[2]])&,centroids];

                (*Compile table and export*)
                data = Table[{gtlAssoc[x[[1]]], x[[1, 1]], x[[1, 2]], areas[x[[2]]], intensities[x[[2]]], perimeters[x[[2]]], circularities[x[[2]]], centroidsx[x[[2]]], centroidsy[x[[2]]]}, {x, posDict}];
                headers = {"Position", "Row", "Column", "Area", "IntegratedIntensity", "PerimeterLength", "Circularity", "Centroid-x", "Centroid-y"};

                Export[StringJoin["maya_results/", baseStr, ".csv"], Join[{headers}, data], "CSV"];
                ];
                
        If[parallelQ, ParallelDo[analyse[imagePath], {imagePath, toAnalyse}], Do[analyse[imagePath], {imagePath, toAnalyse}]]];
      
def quantify_timecourse(images, grid, griddist, t=1, d=1, s=1, negate=True, onlyNearestQ=True, hardImageThreshold=None, hardSizeThreshold=None):
	pass

    #Check if images are grayscale

def quantify_redness(images, grid, griddist, t=1, d=1, s=1, negate=False, onlyNearestQ=True, hardImageThreshold=None, hardSizeThreshold=None):
	pass