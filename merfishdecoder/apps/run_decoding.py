import os
import pickle
import pandas as pd
import numpy as np

from merfishdecoder.core import zplane
from merfishdecoder.util import utilities
from merfishdecoder.util import decoder

def run_job(
    dataSetName: str = None,
    fov: int = None,
    zpos: float = None,
    decodingImagesName: str = None,
    outputName: str = None,
    maxCores: int = 5,
    borderSize: int = 80,
    magnitudeThreshold: float = 0.0,
    distanceThreshold: float = 0.60):

    """
    MERFISH Decoding.

    Args
    ----
    dataSetName: input dataset name.
    
    fov: field view number.

    zpos: z position in uM.
    
    decodingImagesName: decoding image file name.
    
    outputName: output file name.
    
    maxCores: max number of processors for parallel computing. 
    
    borderSize: number of pixels to be removed from the decoding
           images.

    magnitudeThreshold: the min magnitudes for a pixel to be decoded.
             Any pixel with magnitudes less than magnitudeThreshold 
             will be filtered prior to the decoding.
             
    distanceThreshold: the maximum distance between an assigned pixel
             and the nearest barcode. Pixels for which the nearest barcode
             is greater than distanceThreshold are left unassigned.

    """

    utilities.print_checkpoint("Decode MERFISH images")
    utilities.print_checkpoint("Start")
    
    # generate zplane object
    zp = zplane.Zplane(dataSetName,
                       fov=fov,
                       zpos=zpos)

    # create the folder
    os.makedirs(os.path.dirname(outputName),
                exist_ok=True)

    # load readout images
    f = np.load(decodingImagesName)
    decodingImages = f[f.files[0]]
    f.close()
    
    # pixel based decoding
    decodedImages = decoder.decoding(
             obj = zp,
             movie = decodingImages,
             borderSize = borderSize,
             distanceThreshold = distanceThreshold,
             magnitudeThreshold = magnitudeThreshold,
             numCores = maxCores)
    
    # save decoded images
    np.savez(outputName,
             decodedImage=decodedImages["decodedImage"], 
             magnitudeImage=decodedImages["magnitudeImage"],
             distanceImage=decodedImages["distanceImage"])

    utilities.print_checkpoint("Done")

