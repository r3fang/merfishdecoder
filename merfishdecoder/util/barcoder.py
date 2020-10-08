import gc
import random
import cv2
import copy
import multiprocessing as mp
import SharedArray as sa
import tempfile
import os
import h5py

import pandas as pd
import numpy as np
from numpy import linalg as LA
from sklearn.neighbors import NearestNeighbors
from collections import Counter
from skimage import measure

from merfishdecoder.data import codebook as cb

def extract_barcodes(
    decodedImage: np.ndarray = None,
    distanceImage: np.ndarray = None,
    probabilityImage: np.ndarray = None, 
    magnitudeImage: np.ndarray = None, 
    barcodesPerCore: int = 50,
    numCores: int = 1
    ) -> pd.core.frame.DataFrame:

    tmpPrefix = \
        tempfile.NamedTemporaryFile().name.split("/")[-1]

    decodedImageFile = \
        tmpPrefix + "_decodedImage"
    
    probabilityImageFile = \
        tmpPrefix + "_probabilityImage"

    distanceImageFile = \
        tmpPrefix + "_distanceImage"

    magnitudeImageFile = \
        tmpPrefix + "magnitudeImage"
    
    decodedImageShared = sa.create(
        "shm://" + decodedImageFile, 
        decodedImage.shape)
    
    probabilityImageShared = sa.create(
        "shm://" + probabilityImageFile, 
        probabilityImage.shape)

    magnitudeImageShared = sa.create(
        "shm://" + magnitudeImageFile, 
        magnitudeImage.shape)

    distanceImageShared = sa.create(
        "shm://" + distanceImageFile, 
        distanceImage.shape)
    
    decodedImageShared[:]     = decodedImage[:]
    probabilityImageShared[:] = probabilityImage[:]
    distanceImageShared[:]    = distanceImage[:]
    magnitudeImageShared[:]   = magnitudeImage[:]
    
    with mp.Pool(numCores) as process:
        barcodes = pd.concat(process.starmap(
            extract_barcodes_by_indexes, 
            [ ( decodedImageFile, probabilityImageFile, 
            distanceImageFile, magnitudeImageFile,  \
            np.arange(j, j + barcodesPerCore)) \
            for j in np.arange(
                0, decodedImage.max() + 1, 
                barcodesPerCore) ]))

    sa.delete(decodedImageFile)
    sa.delete(probabilityImageFile)
    sa.delete(distanceImageFile)
    sa.delete(magnitudeImageFile)
    return barcodes

def extract_barcodes_by_indexes(
    decodedImageName: str = None, 
    probImageName: str = None,
    distImageName: str = None,
    magImageName: str = None,
    barcodeIndexes: np.ndarray = None
    ) -> pd.core.frame.DataFrame:
    
    o = sa.attach(decodedImageName)
    p = sa.attach(probImageName)
    m = sa.attach(magImageName)
    d = sa.attach(distImageName)

    propertiesO = measure.regionprops(
        measure.label(np.isin(o, barcodeIndexes)),
        intensity_image=o,
        cache=False)

    propertiesP = measure.regionprops(
        measure.label(np.isin(o, barcodeIndexes)),
        intensity_image=p,
        cache=False)

    propertiesD = measure.regionprops(
        measure.label(np.isin(o, barcodeIndexes)),
        intensity_image=d,
        cache=False)

    propertiesM = measure.regionprops(
        measure.label(np.isin(o, barcodeIndexes)),
        intensity_image=m,
        cache=False)
    
    if len(propertiesO) == 0:
        return pd.DataFrame(columns = 
            ["x", "y", "barcode_id", 
            "likelihood", "magnitude", 
            "distance", "area"])
    else:
        barcodeIDs = np.array(
            [prop.min_intensity for prop in propertiesO])
        
        centroidCoords = np.array(
            [prop.weighted_centroid for prop in propertiesP])

        centroids = centroidCoords[:, [1, 0]]              

        areas = np.array(
            [ x.area for x in propertiesP ]).astype(np.float)

        liks = np.array([ 
            -sum(np.log10(1 - x.intensity_image[x.image])) \
            for x in propertiesP ]
            ).astype(np.float32)
        
        mags = np.array([ 
            x.mean_intensity \
            for x in propertiesM ]
            ).astype(np.float32)

        dists = np.array([ 
            x.mean_intensity \
            for x in propertiesD ]
            ).astype(np.float32)
        
        return pd.DataFrame({
            "x": centroids[:,0],
            "y": centroids[:,1],
            "barcode_id": barcodeIDs,
            "likelihood": liks,
            "magnitude": mags,
            "distance": dists,
            "area": areas})

def calc_barcode_fdr(b, cb):
    blanks = b[b.barcode_id.isin(cb.get_blank_indexes())]
    blanksNum = blanks.shape[0]
    totalNum = b.shape[0] + 1 # add psudo count
    fdr = (blanksNum / len(cb.get_blank_indexes())) / (totalNum / cb.get_barcode_count())
    return fdr

def estimate_lik_err_table(
    bd, cb, minScore=0, maxScore=10, bins=100):
    scores = np.linspace(minScore, maxScore, bins)
    blnkBarcodeNum = len(cb.get_blank_indexes())
    codeBarcodeNum = len(cb.get_coding_indexes()) + len(cb.get_blank_indexes())
    pvalues = dict()
    for s in scores:
        bd = bd[bd.likelihood >= s]
        numPos = np.count_nonzero(
            bd.barcode_id.isin(cb.get_coding_indexes()))
        numNeg = np.count_nonzero(
            bd.barcode_id.isin(cb.get_blank_indexes()))
        numNegPerBarcode = numNeg / blnkBarcodeNum
        numPosPerBarcode = (numPos + numNeg) / codeBarcodeNum
        pvalues[s] = numNegPerBarcode / numPosPerBarcode
    return pvalues

def estimate_barcode_threshold(
    barcodes,
    codebook,
    cutoff: float = 0.05,
    bins: int = 100):

    tab = estimate_lik_err_table(
        barcodes, 
        codebook, 
        minScore=0, 
        maxScore=10, 
        bins=bins)
    
    return min(np.array(list(tab.keys()))[
        np.array(list(tab.values())) <= cutoff])

def export_barcodes(
    obj,
    fnames: list = None):

    barcodes = []
    for fname in fnames:
        x = pd.read_hdf(fname, key="barcodes")
        x = x.assign(global_x = np.array(x.x * obj.get_microns_per_pixel()) +\
            np.array(obj.get_fov_offset(x.fov)[0]))
        x = x.assign(global_y = np.array(x.y * obj.get_microns_per_pixel()) +\
            np.array(obj.get_fov_offset(x.fov)[1]))
        x = x.assign(gene_name = \
            np.array(obj.get_codebook().get_data()["name"][
                x.barcode_id.astype(int)]))
        barcodes.append(x)

    # combine barcodes
    barcodes = pd.concat(
        barcodes, ignore_index = True)

    return barcodes
    
def filter_barcodes(barcodes,
                    codebook,
                    likelihoodThreshold: float = None,
                    keepBlankBarcodes: bool = False,
                    minAreaSize: int = 1):
    
    barcodes = barcodes[barcodes.likelihood >= likelihoodThreshold]
    barcodes = barcodes[barcodes.area >= minAreaSize]
    if not keepBlankBarcodes:
        barcodes = barcodes[
            barcodes.barcode_id.isin(codebook.get_coding_indexes())]
    return barcodes   
