import os
import pandas as pd
import numpy as np
import geopandas as geo
import sys
from shapely import geometry
from shapely.geometry import Polygon
from merfishdecoder.core import dataset

def alpha_shape(points, alpha):
    """
    Compute the alpha shape (concave hull) of a set
    of points.
    @param points: Iterable container of points.
    @param alpha: alpha value to influence the
        gooeyness of the border. Smaller numbers
        don't fall inward as much as larger numbers.
        Too large, and you lose everything!
    """
    
    from shapely.ops import cascaded_union, polygonize
    from scipy.spatial import Delaunay
    import numpy as np
    import math
    
    
    if len(points) < 4:
        # When you have a triangle, there is no sense
        # in computing an alpha shape.
        return geometry.MultiPoint(list(points)).convex_hull

    def add_edge(edges, edge_points, coords, i, j):
        """
        Add a line between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in edges or (j, i) in edges:
            # already added
            return
        edges.add( (i, j) )
        edge_points.append(coords[ [i, j] ])

    coords = np.array([point.coords[0] for point in points])

    tri = Delaunay(coords)
    edges = set()
    edge_points = []
    for ia, ib, ic in tri.vertices:
        pa = coords[ia]
        pb = coords[ib]
        pc = coords[ic]
        # Lengths of sides of triangle
        a = math.sqrt((pa[0]-pb[0])**2 + (pa[1]-pb[1])**2)
        b = math.sqrt((pb[0]-pc[0])**2 + (pb[1]-pc[1])**2)
        c = math.sqrt((pc[0]-pa[0])**2 + (pc[1]-pa[1])**2)
        # Semiperimeter of triangle
        s = (a + b + c)/2.0
        # Area of triangle by Heron's formula
        area = math.sqrt(s*(s-a)*(s-b)*(s-c))
        circum_r = a*b*c/(4.0*area)
        # Here's the radius filter.
        #print circum_r
        if circum_r < 1.0/alpha:
            add_edge(edges, edge_points, coords, ia, ib)
            add_edge(edges, edge_points, coords, ib, ic)
            add_edge(edges, edge_points, coords, ic, ia)
    m = geometry.MultiLineString(edge_points)
    triangles = list(polygonize(m))
    return cascaded_union(triangles), edge_points
    
def generate_density_mask(
    dataSet, bd, radius = 1.2):

    X = np.array(
        bd[["global_x", "global_y", "global_z"]])

    neigh = NearestNeighbors(
        radius = radius)
    
    distances, indexes = neigh.radius_neighbors(X)
    density = [ x.shape[0] for x in indexes ]
    
    neigh.fit(X)
    imageSizes = dataSet.get_image_dimensions()

    Y = np.array([(y,x) for x in range(imageSizes[0]) \
        for y in range(imageSizes[1])])

    distances, indexes = neigh.radius_neighbors(Y)
    img = np.array([ 
        x.shape[0] for x in indexes 
        ]).reshape(imageSizes)
    return img

def read_barcodes_per_fov(
    fname: str = None,
    fov: int = None):
    try:
        return pd.concat([
            pd.read_hdf(fname, key="fov_%d" % fov) ],
            axis=1)
    except KeyError:
        print("barcodes in fov_%d does not exist" % fov)
        return None

def identify_barcode_cluster_per_fov(
    fname: str = None,
    fov: int = None, 
    minBarcodes = 30,
    radius = 1.2,
    minNeighbours = 10,
    alpha: float = 0.1,
    concaveHullBuffer: float = 0.3):

    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components
    from sklearn.neighbors import NearestNeighbors
    from shapely import geometry
    
    barcodes = read_barcodes_per_fov(fname, fov)
    
    if barcodes is None:
        return geo.GeoDataFrame(
            pd.DataFrame({'fov' : []}), 
            geometry=[])
         
    if barcodes.shape[0] == 0:
        return geo.GeoDataFrame(
            pd.DataFrame({'fov' : []}), 
            geometry=[])
            
    neigh = NearestNeighbors(
        radius = radius)
    neigh.fit(barcodes[["global_x", "global_y", "global_z"]])
    distances, indexes = neigh.radius_neighbors(
        barcodes[["global_x", "global_y", "global_z"]])
    density = np.array([ x.shape[0] for x in indexes ])
    
    rows = []; cols = []
    for i, idx in zip(np.arange(barcodes.shape[0]), indexes):
        if len(idx) > minNeighbours:
            rows.append(np.array([i] * len(idx)))
            cols.append(idx)
    
    if len(rows) == 0:
        labels = -np.ones(barcodes.shape[0])
    else:
        rows = np.concatenate(rows)
        cols = np.concatenate(cols)
        
        graph = csr_matrix((
            np.ones(rows.shape[0]), (rows, cols)), 
            shape=(barcodes.shape[0], barcodes.shape[0]))
        
        n_components, labels = connected_components(
            csgraph= graph, 
            directed=False, 
            return_labels=True)
    
    # partition barcodes to groups
    barcodes = barcodes.assign(
        feature_id = labels)
    
    # remove barcode cluster with count less than 30 barcodes
    (idxes, counts) = np.unique(
        barcodes.feature_id, 
        return_counts=True)

    # remove barcode cluster with count less than 30 barcodes
    barcodes.loc[
        barcodes.feature_id.isin(
        idxes[counts < minBarcodes]), 
        "feature_id"] = -1
    
    # draw boundries
    barcodes = barcodes[barcodes.feature_id > -1]
    polys = []
    for i in np.unique(barcodes.feature_id):
        bd = barcodes[barcodes.feature_id == i]
        points = [geometry.Point(coord[0], coord[1]) \
            for coord in np.array((bd.global_x, bd.global_y)).T]
        concave_hull, edge_points = alpha_shape(points, alpha=alpha)
        polys.append(concave_hull.buffer(concaveHullBuffer))
    
    return geo.GeoDataFrame(
        pd.DataFrame({"fov": [fov] * len(polys)}),
        geometry=polys) # facecolor

def main():
    dataSetName = sys.argv[1]
    barcodeFileName = "filteredBarcodes/barcodes.h5"
    minBarcodes = 30
    radius = 1.2
    minNeighbours = 10
    alpha = 0.1
    concaveHullBuffer = 0.2
    dataSet = dataset.MERFISHDataSet(
            dataSetName)

    # change working directory
    os.chdir(dataSet.analysisPath)
    clusters = pd.concat([ identify_barcode_cluster_per_fov(
        fname = barcodeFileName,
        fov = fov,
        minBarcodes = 50,
        radius = 1.2,
        minNeighbours = 10,
        alpha = 0.1,
        concaveHullBuffer = 0.3) \
    for fov in dataSet.get_fovs() ])

    clusters.to_file(
        filename = "exportedFeatures/clusters.shp")

if __name__ == "__main__":
    main()
