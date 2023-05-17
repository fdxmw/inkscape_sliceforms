import math
import sys


def main():
    """Calculate truncated sphere height from inner_radius and top_radius.

    top_radius is the radius of the truncated sphere's top (and bottom) hole.

    """
    outer_radius = float(sys.argv[1])
    inner_radius = float(sys.argv[2])
    top_radius = float(sys.argv[3])

    # cos(loxodromic_angle) = top_radius / inner_radius
    loxodromic_angle = math.acos(top_radius / inner_radius)

    # sin(loxodromic_angle) = (height / 2) / outer_radius
    height = math.sin(loxodromic_angle) * outer_radius * 2

    print(f'height {height:.2f}')
    print(f'loxodromic_angle {math.degrees(loxodromic_angle):.2f}')


if __name__ == '__main__':
    main()
