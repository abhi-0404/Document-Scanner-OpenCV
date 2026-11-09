"""Tests for the OpenCV scanning pipeline in scanner.py."""
import numpy as np

from scanner import crop_out, enhance, find_vertices, reorder, scan, to_edges, to_grayscale, blur
from tests.conftest import PAGE_CORNERS


def test_reorder_puts_corners_in_clockwise_order_from_top_left():
    shuffled = PAGE_CORNERS[[2, 0, 3, 1]]
    assert np.array_equal(reorder(shuffled), PAGE_CORNERS)


def test_find_vertices_locates_the_page_corners(photo):
    edges = to_edges(blur(to_grayscale(photo)))
    found = find_vertices(edges)
    assert found.shape == (4, 2)
    assert np.abs(found - PAGE_CORNERS).max() <= 6


def test_find_vertices_falls_back_to_image_corners_when_no_page():
    blank = np.zeros((100, 200), dtype=np.uint8)
    found = find_vertices(blank)
    expected = np.array([[0, 0], [199, 0], [199, 99], [0, 99]], dtype=np.float32)
    assert np.array_equal(found, expected)


def test_crop_out_flattens_to_the_page_size(photo):
    flat = crop_out(photo, PAGE_CORNERS)
    height, width = flat.shape[:2]
    # Longest top/bottom edge is about 471 px and longest side about 382 px.
    assert abs(width - 471) <= 2
    assert abs(height - 382) <= 2


def test_enhance_turns_grayscale_into_three_channel_uint8():
    gray = np.full((50, 80), 128, dtype=np.uint8)
    out = enhance(gray)
    assert out.shape == (50, 80, 3)
    assert out.dtype == np.uint8


def test_scan_returns_a_bright_flattened_page(photo):
    scanned = scan(photo)
    height, width = scanned.shape[:2]
    assert abs(width - 471) <= 8
    assert abs(height - 382) <= 8
    assert scanned.shape[2] == 3
    # The result is the page, not the dark desk around it.
    assert scanned.mean() > 150
    assert photo.mean() < scanned.mean()
