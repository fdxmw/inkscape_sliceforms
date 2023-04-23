import math
import unittest

import hyperbola_calculations


class TestHyperbolaCalculations(unittest.TestCase):
    def test_slot_corners(self):
        # Test left edge intersections.
        intersections = hyperbola_calculations.slot_corners(
            outer_waist_radius=2, inner_radius=1, half_slice_height=3,
            outer_inner=hyperbola_calculations.OuterInner.INNER,
            angle=math.pi / 4, width=0)

        self.assertAlmostEqual(intersections[0].x, 1)
        self.assertAlmostEqual(intersections[1].x, 1)
        self.assertAlmostEqual(intersections[0].y, 1)
        self.assertAlmostEqual(intersections[1].y, 1)

        intersections = hyperbola_calculations.slot_corners(
            outer_waist_radius=2, inner_radius=1, half_slice_height=3,
            outer_inner=hyperbola_calculations.OuterInner.INNER,
            angle=-math.pi / 4, width=0)

        self.assertAlmostEqual(intersections[0].x, 1)
        self.assertAlmostEqual(intersections[1].x, 1)
        self.assertAlmostEqual(intersections[0].y, -1)
        self.assertAlmostEqual(intersections[1].y, -1)

        # Test right edge intersections.
        intersections = hyperbola_calculations.slot_corners(
            outer_waist_radius=2, inner_radius=1, half_slice_height=3,
            outer_inner=hyperbola_calculations.OuterInner.OUTER,
            angle=math.pi / 4, width=0)

        self.assertAlmostEqual(intersections[0].x, 2)
        self.assertAlmostEqual(intersections[1].x, 2)
        self.assertAlmostEqual(intersections[0].y, 2)
        self.assertAlmostEqual(intersections[1].y, 2)

        intersections = hyperbola_calculations.slot_corners(
            outer_waist_radius=2, inner_radius=1, half_slice_height=3,
            outer_inner=hyperbola_calculations.OuterInner.OUTER,
            angle=-math.pi / 4, width=0)

        self.assertAlmostEqual(intersections[0].x, 2)
        self.assertAlmostEqual(intersections[1].x, 2)
        self.assertAlmostEqual(intersections[0].y, -2)
        self.assertAlmostEqual(intersections[1].y, -2)

        # Test top edge intersections.
        intersections = hyperbola_calculations.slot_corners(
            outer_waist_radius=2, inner_radius=1, half_slice_height=1.5,
            outer_inner=hyperbola_calculations.OuterInner.OUTER,
            angle=math.pi / 4, width=0)

        self.assertAlmostEqual(intersections[0].x, 1.5)
        self.assertAlmostEqual(intersections[1].x, 1.5)
        self.assertAlmostEqual(intersections[0].y, 1.5)
        self.assertAlmostEqual(intersections[1].y, 1.5)

        # Test bottom edge intersections.
        intersections = hyperbola_calculations.slot_corners(
            outer_waist_radius=2, inner_radius=1, half_slice_height=1.5,
            outer_inner=hyperbola_calculations.OuterInner.OUTER,
            angle=-math.pi / 4, width=0)

        self.assertAlmostEqual(intersections[0].x, 1.5)
        self.assertAlmostEqual(intersections[1].x, 1.5)
        self.assertAlmostEqual(intersections[0].y, -1.5)
        self.assertAlmostEqual(intersections[1].y, -1.5)


if __name__ == '__main__':
    unittest.main()
