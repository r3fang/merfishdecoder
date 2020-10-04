import cv2
import numpy as np

from merfishdecoder.core import zplane


def scale_readout_images(obj: zplane.Zplane = None, 
                         frameNames: list = None,
                         scaleFactors: dict = None,
                         ) -> zplane.Zplane:

    """

    Correct the intensity difference between color channels
               using existed scale factor profiles

    """
    frameNames = obj.get_readout_name() \
        if frameNames is None else frameNames
    if scaleFactors is None:
        scaleFactors = estimate_scale_factors(
            obj, frameNames)
    for fn in frameNames:
        obj._frames[fn]._img = obj._frames[fn]._img.astype(np.float16) / scaleFactors[fn]
    return obj

def estimate_scale_factors(obj: zplane.Zplane = None, 
                           frameNames: list = None
                           ) -> dict:

    """
    Estimate scale factors between rounds of images.
    """

    frameNames = obj.get_readout_name() \
        if frameNames is None else frameNames

    return dict(zip(frameNames,
        [ np.median(x[x > 0]) for x in 
        obj.get_readout_images(frameNames) ]))


