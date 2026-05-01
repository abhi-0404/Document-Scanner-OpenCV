import cv2
import numpy as np

def reorder(vertices):
    reordered = np.zeros_like(vertices, dtype=np.float32)
    add = vertices.sum(1)
    reordered[0] = vertices[np.argmin(add)]
    reordered[2] = vertices[np.argmax(add)]
    diff = np.diff(vertices, axis=1)
    reordered[1] = vertices[np.argmin(diff)]
    reordered[3] = vertices[np.argmax(diff)]
    return reordered

def to_grayscale(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

def blur(im):
    return cv2.GaussianBlur(im, (3, 3), 0)

def to_edges(im):
    return cv2.Canny(im, 50, 150)

def find_vertices(im, max_candidates=5, epsilon_ratio=0.02):
    contours, _ = cv2.findContours(im.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:max_candidates]
    vertices = None
    for cnt in contours:
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        approx = cv2.approxPolyDP(cnt, epsilon_ratio * perimeter, True)
        if len(approx) == 4 and cv2.contourArea(approx) > 0:
            vertices = approx.reshape(4, 2)
            break
    if vertices is None:
        height, width = im.shape[:2]
        vertices = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32)
    return reorder(vertices.astype(np.float32))

def crop_out(im, vertices):
    top_width = np.linalg.norm(vertices[0] - vertices[1])
    bottom_width = np.linalg.norm(vertices[2] - vertices[3])
    left_height = np.linalg.norm(vertices[0] - vertices[3])
    right_height = np.linalg.norm(vertices[1] - vertices[2])
    width = int(max(top_width, bottom_width))
    height = int(max(left_height, right_height))
    if width <= 0 or height <= 0:
        height, width = im.shape[:2]
    target = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)
    transform = cv2.getPerspectiveTransform(vertices.astype(np.float32), target)
    cropped = cv2.warpPerspective(im, transform, (width, height))
    return cropped

def enhance(im, gamma=1.1, clahe_clip=2.0, clahe_grid=(12, 12)):
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    corrected = cv2.LUT(im, table)
    lab = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_grid)
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    enhanced_img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    hsv = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = cv2.addWeighted(s, 1.1, cv2.GaussianBlur(s, (0, 0), 1.0), 0.2, 0)
    s = np.clip(s, 25, 235).astype(np.uint8)
    hsv = cv2.merge([h, s, v])
    enhanced_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    blurred = cv2.GaussianBlur(enhanced_img, (0, 0), 1.5)
    sharpened = cv2.addWeighted(enhanced_img, 1.35, blurred, -0.35, 0)
    final = cv2.bilateralFilter(sharpened, 7, 50, 50)
    return final

def scan(im):
    grayscale = to_grayscale(im)
    blurred = blur(grayscale)
    edges = to_edges(blurred)
    vertices = find_vertices(edges)
    cropped = crop_out(im, vertices)
    scanned = enhance(cropped)
    return scanned
