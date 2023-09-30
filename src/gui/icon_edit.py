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

def get_pixmap(filename, fade=True):
    fade_factor = 0.15
    fullfile = os.path.join(_ICONS_DIR, filename)
    if not fade:
        return QPixmap(fullfile)
    img = io.imread(fullfile).astype(np.float32)
    img = (fade_factor*img).astype(np.uint8)

    return numpy_to_qt_pixmap(img)
