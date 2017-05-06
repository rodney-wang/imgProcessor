# coding=utf-8
from __future__ import print_function

import numpy as np

from skimage.measure import label
from skimage.filters import threshold_otsu
from scipy.ndimage.filters import minimum_filter
from scipy.ndimage.measurements import center_of_mass

from imgProcessor.imgIO import imread
from imgProcessor.utils.getBackground2 import getBackground2


def vignettingFromSpotAverage(
        images, bgImages=None, averageSpot=True, thresh=None):
    '''
    [images] --> list of images containing
                 small bright spots generated by the same 
                 device images at different positions within image plane
            depending on the calibrated waveband the device can be 
            a LCD display or PV 1-cell mini module

    This method is referred as 'Method B' in
    ---
    K.Bedrich, M.Bokalic et al.:
    ELECTROLUMINESCENCE IMAGING OF PV DEVICES:
    ADVANCED FLAT FIELD CALIBRATION,2017
    ---

    Args:
        averageSpot(bool): True: take only the average intensity of each spot
        thresh(float): marks the minimum spot value 
                       (estimated with Otsus method otherwise)

    Returns:
        * array to be post processed
        * image mask containing valid positions
    '''

    fitimg, mask = None, None
    mx = 0
    for c, img in enumerate(images):
        print('%s/%s' % (c + 1, len(images)))

        if c == 0:
            avgBg = getBackground2(bgImages, img)
        img = imread(img, dtype=float)
        img -= avgBg
        # init:
        if fitimg is None:
            fitimg = np.zeros_like(img)
            mask = np.zeros_like(img, dtype=bool)
        # find spot:
        if thresh is None:
            t = threshold_otsu(img)
        else:
            t = thresh

        # take brightest spot
        spots, n = label(minimum_filter(img > t, 3),
                         background=0, return_num=True)
        spot_sizes = [(spots == i).sum() for i in range(1, n + 1)]

        try:
            spot = (spots == np.argmax(spot_sizes) + 1)
        except ValueError:
            print("couldn't find spot in image")
            continue

        if averageSpot:
            spot = np.rint(center_of_mass(spot)).astype(int)
            mx2 = img[spot].max()
        else:
            mx2 = img[spot].mean()
        fitimg[spot] = img[spot]
        mask[spot] = 1

        if mx2 > mx:
            mx = mx2

    # scale [0...1]:
    fitimg /= mx

    return fitimg, mask


if __name__ == '__main__':
    import sys
    from imgProcessor.equations.vignetting import vignetting
    from imgProcessor.filters.addNoise import addNoise

    import pylab as plt

    n = 50
    s0, s1 = 300, 400
    size = 30  # ...of the small rect within image
    SNR = 10

    # create synthetic data:
    imgs = []
    for i in range(n):
        # random top-left position:
        r0, r1 = np.random.rand(2)
        p0, p1 = int(r0 * (s0 - size)), int(r1 * (s1 - size))
        # rect intensity depending on current position:
        color = int(vignetting((p0 + size // 2, p1 + size // 2),
                               cx=s0 // 2, cy=s1 // 2) * 255)

        img = np.zeros((s0, s1))
        img[p0: p0 + size, p1: p1 + size] = color
        imgs.append(addNoise(img, SNR))

    ###
    out, _ = vignettingFromSpotAverage(imgs, 0, averageSpot=False)
    out2, _ = vignettingFromSpotAverage(imgs, 0)
    ###
    if 'no_window' not in sys.argv:
        plt.figure('without spot average')
        plt.imshow(out, interpolation='none')

        plt.figure('with spot average')
        plt.imshow(out2, interpolation='none')
        plt.show()