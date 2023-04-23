import math
import unittest

import calculations


class TestCalculations(unittest.TestCase):
    def test_calculate_slot_angles(self):
        # From page 4 of
        # https://www.heldermann-verlag.de/jgg/jgg15/j15h1mone.pdf
        expected_angles = [76.9, 63.4, 49.1, 33.7, 17.2, 0, -17.2, -33.7,
                           -49.1, -63.4, -76.9]
        actual_angles = [
            math.degrees(r)
            for r in calculations.slot_angles(12, math.pi / 6)]

        self.assertEqual(len(actual_angles), len(expected_angles))

        for actual, expected in zip(actual_angles, expected_angles):
            self.assertAlmostEqual(actual, expected, places=1)


if __name__ == '__main__':
    unittest.main()
