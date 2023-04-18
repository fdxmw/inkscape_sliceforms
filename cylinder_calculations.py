import math

from common.point import Point

from calculations import solve_quadratic


def loxodromic_angle(height, radius):
    '''Calculate slice intersection angle for a cylinder with (height, radius).

    When a cylinder is sliced in half vertically, it reveals a rectangular
    cross-section. The loxodromic_angle is the angle of the diagonal of the
    rectangular cross-section, relative to the base of the cylinder.

    '''
    return math.atan((height / 2) / radius)


def intersect_ellipse_line(x_radius, y_radius, angle, dy) -> Point:
    '''Intersect an ellipse and a line.

    The ellipse is centered at the origin, with horizontal radius x_radius and
    vertical radius y_radius.

    The line has y-intercept dy, and slope 'angle', in radians.

    Find the point (x, y) where the line intersects the ellipse, such that x is
    positive.

    '''
    # Ellipse centered at origin has equation
    #   x^2 / x_radius^2 + y^2 / y_radius^2 = 1
    #
    # Line with angle 'angle' and y-intercept dy has equation
    #   y = tan(angle) * x + dy
    #
    # Substitute:
    #   x^2 / x_radius^2 + (tan(angle) * x + dy)^2 / y_radius^2 = 1
    #   y_radius^2 * x^2 + x_radius^2 * (tan(angle) * x + dy)^2 =
    #     x_radius^2 * y_radius^2
    #   y_radius^2 * x^2 + x_radius^2 * ((tan(angle) * x)^2 +
    #                                    2 * tan(angle) * x * dy +
    #                                    dy^2) =
    #     x_radius^2 * y_radius^2
    #   y_radius^2 * x^2 + x_radius^2 * (tan(angle) * x)^2 +
    #                      x_radius^2 * 2 * tan(angle) * x * dy +
    #                      x_radius^2 * dy^2 =
    #     x_radius^2 * y_radius^2
    #   (y_radius^2 + x_radius^2 * tan(angle)^2) * x^2 +
    #     (x_radius^2 * 2 * tan(angle) * dy) * x +
    #     x_radius^2 * dy^2 - x_radius^2 * y_radius^2 = 0
    #
    # Solve quadratic equation (a * x^2 + b * x + c = 0) with:
    #   a = y_radius^2 + x_radius^2 * tan(angle)^2
    #   b = x_radius^2 * 2 * tan(angle) * dy
    #   c = x_radius^2 * (dy^2 - y_radius^2)
    a = (y_radius * y_radius +
         x_radius * x_radius * math.pow(math.tan(angle), 2))
    b = x_radius * x_radius * 2 * math.tan(angle) * dy
    c = x_radius * x_radius * (dy * dy - y_radius * y_radius)

    x = solve_quadratic(a, b, c)
    y = math.tan(angle) * x + dy
    return Point(x, y)


def slot_corners(x_radius, y_radius, angle, width):
    '''Calculate slot corner coordinates.

    'angle' is the slot's angle, and 'width' is the slot's width.

    Returns a pair of Points (P0, P1) that identify a slot's corners. The
    origin is vertically centered between the slot's top-left and bottom-right
    corners.

                ▏
                ▏P1
               ╱
              ╱
             ╱   P0
            ╱  ╱▏
           ╱  ╱ ▏
          ╱  ╱
         ╱  ╱ angle
            ▔▔▔▔
       ╱━━╱
        width

    The vertical line in the diagram above is actually an elliptical arc, with
    horizontal radius x_radius and vertical radius y_radius.

    '''
    # Vertical distance from a slot wall to the center of the slot.
    #    ▁▁
    #     ▏      ╱     ╱
    #  dy ▏     ╱▕    ╱
    #    ▁▏    ╱ ▕   ╱
    #     ▏   ╱  ▕  ╱
    #  dy ▏  ╱   ▕ ╱
    #     ▏ ╱    ▕╱ angle
    #    ▔▔       ▔▔▔▔
    #     ╱━━━━━╱
    #      width
    dy = (width / 2) / math.sin(math.pi / 2 - angle)

    # Intersect the slot walls with the elliptical slice edge. The upper slot
    # wall has y-intercept dy, and the lower slot wall has y-intercept
    # -dy. Both walls have the same angle.
    return [intersect_ellipse_line(x_radius, y_radius, angle, dy),
            intersect_ellipse_line(x_radius, y_radius, angle, -dy)]


def calculate_height(radius, loxodromic_angle):
    '''Calculate a cylinder's height from radius and loxodromic_angle.

    This is useful for creating a cylinder with a specific loxodromic angle.

    '''
    return math.tan(loxodromic_angle) * (radius * 2)


def main():
    radius = 40
    height = calculate_height(radius=radius, loxodromic_angle=math.radians(35))
    print(height)
    print(math.degrees(loxodromic_angle(height=height, radius=radius)))


if __name__ == '__main__':
    main()
