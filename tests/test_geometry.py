from src.calibration.geometry import compute_homography, order_corners


def test_order_corners_sorts_shuffled_points():
    top_left, top_right, bottom_right, bottom_left = (
        (10.0, 10.0),
        (100.0, 12.0),
        (98.0, 90.0),
        (8.0, 95.0),
    )
    shuffled = [bottom_right, top_left, bottom_left, top_right]

    ordered = order_corners(shuffled)

    assert ordered == [top_left, top_right, bottom_right, bottom_left]


def test_compute_homography_maps_corners_to_unit_square():
    corners = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]

    transform = compute_homography(corners)

    assert transform.shape == (3, 3)
