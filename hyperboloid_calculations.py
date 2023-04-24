import enum
import math
import sys

from common import point


def loxodromic_angle(height: float, outer_edge_radius: float,
                     outer_waist_radius: float) -> float:
    '''Calculate slice intersection angle for hyperboloid.

    The loxodromic_angle is the angle of each slice relative to the base of the
    hyperboloid.

    '''
    # Draw a right triangle with sides outer_waist_radius and slice_base, and
    # hypotenuse outer_edge_radius.
    # outer_edge_radius² = outer_waist_radius² + slice_base²
    slice_base = math.sqrt(outer_edge_radius ** 2 - outer_waist_radius ** 2)

    # Draw a right triangle with sides slice_base and (height / 2), and
    # hypotenuse (slice_height / 2). The loxodromic_angle is the angle between
    # slice_base and the hypotenuse.
    return math.atan((height / 2) / slice_base)


def check_slice_intersection(
        intersection: point.Point, outer_waist_radius: float,
        inner_radius: float, half_slice_height: float) -> point.Point:
    '''If the intersection is on the slice, return intersection, else None.'''
    on_slice = (intersection.x >= inner_radius and
                intersection.x <= outer_waist_radius and
                intersection.y >= -half_slice_height and
                intersection.y <= half_slice_height)
    if on_slice:
        return intersection
    else:
        return None


def intersect_vertical_line(
        vx: float, angle: float, dy: float, outer_waist_radius: float,
        inner_radius: float, half_slice_height: float) -> point.Point:
    '''Intersect a vertical line and a line.

    The vertical line is at x = vx.

    The line has y-intercept dy, and slope 'angle', in radians.

    Find the point (x, y) where the line intersects the vertical line.

    '''
    # Line with angle 'angle' and y-intercept dy has equation
    #   y = tan(angle) * x + dy
    return check_slice_intersection(point.Point(vx, math.tan(angle) * vx + dy),
                                    outer_waist_radius, inner_radius,
                                    half_slice_height)


def intersect_horizontal_line(
        hy: float, angle: float, dy: float, outer_waist_radius: float,
        inner_radius: float, half_slice_height: float) -> point.Point:
    '''Intersect a horizontal line and a line.

    The horizontal line is at y = hy.

    The line has y-intercept dy, and slope 'angle', in radians.

    Find the point (x, y) where the line intersects the vertical line.

    '''
    # Line with angle 'angle' and y-intercept dy has equation
    #   y = tan(angle) * x + dy
    #   x = (y - dy) / tan(angle)
    return check_slice_intersection(
        point.Point((hy - dy) / math.tan(angle), hy),
        outer_waist_radius, inner_radius, half_slice_height)


class OuterInner(enum.IntEnum):
    OUTER = 0
    INNER = 1


