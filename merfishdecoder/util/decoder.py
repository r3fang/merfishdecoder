import pandas as pd
import numpy as np
import gc
from numpy import linalg as LA
import random
import cv2
import copy
from sklearn.neighbors import NearestNeighbors
import multiprocessing as mp
import SharedArray as sa
from skimage import measure
import tempfile
import os
from collections import Counter
from numba import jit
import gc

from merfishdecoder.data import codebook as cb
from merfishdecoder.util import utilities
from merfishdecoder.core import zplane

def decoding(obj: zplane.Zplane = None,
             movie: np.ndarray = None,
             borderSize: int = 80,
             distanceThreshold: float = 0.65,
             magnitudeThreshold: float = 0.0,
             numCores: int = 1):

    """
    Pixel-based decoding.

    Args
    ----
    dataSetName: input dataset name.
    
    decodingMovieFile: movie for decoding.

    numCores: number of processors for parallel computing. 
             
    magnitudeThreshold: the min magnitudes for a pixel to be decoded.
             Any pixel with magnitudes less than magnitudeThreshold 
             will be filtered prior to the decoding.
             
    distanceThreshold: the maximum distance between an assigned pixel
             and the nearest barcode. Pixels for which the nearest barcode
             is greater than distanceThreshold are left unassigned.

    """

    # remove the bordering pixels of decoding movie
    imageSize = movie.shape[1:]
    borderImage = np.ones(imageSize)
    borderImage[
        borderSize:(imageSize[0] - borderSize),
        borderSize:(imageSize[0] - borderSize)] = 0
    movie = np.array([ x * (1 - borderImage) for x in movie ])
    
    # normalized codebook matrix
    codebookMatWeighted = obj.get_codebook().get_barcodes().astype(np.float32)
    bitNum = codebookMatWeighted.sum(axis=1)[0]
    codebookMatWeighted = codebookMatWeighted / \
        cal_pixel_magnitude(codebookMatWeighted)[:, None]
    
    # pixel-based decoding
    decodeDict = pixel_based_decode(
        movie = movie,
        codebookMat = codebookMatWeighted,
        distanceThreshold = distanceThreshold,
        magnitudeThreshold = magnitudeThreshold,
        oneBitThreshold = bitNum - 1,
        numCores = numCores)
    return decodeDict

@jit(nopython=True)
def cal_pixel_magnitude(x):

    """
    Calculate magnitude for pixel trace x 
    """

    pixelMagnitudes = np.array([ np.linalg.norm(x[i]) \
        for i in range(x.shape[0]) ], dtype=np.float32)
    pixelMagnitudes[pixelMagnitudes == 0] = 1 
    return(pixelMagnitudes)  

def kneighbors_func(x, n):
    return(n.kneighbors(
        x, return_distance=True))

