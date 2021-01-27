import os
import glob
import collections
import pickle

import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
import matplotlib.pyplot as plt 
from sklearn.linear_model import LogisticRegression

from merfishdecoder.core import dataset
from merfishdecoder.util import utilities

def run_job(dataSetName: str = None,
            workDir: str = "extractedPixelTraces",
            distanceThreshold: float = 0.6,
            outputName: str = None):

    """
    Estimate prior distribution for each round of image.

    Args
    ----
    dataSetName: input dataset name.
    
    workDir: work directory that contains extracted pixel traces.

    distanceThreshold: distance cutoff for pixels.
    
    outputName: output name that stores model parameters.
             
    """

    utilities.print_checkpoint("Estimate Prior")
    utilities.print_checkpoint("Start")

    # create dataSet object
    dataSet = dataset.MERFISHDataSet(dataSetName)
    cb = dataSet.get_codebook()
    
    # change to work directory
    os.chdir(dataSet.analysisPath)
    
    # list the extracted pixels
    pixelTraces = pd.concat([ 
        pd.read_hdf(fn) \
        for fn in glob.glob(workDir + "/*.h5") ],
        axis = 0)
    
    # filter decoded pixels
    pixelTraces = pixelTraces[
        pixelTraces.distance <= distanceThreshold]
    
    # estimate foreground
    cb = dataSet.get_codebook()
    cbMat = cb.get_barcodes()[pixelTraces.barcode_id,:]
    pixelTracesExp = np.array(pixelTraces[cb.get_bit_names()])
    modelDict = collections.defaultdict()
    plt.clf()
    for i in range(cb.get_bit_count()):
        pixelOneBit = pixelTracesExp[cbMat[:,i] > 0, i]
        pixelOneBit = np.log10(pixelOneBit[pixelOneBit > 0] + 1)
        #plt.hist(pixelOneBit, bins=100)
        gm = GaussianMixture(
            n_components=2,
            random_state=0,
            n_init=1,
            init_params="kmeans",
            covariance_type="spherical",
            warm_start=True,
            means_init = np.array([[0.5], [1.5]])
        ).fit(pixelOneBit.reshape(-1, 1))
        y = gm.predict(pixelOneBit.reshape(-1, 1))
        X = pixelOneBit.reshape(-1, 1)
        clf = LogisticRegression(random_state=0).fit(X, y)
        modelDict[cb.get_bit_names()[i]] = clf
        plt.scatter(X, clf.predict_proba(X)[:,1], s=0.5)
    pickle.dump(modelDict, open(outputName, 'wb'))
    plt.xlabel("log10(magnitude)")
    plt.ylabel("probability")
    plt.savefig("modelCurve")
    # estimate background
    utilities.print_checkpoint("Done")

def main():
    dataSetName = "191010_LMN7_DIV18_Map2Tau"
    workDir = "extractedPixelTraces"
    distanceThreshold = 0.6
    outputName = "gmModelParam.v2.pkl"

    run_job(dataSetName = dataSetName,
            workDir = workDir,
            distanceThreshold = distanceThreshold,
            outputName = outputName)

