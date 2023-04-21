#!/usr/bin/env python3

'''Inkscape extension that generates sliceform torus templates.'''

# Paper with equations:
#   https://www.heldermann-verlag.de/jgg/jgg15/j15h1mone.pdf
# Assembly: https://www.youtube.com/watch?v=WVE-HeVFJ1k

import math
from collections import namedtuple
from enum import IntEnum

import inkex
from inkex.elements import PathElement
from inkex.transforms import Transform

from common.defaults import defaults
from common.logging import log
from common.path import move_abs, arc_abs, Size, Winding, line_abs
from common.point import Point, midpoint

from calculations import calculate_slot_width, calculate_slot_angles
from torus_calculations import intersect_circle_line, slot_corners

__version__ = '0.1'


class OuterInner(IntEnum):
    OUTER = 0
    INNER = 1


class SliceformTorusGenerator(inkex.extensions.GenerateExtension):
    def add_arguments(self, pars):
        pars.add_argument('--tab', type=str, dest='tab')
        pars.add_argument('--units', type=str,
                          dest='units', default='mm',
                          help='Units')
        pars.add_argument('--major_radius', type=float,
                          dest='major_radius', default='30',
                          help='Major radius')
        pars.add_argument('--minor_radius', type=float,
                          dest='minor_radius', default='15',
                          help='minor radius')
        pars.add_argument('--num_slices', type=int,
                          dest='num_slices', default='6',
                          help='Number of slices')
        pars.add_argument('--material_thickness', type=float,
                          dest='material_thickness', default='.25',
                          help='Thickness of material')
        pars.add_argument('--material_width', type=float,
                          dest='material_width', default='203',
                          help='Width of material')

    def to_uu(self, n: float):
        '''Convert from self.units to user units.'''
        return self.svg.unittouu(str(n) + self.units)

    def render_slice(self, angles, fill_color, outer_inner: OuterInner,
                     top_point) -> PathElement:
        # Draw a crescent moon shape, oriented like a closing parenthesis, with
        # the crescent moon's points vertically aligned on the left.
        #
        # The outer edge is a circular arc with radius major_radius, centered
        # at (0, minor_radius). The arc only uses the portion of the circle
        # with non-negative x.
        #
        # The inner edge is a circular arc with radius major_radius, centered
        # at (0, -minor_radius). The arc only uses the portion of the circle
        # with non-negative x.
        #
        # top_point is the higher point where the outer and inner edges
        # meet. It is on the y-axis, so top_point.x is 0, and top_point.y is
        # positive.
        #
        # The outer and inner edges meet at two points:
        #   top_point and (0, -top_point.y).
        def to_display_coordinates(p: Point) -> Point:
            '''Translate a calculated point.

            Calculations assume (0, 0) is the midpoint between the crescent
            moon's points. Translate so (0, 0) is at the top left corner of the
            crescent moon's bounding box.

            '''
            return Point(p.x, p.y + self.major_radius)

        # In display coordinates, higher y-values go down the screen, so the
        # top_point becomes the bottom_point and vice versa.
        bottom_point = to_display_coordinates(top_point)
        top_point = to_display_coordinates(Point(0, -top_point.y))

        # For each slot angle, collect three pairs of points:
        #  outer: Where the slot intersects the slice's outer edge.
        #  inner: Where the slot intersects the slice's inner edge.
        # middle: Midpoints between the outer and inner intersections.
        Intersection = namedtuple('Intersection', ['outer', 'middle', 'inner'])
        intersections = []
        for angle in angles:
            outer_points = slot_corners(self.major_radius, self.minor_radius,
                                        self.slot_width, angle)
            outer_points = [to_display_coordinates(p) for p in outer_points]

            inner_points = slot_corners(self.major_radius, -self.minor_radius,
                                        self.slot_width, angle)
            inner_points = [to_display_coordinates(p) for p in inner_points]

            middle_points = [midpoint(inner_points[0], outer_points[0]),
                             midpoint(inner_points[1], outer_points[1])]

            intersections.append(Intersection(
                outer=outer_points, middle=middle_points, inner=inner_points))

        # Start at the bottom point.
        commands = move_abs(bottom_point)

        # Draw the outer (larger) arc of the crescent moon, counterclockwise
        # from the bottom point.
        if outer_inner == OuterInner.OUTER:
            for intersection in intersections:
                commands += arc_abs(self.major_radius, self.major_radius,
                                    Size.SMALL, Winding.CCW,
                                    intersection.outer[0])
                commands += line_abs(intersection.middle[0])
                commands += line_abs(intersection.middle[1])
                commands += line_abs(intersection.outer[1])
            # Draw the last segment of the larger arc, ending at the top point.
            commands += arc_abs(self.major_radius, self.major_radius,
                                Size.SMALL, Winding.CCW, top_point)
        else:
            commands += arc_abs(self.major_radius, self.major_radius,
                                Size.LARGE, Winding.CCW, top_point)

        # Draw the inner (smaller) arc of the crescent moon, clockwise from the
        # top point.
        if outer_inner == OuterInner.INNER:
            for intersection in reversed(intersections):
                commands += arc_abs(self.major_radius, self.major_radius,
                                    Size.SMALL, Winding.CW,
                                    intersection.inner[1])
                commands += line_abs(intersection.middle[1])
                commands += line_abs(intersection.middle[0])
                commands += line_abs(intersection.inner[0])
        # Draw the last segment of the smaller arc, ending at bottom point.
        commands += arc_abs(self.major_radius, self.major_radius,
                            Size.SMALL, Winding.CW, bottom_point)
        commands += 'Z'

        path = PathElement()
        path.style = inkex.styles.Style(style={
            'stroke-width': self.stroke_width,
            'stroke': defaults['cut_color'],
            'fill': fill_color})
        path.set_path(commands)
        return path

    def generate(self):
        self.stroke_width = str(self.svg.unittouu(defaults['stroke_width']))
        self.units = self.options.units

        self.major_radius = self.to_uu(self.options.major_radius)
        self.minor_radius = self.to_uu(self.options.minor_radius)
        self.num_slices = self.options.num_slices
        self.material_thickness = self.to_uu(self.options.material_thickness)
        self.material_width = self.to_uu(self.options.material_width)

        # Spacing between templates.
        self.template_spacing = self.svg.unittouu(defaults['template_spacing'])

        assert self.num_slices > 0, \
            'Error: num_slices must be greater than zero'

        assert self.major_radius > self.minor_radius, \
            'Error: Major radius must be larger than minor radius'

        # First equation on page 3 from
        # https://www.heldermann-verlag.de/jgg/jgg15/j15h1mone.pdf
        self.loxodromic_angle = (
            math.atan(self.minor_radius /
                      math.sqrt(self.major_radius * self.major_radius -
                                self.minor_radius * self.minor_radius)))

        self.slot_width = calculate_slot_width(self.material_thickness,
                                               self.loxodromic_angle * 2)

        angles = calculate_slot_angles(self.num_slices, self.loxodromic_angle)

        # top_point is the top left point where the inner and outer edges
        # meet. Note that the top left corner of the bounding box is a
        # different point. Calculate this point's coordinates by intersecting a
        # vertical line through (0, 0) with the outer edge.
        top_point = intersect_circle_line(self.major_radius, self.minor_radius,
                                          math.pi / 2, 0)

        # Find the point where the horizontal line through top_point intersects
        # with the current slice's outer edge. That point's x-coordinate is how
        # far we have to shift subsequent slices to the right so slices don't
        # overlap.
        additional_slice_width = intersect_circle_line(
            self.major_radius, self.minor_radius, 0, top_point.y).x
        slice_height = self.major_radius * 2

        # Lay out templates in rows, with self.material_width as the maximum
        # row width.

        # The first slice requires the full slice width, so compensate by
        # decreasing the material width by the width of one full slice. Find
        # the point where the horizontal line through (0, 0) intersects the
        # outer edge.
        first_slice_width = intersect_circle_line(
            self.major_radius, self.minor_radius, 0, 0).x
        material_width = self.material_width - first_slice_width
        templates_per_row = (
            1 + math.floor(material_width /
                           (additional_slice_width + self.template_spacing)))
        num_rows = math.ceil(self.num_slices / templates_per_row)

        # Generate two rows of slice templates. The top row has slots on the
        # outer edge, and the bottom row has slots on the inner edge.
        def generate_templates(top_left: Point, outer_inner: OuterInner):
            templates_generated = 0
            while templates_generated < self.num_slices:
                top_left.x = 0
                num_templates = min(templates_per_row,
                                    self.num_slices - templates_generated)
                templates_generated += num_templates
                for _ in range(num_templates):
                    path = self.render_slice(
                        angles, defaults['fill_colors'][outer_inner],
                        outer_inner, top_point)

                    translate = Transform()
                    translate.add_translate(top_left.x, top_left.y)
                    path.transform = translate
                    yield path

                    top_left.x += (additional_slice_width +
                                   self.template_spacing)
                top_left.y += slice_height + self.template_spacing

        top_left = Point(0, 0)
        yield from generate_templates(top_left, OuterInner.OUTER)
        top_left = Point(0, num_rows * (slice_height + self.template_spacing))
        yield from generate_templates(top_left, OuterInner.INNER)


SliceformTorusGenerator().run()
