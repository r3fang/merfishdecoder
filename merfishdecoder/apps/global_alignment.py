import numpy as np
import merfishdecoder
from merfishdecoder import dataset

class SimpleGlobalAlignment():

    """A global alignment that uses the theoretical stage positions in
    order to determine the relative positions of each field of view.
    """

    def __init__(self, dataSet, parameters=None, analysisName=None):
        self.dataSet = dataSet

    def fov_coordinates_to_global(self, fov, fovCoordinates):
        fovStart = self.dataSet.get_fov_offset(fov)
        micronsPerPixel = self.dataSet.get_microns_per_pixel()
        if len(fovCoordinates) == 2:
            return (fovStart[0] + fovCoordinates[0]*micronsPerPixel,
                    fovStart[1] + fovCoordinates[1]*micronsPerPixel)
        elif len(fovCoordinates) == 3:
            zPositions = self.dataSet.get_z_positions()
            return (np.interp(fovCoordinates[0], np.arange(len(zPositions)),
                              zPositions),
                    fovStart[0] + fovCoordinates[1]*micronsPerPixel,
                    fovStart[1] + fovCoordinates[2]*micronsPerPixel)

    def fov_coordinate_array_to_global(self, fov: int,
                                       fovCoordArray: np.array) -> np.array:
        tForm = self.fov_to_global_transform(fov)
        toGlobal = np.ones(fovCoordArray.shape)
        toGlobal[:, [0, 1]] = fovCoordArray[:, [1, 2]]
        globalCentroids = np.matmul(tForm, toGlobal.T).T[:, [2, 0, 1]]
        globalCentroids[:, 0] = fovCoordArray[:, 0]
        return globalCentroids

    def fov_global_extent(self, fov: int):
        """
        Returns the global extent of a fov, output interleaved as
        xmin, ymin, xmax, ymax

        Args:
            fov: the fov of interest
        Returns:
            a list of four floats, representing the xmin, xmax, ymin, ymax
        """

        return [x for y in (self.fov_coordinates_to_global(fov, (0, 0)),
                            self.fov_coordinates_to_global(fov, (2048, 2048)))
                for x in y]

    def global_coordinates_to_fov(self, fov, globalCoordinates):
        tform = np.linalg.inv(self.fov_to_global_transform(fov))

        def convert_coordinate(coordinateIn):
            coords = np.array([coordinateIn[0], coordinateIn[1], 1])
            return np.matmul(tform, coords).astype(int)[:2]
        pixels = [convert_coordinate(x) for x in globalCoordinates]
        return pixels

    def fov_to_global_transform(self, fov):
        micronsPerPixel = self.dataSet.get_microns_per_pixel()
        globalStart = self.fov_coordinates_to_global(fov, (0, 0))

        return np.float32([[micronsPerPixel, 0, globalStart[0]],
                           [0, micronsPerPixel, globalStart[1]],
                           [0, 0, 1]])

    def get_global_extent(self):
        fovSize = self.dataSet.get_image_dimensions()
        fovBounds = [self.fov_coordinates_to_global(x, (0, 0))
                     for x in self.dataSet.get_fovs()] + \
                    [self.fov_coordinates_to_global(x, fovSize)
                     for x in self.dataSet.get_fovs()]

        minX = np.min([x[0] for x in fovBounds])
        maxX = np.max([x[0] for x in fovBounds])
        minY = np.min([x[1] for x in fovBounds])
        maxY = np.max([x[1] for x in fovBounds])

        return minX, minY, maxX, maxY
