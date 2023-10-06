import os
import numpy as np
from skimage import io
from PyQt5.QtGui import QPixmap, QImage

_ICONS_DIR = "./data/icons"

def numpy_to_qt_image(image):
    height, width, channel = image.shape
    bytesPerLine = 3 * width
    return QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)

def numpy_to_qt_pixmap(image):
    return QPixmap(numpy_to_qt_image(image))

def get_pixmap(filename, fade=True, highlight=False):
    fade_factor = 0.15
    fullfile = os.path.join(_ICONS_DIR, filename)
    if not fade and not highlight:
        return QPixmap(fullfile)
    img = io.imread(fullfile).astype(np.float32)

    if highlight:
        s = img.shape
        red = np.array([255, 0, 0]).reshape(1, 1, 3).astype(np.float32)
        img[0:2, :, :] = red
        img[:, 0:2, :] = red
        img[(s[0] - 2):s[0], :, :] = red
        img[:, (s[1] - 2):s[1], :] = red

    if fade:
        img *= fade_factor
    img = img.astype(np.uint8)

    return numpy_to_qt_pixmap(img)
