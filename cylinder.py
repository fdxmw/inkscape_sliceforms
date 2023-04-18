#!/usr/bin/env python3

'''Inkscape extension that generates sliceform cylinder templates.'''

# Assembly: https://www.youtube.com/watch?v=QfBc0fR64EQ

import math
from collections import namedtuple
from enum import IntEnum

import inkex
from inkex.elements import PathElement
from inkex.transforms import Transform

from common.defaults import defaults
from common.logging import log
from common.path import move_abs, arc_abs, Size, Winding, line_abs
from common.path import vline_rel, hline_rel
from common.point import Point, midpoint

from calculations import calculate_slot_width, calculate_slot_angles
from cylinder_calculations import loxodromic_angle, slot_corners
from cylinder_calculations import intersect_ellipse_line

__version__ = '0.1'


class OuterInner(IntEnum):
    OUTER = 0
    INNER = 1


class SliceformCylinderGenerator(inkex.extensions.GenerateExtension):
    def add_arguments(self, pars):
        pars.add_argument('--tab', type=str, dest='tab')
        pars.add_argument('--units', type=str,
                          dest='units', default='mm',
                          help='Units')
        pars.add_argument('--outer_radius', type=float,
                          dest='outer_radius', default='30',
                          help='Outer radius')
        pars.add_argument('--inner_radius', type=float,
                          dest='inner_radius', default='15',
                          help='Inner radius')
        pars.add_argument('--height', type=float,
                          dest='height', default='15',
                          help='height')
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

    def render_slice(self, angles, slice_height, parent, fill_color,
                     outer_inner: OuterInner) -> PathElement:
        # Draw a backwards 'C' shape. The 'C' opens to the left.
        #
        # The outer (rightmost) edge is an elliptical arc with horizontal
        # radius outer_radius_x, and vertical radius outer_radius_y. The
        # ellipse is centered at the midpoint of the bounding box's left
        # side. The arc only uses the portion of the ellipse with non-negative
        # x.
        #
        # The inner (leftmost) edge is an elliptical arc with horizontal radius
        # inner_radius_x, and vertical radius inner_radius_y. The ellipse is
        # centered at the midpoint of the bounding box's left side. The arc
        # only uses the portion of the ellipse with non-negative x.
        #
        # The outer and inner edges are connected by two vertical lines along
        # the bounding box's left side. vertical_gap is the length of these
        # vertical lines.
        outer_radius_x = self.outer_radius
        outer_radius_y = slice_height / 2
        inner_radius_x = self.inner_radius
        inner_radius_y = self.inner_radius / math.cos(self.loxodromic_angle)
        vertical_gap = outer_radius_y - inner_radius_y

        def translate_point(p: Point) -> Point:
            '''Translate a calculated point.

            Calculations assume (0, 0) is centered at the midpoint of the
            bounding box's left side. Translate so (0, 0) is at the top left
            corner of the bounding box.

            '''
            return Point(p.x, p.y + outer_radius_y)

        # For each slot angle, collect three pairs of points:
        #  outer: Where the slot intersects the slice's outer edge.
        #  inner: Where the slot intersects the slice's inner edge.
        # middle: Midpoints between the outer and inner intersections.
        Intersection = namedtuple('Intersection', ['outer', 'middle', 'inner'])
        intersections = []
        for angle in angles:
            outer_points = slot_corners(outer_radius_x, outer_radius_y, angle,
                                        self.slot_width)
            outer_points = [translate_point(op) for op in outer_points]

            inner_points = slot_corners(inner_radius_x, inner_radius_y, angle,
                                        self.slot_width)
            inner_points = [translate_point(ip) for ip in inner_points]

            middle_points = [midpoint(inner_points[0], outer_points[0]),
                             midpoint(inner_points[1], outer_points[1])]

            intersections.append(Intersection(
                outer=outer_points, middle=middle_points, inner=inner_points))

        # Start at the bottom left point.
        bottom_left = Point(0, slice_height)
        commands = move_abs(bottom_left)

        # Draw the larger arc, counterclockwise from the bottom left corner.
        if outer_inner == OuterInner.OUTER:
            for intersection in intersections:
                commands += arc_abs(outer_radius_x, outer_radius_y,
                                    Size.SMALL, Winding.CCW,
                                    intersection.outer[0])
                commands += line_abs(intersection.middle[0])
                commands += line_abs(intersection.middle[1])
                commands += line_abs(intersection.outer[1])
            # Draw the last segment of the larger arc, ending at (0, 0).
            # point.
            commands += arc_abs(outer_radius_x, outer_radius_y,
                                Size.SMALL, Winding.CCW, Point(0, 0))
        else:
            commands += arc_abs(outer_radius_x, outer_radius_y,
                                Size.LARGE, Winding.CCW, Point(0, 0))

        commands += vline_rel(vertical_gap)

        # Draw the smaller arc, clockwise from top_left.
        if outer_inner == OuterInner.INNER:
            for intersection in reversed(intersections):
                commands += arc_abs(inner_radius_x, inner_radius_y,
                                    Size.SMALL, Winding.CW,
                                    intersection.inner[0])
                commands += line_abs(intersection.middle[0])
                commands += line_abs(intersection.middle[1])
                commands += line_abs(intersection.inner[1])
        # Draw the last segment of the smaller arc, ending at the bottom point.
        bottom_left_inner = Point(0, vertical_gap + inner_radius_y * 2)
        commands += arc_abs(inner_radius_x, inner_radius_y,
                            Size.SMALL, Winding.CW,
                            bottom_left_inner)
        commands += 'Z'

        path = PathElement()
        path.style = inkex.styles.Style(style={
            'stroke_width': self.stroke_width,
            'stroke': defaults['cut_color'],
            'fill': fill_color})
        path.set_path(commands)
        return path

    def generate(self):
        self.stroke_width = str(self.svg.unittouu(defaults['stroke_width']))
        self.units = self.options.units

        self.outer_radius = self.to_uu(self.options.outer_radius)
        self.inner_radius = self.to_uu(self.options.inner_radius)
        self.height = self.to_uu(self.options.height)
        self.num_slices = self.options.num_slices
        self.material_thickness = self.to_uu(self.options.material_thickness)
        self.material_width = self.to_uu(self.options.material_width)

        # Spacing between templates.
        self.template_spacing = self.svg.unittouu(defaults['template_spacing'])

        assert self.num_slices > 0, \
            'Error: num_slices must be greater than zero'

        assert self.outer_radius > self.inner_radius, \
            'Error: Outer radius must be larger than inner radius'

        self.loxodromic_angle = loxodromic_angle(self.height,
                                                 self.outer_radius)

        self.slot_width = calculate_slot_width(self.material_thickness,
                                               self.loxodromic_angle * 2)

        angles = calculate_slot_angles(self.num_slices, self.loxodromic_angle)

        outer_radius_x = self.outer_radius
        outer_radius_y = math.sqrt(self.outer_radius * self.outer_radius +
                                   (self.height / 2) * (self.height / 2))
        inner_radius_y = self.inner_radius / math.cos(self.loxodromic_angle)
        # Find the point where the horizontal line at inner_radius_y intersects
        # the outer radius. That point's x-coordinate is how far we have to
        # shift subsequent slices to the right so slices don't overlap.
        additional_slice_width = intersect_ellipse_line(
            outer_radius_x, outer_radius_y, 0, inner_radius_y).x
        slice_height = 2 * outer_radius_y

        # Lay out templates in rows, with self.material_width as the maximum
        # row width.

        # The first slice requires the full slice width, so compensate by
        # decreasing the material width by the width of one full slice.
        material_width = self.material_width - outer_radius_x
        # Each additional slice requires 'slice width' additional horizontal
        # space.
        templates_per_row = (
            1 + math.floor(material_width /
                           (additional_slice_width + self.template_spacing)))
        num_rows = math.ceil(self.num_slices / templates_per_row)

        def generate_templates(top_left, outer_inner: OuterInner):
            '''Render rows of slices starting at top_left.

            outer_inner determines whether the slots appear on the outer or
            inner edge of the slice.

            Returns the point where the top left corner of the next slice
            should be rendered.
            '''
            templates_generated = 0
            while templates_generated < self.num_slices:
                top_left.x = 0
                num_templates = min(templates_per_row,
                                    self.num_slices - templates_generated)
                templates_generated += num_templates
                for _ in range(num_templates):
                    path = self.render_slice(
                        angles, slice_height, self.svg.get_current_layer(),
                        defaults['fill_colors'][outer_inner], outer_inner)

                    translate = Transform()
                    translate.add_translate(top_left.x, top_left.y)
                    path.transform = translate
                    yield path

                    top_left.x += (additional_slice_width +
                                   self.template_spacing)
                top_left.y += slice_height + self.template_spacing

        # Generate two sets of slice templates. The first set has slots on the
        # outer edge, and the second set has slots on the inner edge.
        top_left = Point(0, 0)
        yield from generate_templates(top_left, OuterInner.OUTER)
        top_left = Point(0, num_rows * (slice_height + self.template_spacing))
        yield from generate_templates(top_left, OuterInner.INNER)


SliceformCylinderGenerator().run()