def pixel_based_decode(
    movie: np.ndarray,
    codebookMat: np.ndarray,
    numCores: int = 1,
    distanceThreshold: float = 0.65,
    magnitudeThreshold: float = 0,
    oneBitThreshold: int = 3
    ) -> dict:
  
    """
    NOTE: THIS FUNCTION IS COPIED/MODIFIED FROM MERLIN
    https://github.com/emanuega/MERlin
    
    Purpose:
           Assign barcodes to the pixels in the provided image stock.
           Each pixel is assigned to the nearest barcode from the codebook if
           the distance between the normalized pixel trace and the barcode is
           less than the distance threshold.
    Args:
        movie: input image stack. The first dimension indexes the bit
            number and the second and third dimensions contain the
            corresponding image.
           
        codebook: a codebook object that contains the barcode for MERFISH.
            A valid codebook should contains both gene and blank batcodes.
        
        distanceThreshold: the maximum distance between an assigned pixel
            and the nearest barcode. Pixels for which the nearest barcode
            is greater than distanceThreshold are left unassigned.

        magnitudeThreshold: the minimum magnitude for a pixel. Pixels for 
            which magnitude is smaller than magnitudeThreshold are left unassigned.
            Note that the magnitude is scaled by the median value of each bit.

        numCores: number of processors used for decoding
        
    Returns:
        A dictionary object contains the following images:
            decodedImage - assigned barcode id
            magnitudeImage - magnitude for the pixel
            distanceImage - min dsitance to the closest barcode
            
    """
    
    imageSize = movie.shape[1:]
    
    pixelTraces = np.reshape(
        movie, 
        (movie.shape[0], 
        np.prod(movie.shape[1:]))).T
    numPixel = pixelTraces.shape[0]
    
    pixelMagnitudes = cal_pixel_magnitude(
        pixelTraces.astype(np.float32))
    
    pixelTracesCov = np.array(
        [np.count_nonzero(x) for x in pixelTraces])

    pixelIndexes = np.where(
        (pixelTracesCov >= oneBitThreshold) &
        (pixelMagnitudes >= magnitudeThreshold))[0]
    
    if pixelIndexes.shape[0] == 0:
        return dict({
            "decodedImage": np.empty(0),
            "magnitudeImage": np.empty(0),
            "distanceImage": np.empty(0)})

    pixelTraces = pixelTraces[pixelIndexes]
    pixelMagnitudes = pixelMagnitudes[pixelIndexes]
    
    normalizedPixelTraces = \
        pixelTraces / pixelMagnitudes[:, None]
    
    del pixelTraces
    del pixelTracesCov
    gc.collect()
    
    neighbors = NearestNeighbors(
        n_neighbors = 1, 
        algorithm = 'ball_tree')
    
    neighbors.fit(codebookMat)
    
    if numCores > 1:
        normalizedPixelTracesSplits = np.array_split(
            normalizedPixelTraces, 100)
        with mp.Pool(processes=numCores) as pool:
            results = pool.starmap(kneighbors_func, 
                zip(normalizedPixelTracesSplits, [neighbors] * 100))
        distances = np.vstack([ x[0] for x in results ])
        indexes = np.vstack([ x[1] for x in results ])
    else:
        results = kneighbors_func(
            normalizedPixelTraces, neighbors)
        distances = results[0]
        indexes = results[1]

    del normalizedPixelTraces
    gc.collect()
    pixelTracesDecoded = -np.ones(
        numPixel, 
        dtype=np.int16)

    pixelTracesDecoded[pixelIndexes] = \
        np.array([i if ( d <= distanceThreshold ) else -1
              for i, d in zip(indexes, distances)], 
        dtype=np.int16)
    
    decodedImage = np.reshape(
       pixelTracesDecoded,
       imageSize)
    
    pixelDistanceTraces = np.ones(
        numPixel, 
        dtype=np.float32
        ) * distanceThreshold
    
    pixelDistanceTraces[pixelIndexes] = \
        np.ravel(distances)
    
    distanceImage = np.reshape(
       pixelDistanceTraces,
       imageSize)
        
    pixelMagnitudeTraces = np.zeros(
        numPixel, 
        dtype=np.float32)

    pixelMagnitudeTraces[pixelIndexes] = \
        np.ravel(pixelMagnitudes)
    
    magnitudeImage = np.reshape(
       pixelMagnitudeTraces,
       imageSize)

    return dict({
        "decodedImage": decodedImage,
        "magnitudeImage": magnitudeImage,
        "distanceImage": distanceImage})

def calc_pixel_probability(
    model,
    decodedImage:   np.ndarray = None,
    magnitudeImage: np.ndarray = None,
    distanceImage:  np.ndarray = None,
    minProbability: float = 0.01):
    
    m = np.log10(magnitudeImage[decodedImage > -1]+1)
    d = distanceImage[decodedImage > -1]
    p = model.predict_proba(
        np.array([m, d]).T)[:,1]
    probabilityImage = np.zeros(decodedImage.shape) + minProbability
    probabilityImage[decodedImage > -1] = p
    return probabilityImage

