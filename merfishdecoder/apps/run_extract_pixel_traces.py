import os
import pickle
import pandas as pd
import numpy as np

from merfishdecoder.core import zplane
from merfishdecoder.util import utilities
from merfishdecoder.util import barcoder
from merfishdecoder.util import decoder

def run_job(dataSetName: str = None,
            fov: int = None,
            zpos: float = None,
            processedImagesName: str = None,
            decodedImagesName: str = None,
            outputName: str = None):

    # dataSetName = "20200303_hMTG_V11_4000gene_best_sample/data/"
    # fov = 0
    # zpos = 1.0
    # decodedImagesName = "decodedImages/fov_0_zpos_1.0.npz"
    # processedImagesName = "processedImages/fov_0_zpos_1.0.npz"
    # outputName = "extractedPixelTraces/fov_0_zpos_1.0.h5"

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
    
    dat[["barcode_id", "distance", "magnitudes"] + \
        zp.get_bit_name()].to_hdf(
        outputName, key= "pixelTraces", index=False)

    utilities.print_checkpoint("Done")
