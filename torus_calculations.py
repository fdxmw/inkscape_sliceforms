import math

from common.point import Point

from calculations import solve_quadratic


def intersect_circle_line(radius, dx, angle, dy):
    '''Find the point where a circle intersects a line.

    The circle is centered at (dx, 0) and has radius 'radius'.

    The line has slope 'angle' in radians, and y-intercept dy.

    Returns a Point(x, y) where x is non-negative.

    '''
    # The circle's equation is (x - dx)^2 + y^2 = radius^2
    #
    # The line's equation is y = tan(angle) * x + dy
    #
    # Substitute:
    #   (x - dx)^2 + (tan(angle) * x + dy)^2 = radius^2
    #   x^2 - 2*dx*x + dx^2 +
    #     (tan(angle) * x)^2 + 2 * tan(angle) * dy * x + dy^2 =
    #     radius^2
    #   x^2 - 2*dx*x + dx^2 +
    #     tan(angle)^2 * x^2 + 2*tan(angle) * dy * x + dy^2 =
    #     radius^2
    #   x^2 + tan(angle)^2 * x^2 +
    #     -2*dx*x + 2*tan(angle) * dy * x +
    #     dx^2 + dy^2 - radius^2= 0
    #   (1 + tan(angle)^2) * x^2 +
    #     (-2*dx + 2*tan(angle) * dy) * x +
    #     dx^2 + dy^2 - radius^2= 0
    #
    # Solve quadratic equation (a * x^2 + b * x + c = 0) with:
    #   a = 1 + tan(angle)^2
    #   b = -2*dx + 2*tan(angle) * dy
    #   c = dx^2 + dy^2 - radius^2
    a = 1 + math.pow(math.tan(angle), 2)
    b = -2 * dx + 2 * math.tan(angle) * dy
    c = dx * dx + dy * dy - radius * radius

    x = solve_quadratic(a, b, c)
    y = math.tan(angle) * x + dy
    return Point(x, y)


def slot_corners(radius, dx, width, angle):
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

    The vertical line in the diagram above is actually a circular arc centered
    at (dx, 0), with radius 'radius'.

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
    return [intersect_circle_line(radius, dx, angle, dy),
            intersect_circle_line(radius, dx, angle, -dy)]
