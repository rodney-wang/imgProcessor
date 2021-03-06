# coding=utf-8
from __future__ import division

import cv2
import numpy as np

# import imgProcessor as iP
from imgProcessor.transform.linearBlend import linearBlend
from imgProcessor.imgIO import imread
from scipy.optimize.optimize import brent
# from skimage.filters.edges import roberts
# from imgProcessor.filters.fastFilter import fastFilter


class StitchImages(object):

    def __init__(self, img):
        '''
        Find the Overlap between image parts and stitch them at a given edge together.
        There is no perspective correction.
        @param img: the base image
        @param gradient: whether to use image gradient for fitting
        '''
        # TODO: does not work with nan in img. so far
        self.base_img_rgb = imread(img)

    def addImg(self, img, side='bottom', overlap=50, overlapDeviation=0,
               rotation=0, rotationDeviation=0, backgroundColor=None, params=None):
        '''
        @param side: 'left', 'right', 'top', 'bottom', default side is 'bottom'
        @param overlap: overlap guess in pixels of both images
        @param overLapDeviation uncertainty of overlap -> overlap in range(ov-deviation, ov+deviation)
        @param rotation: max. rotational error between images [DEG]
        @param rotationDeviation: same as overLapDeviation, but for rotation [DEG]
        @param backgroundColor: if not None, treat this value as transparent within the stitching area
        '''
        img_rgb = imread(img)

#         if iP.ARRAYS_ORDER_IS_XY:
#             side = {'left': 'top',
#                     'right': 'bottom',
#                     'top': 'left',
#                     'bottom': 'right'}[side]

        # the following algorithm is based on side = 'bottom', so
        if side in ('top', 'left'):
            img_rgb, self.base_img_rgb = self.base_img_rgb, img_rgb

        # rotate images if to be stitched 'left' or 'right'
        if side in ('left', 'right'):
            self.base_img_rgb = np.rot90(self.base_img_rgb, -1)
            img_rgb = np.rot90(img_rgb, -1)
        # check image shape
        assert img_rgb.shape[1] == self.base_img_rgb.shape[
            1], 'image size must be identical in stitch-direction'

        if params is None:
            # find overlap
            params = (offsx, offsy, rot) = self._findOverlap(
                img_rgb, overlap, overlapDeviation, rotation, rotationDeviation)
        else:
            offsx, offsy, rot = params
        img_rgb = self._rotate(img_rgb, rot)

        self._lastParams = params

        # move values in x axis:
        img_rgb = np.roll(img_rgb, offsx)
        # melt both images together
        self.base_img_rgb = linearBlend(
            self.base_img_rgb, img_rgb, offsy, backgroundColor)
        # rotate back if side='left' or 'right'
        if side in ('left', 'right'):
            # self.rotateImage(self.base_img_rgb,-90)
            self.base_img_rgb = np.rot90(self.base_img_rgb, 1)
        return self.base_img_rgb

    @property
    def lastParams(self):
        return self._lastParams

    @staticmethod
    def _rotate(img, angle):
        '''
        angle [DEG]
        '''
        s = img.shape
        if angle == 0:
            return img
        else:
            M = cv2.getRotationMatrix2D((s[1] // 2,
                                         s[0] // 2), angle, 1)
            return cv2.warpAffine(img, M, (s[1], s[0]))

    def _findOverlap(self, img_rgb, overlap, overlapDeviation,
                     rotation, rotationDeviation):
        '''
        return offset(x,y) which fit best self._base_img
        through template matching
        '''
        # get gray images
        if len(img_rgb.shape) != len(img_rgb.shape):
            raise Exception(
                'number of channels(colors) for both images different')
        if overlapDeviation == 0 and rotationDeviation == 0:
            return (0, overlap, rotation)

        s = self.base_img_rgb.shape
        ho = int(round(overlap * 0.5))
        overlap = int(round(overlap))
        # create two image cuts to compare:
        imgcut = self.base_img_rgb[s[0] - overlapDeviation - overlap:, :]
        template = img_rgb[:overlap, ho:s[1] - ho]

        def fn(angle):
            rotTempl = self._rotate(template, angle)
            # Apply template Matching
            fn.res = cv2.matchTemplate(rotTempl.astype(np.float32),
                                       imgcut.astype(np.float32),
                                       cv2.TM_CCORR_NORMED)
            return 1 / fn.res.mean()

        if rotationDeviation == 0:
            angle = rotation
            fn(rotation)

        else:
            # find best rotation angle:
            angle = brent(fn, brack=(rotation - rotationDeviation,
                                     rotation + rotationDeviation))

        loc = cv2.minMaxLoc(fn.res)[-1]

        offsx = int(round(loc[0] - ho))
        offsy = overlapDeviation + overlap - loc[1]
        return offsx, offsy, angle


if __name__ == '__main__':
    import sys
    import imgProcessor
    from fancytools.os.PathStr import PathStr
    d = PathStr(imgProcessor.__file__).dirname().join(
        'media', 'electroluminescence')

    # STITCH BOTTOM
    i1 = d.join('EL_module_a_dist.PNG')
    i2 = d.join('EL_module_b_dist.PNG')
    i3 = d.join('EL_module_c.PNG')

    s = StitchImages(i1)
    stitched1 = s.addImg(i2, side='bottom', overlap=50, overlapDeviation=20)
    stitched1 = s.addImg(i3, side='bottom', overlap=50, overlapDeviation=20)

    # STITCH TOP
    s = StitchImages(i3)
    stitched2 = s.addImg(i2, side='top', overlap=50, overlapDeviation=20)
    stitched2 = s.addImg(i1, side='top', overlap=50, overlapDeviation=20)

    # STITCH RIGHT
    i1 = d.join('EL_module_a_dist2.PNG')
    i2 = d.join('EL_module_b_dist2.PNG')
    i3 = d.join('EL_module_c2.PNG')

    s = StitchImages(i1)
    s.addImg(i2, side='right', overlap=50, overlapDeviation=20)
    stitched3 = s.addImg(i3, side='right', overlap=50, overlapDeviation=20)

    # STITCH LEFT
    s = StitchImages(i3)
    stitched4 = s.addImg(i2, side='left', overlap=50, overlapDeviation=20,
                         rotationDeviation=10)
    stitched4 = s.addImg(i1, side='left', overlap=50, overlapDeviation=20)

    if 'no_window' not in sys.argv:
        cv2.namedWindow("bottom", cv2.WINDOW_NORMAL)
        cv2.imshow('bottom', stitched1)

        cv2.namedWindow("top", cv2.WINDOW_NORMAL)
        cv2.imshow('top', stitched2)

        cv2.namedWindow("right", cv2.WINDOW_NORMAL)
        cv2.imshow('right', stitched3)

        cv2.namedWindow("left", cv2.WINDOW_NORMAL)
        cv2.imshow('left', stitched4)

        cv2.waitKey()
