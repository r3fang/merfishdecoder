import os
import pickle
import pandas as pd
import numpy as np

from merfishdecoder.core import zplane
from merfishdecoder.util import utilities
from merfishdecoder.util import barcoder
from merfishdecoder.util import decoder

def run_job_old(dataSetName: str = None,
            fov: int = None,
            zpos: float = None,
            processedImagesName: str = None,
            decodedImagesName: str = None,
            outputName: str = None):

    utilities.print_checkpoint("Extract Pixel Traces")
    utilities.print_checkpoint("Start")

    # generate zplane object
    zp = zplane.Zplane(dataSetName,
                       fov=fov,
                       zpos=zpos)

    # create the folder
    os.makedirs(os.path.dirname(outputName),
                exist_ok=True)
    
    # load decoded images
    f = np.load(decodedImagesName)
    decodedImages = {
        "decodedImage": f["decodedImage"],
        "magnitudeImage": f["magnitudeImage"],
        "distanceImage": f["distanceImage"]}
    f.close()

    # load processed images
    f = np.load(processedImagesName)
    procesedImages = f[f.files[0]]
    f.close()
    
    # extract pixels
    idx = np.where(decodedImages["decodedImage"] > -1)
    pixelTraces = procesedImages[:,idx[0], idx[1]].T
    barcode_id = decodedImages["decodedImage"][idx[0], idx[1]]
    distances = decodedImages["distanceImage"][idx[0], idx[1]]
    magnitudes = decodedImages["magnitudeImage"][idx[0], idx[1]]
    dat = pd.DataFrame(pixelTraces, columns =  zp.get_bit_name())
    dat = dat.assign(barcode_id = barcode_id)
    dat = dat.assign(distance = distances)
    dat = dat.assign(magnitudes = magnitudes)
    dat = dat.assign(x = idx[0])
    dat = dat.assign(y = idx[1])

    dat[["x", "y", "barcode_id", "distance", "magnitudes"] + \
        zp.get_bit_name()].to_hdf(
        outputName, key= "pixelTraces", index=False)

    utilities.print_checkpoint("Done")

def run_job(dataSetName: str = None,
            fov: int = None,
            zpos: float = None,
            processedImagesName: str = None,
            extractedBarcodesName: str = None,
            decodedImagesName: str = None,
            outputName: str = None,
            areaSizeThreshold: int = 5,
            magnitudeThreshold: float = 1,
            distanceThreshold: float = 0.65):

    utilities.print_checkpoint("Extract Pixel Traces")
    utilities.print_checkpoint("Start")

    # generate zplane object
    zp = zplane.Zplane(dataSetName,
                       fov=fov,
                       zpos=zpos)

    # create the folder
    os.makedirs(os.path.dirname(outputName),
                exist_ok=True)
    
    # load decoded images
    barcodes = pd.read_hdf(extractedBarcodesName)
    
    # filter barcodes
    barcodes = barcodes[
        (barcodes.area >= areaSizeThreshold) & \
        (barcodes.magnitude >= magnitudeThreshold) & \
        (barcodes.distance <= distanceThreshold)
    ]

    # create decoded image
    maskImage = np.zeros(zp.get_image_size())
    for index, row in barcodes.iterrows():
        maskImage[
            int(row['x_start']):int(row['x_end']),
            int(row['y_start']):int(row['y_end'])] = 1
    
    # load decoded images
    f = np.load(decodedImagesName)
    decodedImages = {
        "decodedImage": f["decodedImage"],
        "magnitudeImage": f["magnitudeImage"],
        "distanceImage": f["distanceImage"]}
    f.close()
    maskImage[decodedImages["decodedImage"] == -1] = 0
    decodedImages["maskImage"] = maskImage
    
    # load processed images
    f = np.load(processedImagesName)
    procesedImages = f[f.files[0]]
    f.close()
    
    # extract pixels
    idx = np.where(decodedImages["maskImage"] == 1)
    pixelTraces = procesedImages[:,idx[0], idx[1]].T
    barcode_id = decodedImages["decodedImage"][idx[0], idx[1]]
    distances = decodedImages["distanceImage"][idx[0], idx[1]]
    magnitudes = decodedImages["magnitudeImage"][idx[0], idx[1]]
    dat = pd.DataFrame(pixelTraces, columns =  zp.get_bit_name())
    dat = dat.assign(barcode_id = barcode_id)
    dat = dat.assign(distance = distances)
    dat = dat.assign(magnitudes = magnitudes)
    dat = dat.assign(x = idx[0])
    dat = dat.assign(y = idx[1])

    dat[["x", "y", "barcode_id", "distance", "magnitudes"] + \
        zp.get_bit_name()].to_hdf(
        outputName, key= "pixelTraces", index=False)

    utilities.print_checkpoint("Done")

def main():
    dataSetName = "191010_LMN7_DIV18_Map2Tau"
    fov = 188
    zpos = 5.0
    areaSizeThreshold = 5
    magnitudeThreshold = 0
    distanceThreshold = 0.65
    extractedBarcodesName = "extractedBarcodes/fov_188_zpos_5.0.h5"
    processedImagesName = "processedImages/fov_188_zpos_5.0.npz"
    decodedImagesName = "decodedImages/fov_188_zpos_5.0.npz"
    outputName = "extractedPixelTraces/fov_188_zpos_5.0.h5"

    run_job(dataSetName = dataSetName,
            fov = fov,
            zpos = zpos,
            extractedBarcodesName = extractedBarcodesName,
            processedImagesName = processedImagesName,
            decodedImagesName = decodedImagesName,
            outputName = outputName,
            areaSizeThreshold = areaSizeThreshold,
            magnitudeThreshold = magnitudeThreshold,
            distanceThreshold = distanceThreshold)

if __name__ == "__main__":
    main()



