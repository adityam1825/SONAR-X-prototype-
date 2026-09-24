"""
Unit tests for Haversine distance calculation.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import math
import pytest
from common.haversine import haversine_distance, bearing


class TestHaversineDistance:
    def test_same_point_is_zero(self):
        d = haversine_distance(19.45, 72.84, 19.45, 72.84)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_known_distance(self):
        # Mumbai to Delhi ≈ 1148 km
        d = haversine_distance(19.076, 72.877, 28.644, 77.216)
        assert 1_100_000 < d < 1_200_000

    def test_short_distance(self):
        # ~244 m — demo relocation distance (approx)
        d = haversine_distance(19.4521, 72.8403, 19.4535, 72.8421)
        assert 180 < d < 300

    def test_symmetry(self):
        d1 = haversine_distance(10.0, 20.0, 11.0, 21.0)
        d2 = haversine_distance(11.0, 21.0, 10.0, 20.0)
        assert d1 == pytest.approx(d2, rel=1e-9)

    def test_bearing_north(self):
        b = bearing(0, 0, 1, 0)
        assert b == pytest.approx(0.0, abs=0.1)

    def test_bearing_east(self):
        b = bearing(0, 0, 0, 1)
        assert b == pytest.approx(90.0, abs=0.5)
