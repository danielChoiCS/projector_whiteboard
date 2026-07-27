from src.calibration.manual import _is_convex_and_simple, _quad_area, _validate_quad

SQUARE = [(0, 0), (100, 0), (100, 100), (0, 100)]


def test_quad_area_of_unit_square_matches_side_length_squared():
    assert abs(_quad_area(SQUARE)) == 100 * 100


def test_quad_area_sign_flips_with_winding_direction():
    reversed_square = list(reversed(SQUARE))
    assert _quad_area(SQUARE) == -_quad_area(reversed_square)


def test_is_convex_and_simple_true_for_a_square():
    assert _is_convex_and_simple(SQUARE) is True


def test_is_convex_and_simple_false_for_a_bowtie():
    bowtie = [(0, 0), (100, 100), (100, 0), (0, 100)]
    assert _is_convex_and_simple(bowtie) is False


def test_validate_quad_accepts_a_normal_square():
    is_valid, reason = _validate_quad(SQUARE)
    assert is_valid is True
    assert reason == ""


def test_validate_quad_rejects_a_collapsed_quad():
    collapsed = [(0, 0), (1, 0), (1, 1), (0, 1)]
    is_valid, reason = _validate_quad(collapsed)
    assert is_valid is False
    assert "collapsed" in reason.lower()


def test_validate_quad_rejects_a_bowtie_with_nontrivial_area():
    # A symmetric crossed rectangle has zero net shoelace area (the two
    # crossing lobes are equal and opposite), which would trip the "too
    # close together" check before ever reaching convexity. This asymmetric
    # trapezoid-derived bowtie has real area, so it isolates the
    # convexity/self-intersection check specifically.
    bowtie = [(0, 0), (400, 0), (0, 100), (300, 100)]
    assert abs(_quad_area(bowtie)) > 2000  # comfortably clears MIN_QUAD_AREA
    is_valid, reason = _validate_quad(bowtie)
    assert is_valid is False
    assert "crossed" in reason.lower() or "convex" in reason.lower()
