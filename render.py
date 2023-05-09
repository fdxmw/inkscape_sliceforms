import collections
import enum
import typing

from common import path
from common import point

#  outer: Where the slot intersects the slice's outer edge.
#  inner: Where the slot intersects the slice's inner edge.
# middle: Midpoints between the outer and inner intersections.
Intersection = collections.namedtuple(
    'Intersection', ['outer', 'middle', 'inner'])


def reverse_intersections(
        intersections: list[Intersection]) -> list[Intersection]:
    """Reverse a list of intersections.

    This reverses both the outer list of intersections, and the inner lists of
    points.

    """
    def reverse_points(points: list[point.Point]) -> list[point.Point]:
        return list(reversed(points))
    return [Intersection(outer=reverse_points(i.outer),
                         middle=reverse_points(i.middle),
                         inner=reverse_points(i.inner))
            for i in reversed(intersections)]


def mirror_intersections(
        intersections: list[Intersection]) -> list[Intersection]:
    """Mirror a list of intersections about the y-axis."""
    def mirror_points(points):
        return [point.Point(-p.x, p.y) for p in points]
    return [Intersection(outer=mirror_points(i.outer),
                         middle=mirror_points(i.middle),
                         inner=mirror_points(i.inner))
            for i in intersections]


class OuterInner(enum.IntEnum):
    OUTER = 0
    INNER = 1


def elliptical_slotted_path(
        intersections: list[Intersection], outer_inner: OuterInner,
        winding: path.Winding, radius_x: float, radius_y: float,
        end: point.Point, skip: typing.Callable[[int], bool]) -> str:
    """Return path commands to render a slotted elliptical curve.

    :param intersections: Specifies slot locations
    :param outer_inner: Chooses between rendering the outer and inner edges
    :param winding: Drawing direction: clockwise (Winding.CW) or
        counterclockwise (Winding.CCW).
    :param radius_x: Horizontal ellipse radius.
    :param radius_y: Vertical ellipse radius.
    :param end: End point for the elliptical path.
    :param skip: Function that returns true when a slot should not be rendered.

    """
    commands = ''
    for i, intersection in enumerate(intersections):
        if skip(i):
            continue

        # Draw a slot. The first slot wall is a line between points (a) and
        # (b), the bottom of the slot is a line between points (b) and (c), and
        # the second slot wall is a line between points (c) and (d).
        #
        # 1. Draw an elliptical arc to the first top corner (a)
        # 2. Draw a straight line to the first bottom corner (b)
        # 3. Draw a straight line to the second bottom corner (c)
        # 4. Draw a straight line to the second top corner (d)
        b = intersection.middle[0]
        c = intersection.middle[1]
        if outer_inner == OuterInner.OUTER:
            a = intersection.outer[0]
            d = intersection.outer[1]
        else:
            a = intersection.inner[0]
            d = intersection.inner[1]

        commands += path.arc_abs(
            radius_x, radius_y, path.Size.SMALL, winding, a)
        commands += path.line_abs(b)
        commands += path.line_abs(c)
        commands += path.line_abs(d)

    # Draw the last segment of the elliptical arc, to 'end'.
    commands += path.arc_abs(
        radius_x, radius_y, path.Size.SMALL, winding, end)
    return commands
