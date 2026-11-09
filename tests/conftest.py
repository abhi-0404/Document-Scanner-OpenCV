import cv2
import numpy as np
import pytest

# Corners of the tilted page drawn into the synthetic photo, as (x, y),
# listed in the order the scanner returns them: top-left, top-right, bottom-right, bottom-left.
PAGE_CORNERS = np.array([[150, 100], [620, 140], [580, 520], [120, 480]], dtype=np.float32)


@pytest.fixture()
def photo():
    """An 800x600 'photo' of a white page with text lines, shot at an angle on a dark desk."""
    im = np.full((600, 800, 3), 40, dtype=np.uint8)
    cv2.fillPoly(im, [PAGE_CORNERS.astype(np.int32)], (245, 245, 245))
    for i in range(6):
        y = 190 + i * 45
        cv2.line(im, (200, y), (520, y + 10), (30, 30, 30), 4)
    return im
