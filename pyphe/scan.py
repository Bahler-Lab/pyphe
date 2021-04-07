from shutil import which
from subprocess import check_output
from warnings import warn
import sys
from os import mkdir
import numpy as np
from datetime import datetime
import time

def find_scanner(scanner_index):
    '''
    This function performs a few vital checks before initialising scan sequence and selects a suitable scanner. 
    '''
    #Check if ImageMagick can be called from command line
    if which('convert') is None:
        raise ImportError("Cannot find ImageMagick's convert tool. Please make sure ImageMagick is installed and can be called from the command line.")
    
    #Look for scanners
    print('Searching for scanners.')
    scanner_list = check_output('scanimage -L', shell=True).decode('ascii')
    if 'No scanners were identified' in scanner_list:
        raise RuntimeError('Could not find any scanners. Please check scanners are connected and turned on, work with SANE and the TPU8x10 mode is enabled.') 
    scanner_list = [s for s in scanner_list.split('\n') if not s.strip()=='']
    scanner_list = [s.split()[1][1:-1] for s in scanner_list]
    print('Scanners found: ' + str(scanner_list))
    scanner = scanner_list[scanner_index-1]

    print('Using scanner %s'%scanner)
    return scanner
    
def scan_batch(n, plateStart, prefix, postfix, fixture, resolution, geometries, scanner, mode, format):
    '''
    High-level function for scanning a batch of plates. 
    '''
    
    ppscan = len(geometries[fixture])#plates per scan

    #Get geometry string and adapt to resolution
    geometry = geometries[fixture]

    print('Loaded geometry settings for fixture %s: '%fixture + str(geometry))
    geometry_temp = []
    for g in geometry:
        glist = list(map(lambda x: str(int(int(x)*(resolution/600.0))), g.replace('+', 'x').split('x')))
        geometry_temp.append(glist[0] + 'x' + glist[1] + '+' + glist[2] + '+' + glist[3])

    print('Geometry settings scaled to resolution: ' + str(geometry_temp))
    geometry = geometry_temp

    wdir = '%s_%s/'%(prefix,postfix)
    mkdir(wdir)
    rdir = wdir + 'raw_scans/'
    mkdir(rdir)
    print('Successfully created directories. Please make sure the scanner is turned on.')

    nscans = int(np.ceil(n/float(ppscan)))
    labels = list(map(str, range(plateStart, plateStart+n)))
    labels += ['empty']*(ppscan-1)#Max number of emtpy bays in last scan
    for i in range(1, nscans+1):
        print('Preparing for scan %i out of %i'%(i,nscans))
        print('Please load the scanner as follows:')
        for q in range(1,ppscan+1):
            print('Bay %i -> Plate %s'%(q, labels[(i-1)*ppscan+(q-1)]))

        ready = None
        while not ready:
            try:
                inp = input('If ready, enter y to start scan > ')
                if inp == 'y':
                    ready = True
                else:
                    raise Exception
            except Exception:
                print('Invalid input')

        source = 'TPU8x10' if mode=='Gray' else 'Flatbed'

        cmdStr = 'scanimage --source %s --mode %s --resolution %i --format=tiff --device-name=%s > %s%s_rawscan%s_%s.tiff'%(source, mode, resolution, scanner, rdir, prefix, i, postfix)
        check_output(cmdStr, shell=True)

        for plate in range(ppscan):
            plateNr = (i-1)*ppscan+plate
            if plateNr < n:
                cmdStr = 'convert %s%s_rawscan%s_%s.tiff -crop %s +repage -rotate 90 -flop %s%s_%i_%s.%s'%(rdir, prefix, i, postfix, geometry[plate], wdir, prefix, plateNr+plateStart, postfix, format)
                check_output(cmdStr, shell=True)


    print('Done')
    

def scan_timecourse(nscans, interval, prefix, postfix, fixture, resolution, geometries, scanner, mode, format):
    '''
    High-level function for acquiring image timeseries.
    '''
 
    ppscan = len(geometries[fixture])#plates per scan
    
    #Get geometry string and adapt to resolution
    geometry = geometries[fixture]
    
    print('Loaded geometry settings for fixture %s: '%fixture + str(geometry))
    geometry_temp = []
    for g in geometry:
        glist = list(map(lambda x: str(int(int(x)*(resolution/600.0))), g.replace('+', 'x').split('x')))
        geometry_temp.append(glist[0] + 'x' + glist[1] + '+' + glist[2] + '+' + glist[3])

    print('Geometry settings scaled to resolution: ' + str(geometry_temp))
    geometry = geometry_temp

    #Create directories
    wdir = '%s_%s/'%(prefix,postfix)
    mkdir(wdir)
    for q in range(1, ppscan+1):
        mkdir(wdir+'plate_'+str(q))
    rdir = wdir + 'raw_scans/'
    mkdir(rdir)
    
    #Open log
    log = open(wdir+'/scanlog.txt', 'w')
    timepoints = open(wdir+'/timepoints.txt', 'w')
    log.write(str(datetime.now()) + ' - Started scanplates-timecourse with the following parameters: ' + ' ,'.join(map(str,[nscans, interval, prefix, postfix, fixture, resolution, geometries, scanner, mode])) + '\n')
    
    print('Successfully created directories.')

    starttime = datetime.now()
    for i in range(1, nscans+1):
        print('Preparing for scan %i out of %i'%(i,nscans))

        source = 'TPU8x10' if mode=='Gray' else 'Flatbed'
        
        cmdStr = 'scanimage --source %s --mode %s --resolution %i --format=tiff --device-name=%s > %s%s_rawscan%i_%s.tiff'%(source, mode, resolution, scanner, rdir, prefix, i, postfix)
        check_output(cmdStr, shell=True)

        for plate in range(ppscan):
            cmdStr = 'convert %s%s_rawscan%i_%s.tiff -crop %s +repage -rotate 90 -flop %s%s/%s_%i_%s_plate%i.%s'%(rdir, prefix, i, postfix, geometry[plate], wdir, 'plate_'+str(plate+1), prefix, i, postfix, plate+1, format)
            check_output(cmdStr, shell=True)


        log.write(str(datetime.now()) + ' - Scan %i completed sucessfully\n'%i)
        log.flush()
        timepoints.write(str((datetime.now() - starttime).total_seconds()/(60*60.0)) + '\n')
        timepoints.flush()
        time.sleep(interval*60)#Convert to seconds
        
    log.close()
    timepoints.close()