def slot_corners(outer_waist_radius: float, inner_radius: float,
                 half_slice_height: float, outer_inner: OuterInner,
                 angle: float, width: float):
    '''Calculate slot corner coordinates.

    'angle' is the slot's angle, and 'width' is the slot's width.

    Returns a pair of point.Points (first, second) that identify a slot's
    corners. The origin is vertically centered between the slot's top and
    bottom edges. The slice's left edge is at inner_radius, right edge is at
    outer_waist_radius, top edge at half_slice_height, and bottom edge at
    -half_slice_height, as shown in the diagram below.

    When outer_inner == INNER, this returns the slot's corner points on the
    inner (left) edge. When outer_inner == OUTER, this returns the slot's
    corner points on the outer (top, right, bottom) edges.

                                        (outer_waist_radius, half_slice_height)
     (inner_radius, half_slice_height)       ⋰
                                      ⋱▁▁▁▁⋰
                                      ▕    ▏
                                      ▕    ▏
     •                                ▕    ▏
      (0, 0)                          ▕    ▏
                                      ▕    ▏
                                      ⋰▔▔▔▔⋱
    (inner_radius, -half_slice_height)       ⋱
                                       (outer_waist_radius, -half_slice_height)

                ▏
                ▏first
               ╱
              ╱
             ╱   second
            ╱  ╱▏
           ╱  ╱ ▏
          ╱  ╱
         ╱  ╱ angle
            ▔▔▔▔
       ╱━━╱
        width

    '''
    assert outer_waist_radius > inner_radius
    assert angle < math.pi / 2
    assert angle > -math.pi / 2

    # (angle, width) specify a beam through the origin. Calculate the
    # y-intercept of the top edge of the beam. This is the vertical distance
    # from a slot wall to the center of the slot.
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

    if outer_inner == OuterInner.INNER:
        # Intersect the slot walls with the inner (left) edge.
        intersection0 = intersect_vertical_line(
            inner_radius, angle, dy, outer_waist_radius, inner_radius,
            half_slice_height)
        intersection1 = intersect_vertical_line(
            inner_radius, angle, -dy, outer_waist_radius, inner_radius,
            half_slice_height)
        return [intersection0, intersection1]

    else:
        # Intersect a slot wall with y_intercept with the outer (top, right,
        # bottom) edges.
        def outer_intersection(y_intercept):
            # Try intersecting with the right edge.
            right_intersection = intersect_vertical_line(
                outer_waist_radius, angle, y_intercept, outer_waist_radius,
                inner_radius, half_slice_height)
            if right_intersection is not None:
                return right_intersection

            # Intersection occurs outside the slice. Try intersecting with
            # the top edge instead.
            top_intersection = intersect_horizontal_line(
                half_slice_height, angle, y_intercept, outer_waist_radius,
                inner_radius, half_slice_height)
            if top_intersection is not None:
                return top_intersection

            # Intersection occurs outside the slice. Try intersecting with
            # the bottom edge instead.
            bottom_intersection = intersect_horizontal_line(
                -half_slice_height, angle, y_intercept, outer_waist_radius,
                inner_radius, half_slice_height)
            return bottom_intersection

        first = outer_intersection(dy)
        second = outer_intersection(-dy)
        return [first, second]


def main():
    # Calculate hyperboloid model parameters for models where the slices touch
    # along the outer edge.
    def help():
        divisors = [str(divisor) for divisor in range(1, 361)
                    if 360 % divisor == 0]
        print('Must specify outer_waist_radius and divisor. Valid divisors '
              'are ', str(' '.join(divisors)))
        exit(1)

    if len(sys.argv) != 3:
        help()

    outer_waist_radius = float(sys.argv[1])
    divisor = int(sys.argv[2])
    if 360 % divisor != 0:
        help()

    print('divisor', divisor)
    corner_angle = 360 / divisor
    print('Corner angle', corner_angle)
    print()

    outer_edge_radius = (outer_waist_radius /
                         math.sin(math.radians(corner_angle / 2)))
    print(f'outer_edge_radius {outer_edge_radius:.2f}')
    print(f'outer_waist_radius {outer_waist_radius}')

    # Find the number of slices with slice_width closest to target_slice_width.
    target_slice_width = 10
    multiplier = 2
    best_slice_width = 0
    best_num_slices = 0
    while True:
        num_slices = divisor * multiplier

        # Calculate distance between corners.
        #
        # There are num_slices corners, so the angle between corners is 2pi /
        # num_slices.
        angle_between_corners = 2 * math.pi / num_slices

        # sin(angle_between_corners / 2) =
        # corner_distance / 2 / outer_edge_radius
        corner_distance = (math.sin(angle_between_corners / 2) *
                           outer_edge_radius * 2)

        # sin(pi/2 - angle_between_corners / 2) =
        # slice_width / (corner_distance / 2)
        slice_width = (math.sin(math.pi / 2 - angle_between_corners / 2) *
                       (corner_distance / 2))

        current_error = abs(target_slice_width - slice_width)
        min_error = abs(target_slice_width - best_slice_width)
        if current_error > min_error:
            break
        else:
            best_slice_width = slice_width
            best_num_slices = num_slices
            multiplier += 1

    print(f'  inner_radius {(outer_waist_radius - best_slice_width):.2f}')
    print(f'  height {outer_edge_radius:.2f}')
    print(f'  num_slices {best_num_slices}')
    print(f'  (slice_width {best_slice_width:.2f})')


if __name__ == '__main__':
    main()
