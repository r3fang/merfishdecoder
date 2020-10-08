import argparse
import os, sys
import pickle
import pandas as pd
import numpy as np
import geopandas as geo

from merfishdecoder.core import zplane
from merfishdecoder.util import registration
from merfishdecoder.util import preprocessing
from merfishdecoder.util import imagefilter
from merfishdecoder.util import utilities
from merfishdecoder.util import decoder
from merfishdecoder.util import barcoder
from merfishdecoder.util import segmentation

def main():
    parser = argparse.ArgumentParser(description='MERFISH Analysis.')
    
    parser_req = parser.add_argument_group("required inputs")
    parser_req.add_argument("--data-set-name",
                             type=str,
                             required=True,
                             help="MERFISH dataset name.")

    parser_req.add_argument("--fov",
                             type=int,
                             required=True,
                             help="Field of view.")

    parser_req.add_argument("--zpos",
                             type=float,
                             required=True,
                             help="Z plane.")
    
    parser_req.add_argument("--psm-name",
                            type=str,
                            required=True,
                            help="Pixel scoring machine name.")

    parser_opt = parser.add_argument_group("optional inputs")
    parser_opt.add_argument("--ref-frame-index",
                            type=int,
                            default=0,
                            help="Reference frame index for correcting drift.")

    parser_opt.add_argument("--high-pass-filter-sigma",
                            type=int,
                            default=3,
                            help="Low pass sigma for high pass filter prior to registration.")

    parser_opt.add_argument("--border-size",
                             type=int,
                             default=80,
                             help="Number of pixels to be ignored from the border.")

    parser_opt.add_argument("--magnitude-threshold",
                             type=float,
                             default=0,
                             help="Threshold for pixel magnitude.")

    parser_opt.add_argument("--distance-threshold",
                            type=float,
                            default=0.6,
                            help="Threshold between pixel trace and closest barcode.")
    
    parser_opt.add_argument("--barcodes-per-core",
                            type=int,
                            default=10,
                            help="Number of barcodes to be decoded per core.")

    parser_opt.add_argument("--max-cores",
                            type=int,
                            default=1,
                            help="Max number of CPU cores.")
    
    args = parser.parse_args()

    dataSetName = args.data_set_name
    fov = args.fov
    zpos = args.zpos
    psmName = args.psm_name
    maxCores = args.max_cores
    
    refFrameIndex = args.ref_frame_index
    highPassFilterSigma = args.high_pass_filter_sigma

    borderSize = args.border_size
    magnitudeThreshold = args.magnitude_threshold
    distanceThreshold = args.distance_threshold
    barcodesPerCore = args.barcodes_per_core

    modelType_DAPI = "nuclei"
    modelType_polyT = "cyto"
    diameter_DAPI = 150
    diameter_polyT = 200

    utilities.print_checkpoint("Start MEFISH Analysis")
    prefix = "fov_%d_zpos_%0.1f" % (fov, zpos)
    
    # generate zplane object
    zp = zplane.Zplane(dataSetName,
                       fov=fov,
                       zpos=zpos)
    
    # load the score machine
    psm = pickle.load(open(psmName, "rb"))
    
    # create the folder
    os.makedirs("extractedBarcodes", exist_ok=True)
    os.makedirs("extractedFeatures", exist_ok=True)
    
    utilities.print_checkpoint("Load Readout Images")
    # load readout images
    zp.load_readout_images(
        zp.get_readout_name())
    
    utilities.print_checkpoint("Correct Stage Drift")
    (zp, errors) = registration.correct_drift(
        obj = zp,
        refFrameIndex = refFrameIndex,
        highPassSigma = highPassFilterSigma)
    
    utilities.print_checkpoint("Correct Chromatic Abeeration")
    profile = zp.get_chromatic_aberration_profile()

    zp = registration.correct_chromatic_aberration(
        obj = zp,
        profile = profile)
    
    utilities.print_checkpoint("Remove Cell Background")
    zp = imagefilter.high_pass_filter(
         obj = zp,
         frameNames = zp.get_bit_name(),
         readoutImage = True,
         fiducialImage = False,
         sigma = highPassFilterSigma)
        
    utilities.print_checkpoint("Adjust Illumination")
    scaleFactors = preprocessing.estimate_scale_factors(
        obj = zp,
        frameNames = zp.get_bit_name())
            
    # normalize image intensity
    zp = preprocessing.scale_readout_images(
        obj = zp,
        frameNames = zp.get_bit_name(),
        scaleFactors = scaleFactors)

    utilities.print_checkpoint("Pixel-based Decoding")
    decodedImages = decoder.decoding(
             obj = zp,
             movie = zp.get_readout_images(zp.get_bit_name()),
             borderSize = borderSize,
             distanceThreshold = distanceThreshold,
             magnitudeThreshold = magnitudeThreshold,
             numCores = maxCores)
    
    utilities.print_checkpoint("Extract Barcodes")
    if decodedImages["decodedImage"].max() > -1:
        # calculate pixel probability
        decodedImages["probabilityImage"] = \
            decoder.calc_pixel_probability(
                model = psm,
                decodedImage = decodedImages["decodedImage"],
                magnitudeImage = decodedImages["magnitudeImage"],
                distanceImage = decodedImages["distanceImage"],
                minProbability = 0.01)
        
        barcodes = barcoder.extract_barcodes(
            decodedImage = decodedImages["decodedImage"],
            distanceImage = decodedImages["distanceImage"],
            probabilityImage = decodedImages["probabilityImage"],
            magnitudeImage = decodedImages["magnitudeImage"],
            barcodesPerCore = barcodesPerCore,
            numCores = maxCores)

        # extract barcodes
        barcodes = barcodes.assign(fov = fov) 
        barcodes = barcodes.assign(global_z = zpos) 
        barcodes = barcodes.assign(z = \
            zp._dataSet.get_z_positions().index(zpos))
    else:
        barcodes = pd.DataFrame([],
            columns=['x', 'y', 'barcode_id', 'likelihood', 
            'magnitude', 'distance', 'area', 'fov', 'global_z', 'z'])

    # save barcodes
    barcodes.to_hdf("extractedBarcodes/%s.h5" % prefix,
                    key = "barcodes")
    
    utilities.print_checkpoint("Segment Images DAPI")
    segmentedImage = segmentation.run_cell_pose(
        gpu = False,
        modelType = modelType_DAPI,
        images = [ zp.get_readout_images(["DAPI"])[0] ],
        diameter = diameter_DAPI
        )[0] 
        
    utilities.print_checkpoint("Extract Features DAPI")
    ft = [ (idx, segmentation.extract_polygon_per_index(segmentedImage, idx)) \
        for idx in np.unique(segmentedImage[segmentedImage > 0]) ]
    ft = [ (i, x) for (i, x) in ft if x != None ]

    # convert to a data frame
    if len(ft) > 0:
        features = geo.GeoDataFrame(
            pd.DataFrame({
                "fov": [fov] * len(ft),
                "global_z": [zpos] * len(ft),
                "z": zp._dataSet.get_z_positions().index(zpos)}),
            geometry=[x[1] for x in ft])
    else:
        features = geo.GeoDataFrame(
            pd.DataFrame(
                columns = ["fov", "global_z", "z", "x", "y"]), 
                geometry=None)
    
    if not features.empty:
        features = features.assign(x = features.centroid.x)
        features = features.assign(y = features.centroid.y)
        features.to_file("extractedFeatures/%s_DAPI.shp" % prefix)
    else:
        with open("extractedFeatures/%s_DAPI.shp" % prefix, 'w') as fp: 
            pass

    utilities.print_checkpoint("Segment Images polyT")
    segmentedImage = segmentation.run_cell_pose(
        gpu = False,
        modelType = modelType_polyT,
        images = [ zp.get_readout_images(["polyT"])[0] ],
        diameter = diameter_polyT
        )[0] 
        
    utilities.print_checkpoint("Extract Features polyT")
    ft = [ (idx, segmentation.extract_polygon_per_index(segmentedImage, idx)) \
        for idx in np.unique(segmentedImage[segmentedImage > 0]) ]
    ft = [ (i, x) for (i, x) in ft if x != None ]

    # convert to a data frame
    if len(ft) > 0:
        features = geo.GeoDataFrame(
            pd.DataFrame({
                "fov": [fov] * len(ft),
                "global_z": [zpos] * len(ft),
                "z": zp._dataSet.get_z_positions().index(zpos)}),
            geometry=[x[1] for x in ft])
    else:
        features = geo.GeoDataFrame(
            pd.DataFrame(
                columns = ["fov", "global_z", "z", "x", "y"]), 
                geometry=None)
    
    if not features.empty:
        features = features.assign(x = features.centroid.x)
        features = features.assign(y = features.centroid.y)
        features.to_file("extractedFeatures/%s_polyT.shp" % prefix)
    else:
        with open("extractedFeatures/%s_polyT.shp" % prefix, 'w') as fp: 
            pass

    utilities.print_checkpoint("Done")

if __name__ == "__main__":
    main()
