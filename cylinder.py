#!/usr/bin/env python3

'''Inkscape extension that generates sliceform cylinder templates.

Assembly video: https://www.youtube.com/watch?v=QfBc0fR64EQ

'''


import math
import collections
import enum

import inkex
from inkex import elements
from inkex import transforms

from common import defaults
from common import path
from common import point

import calculations
import cylinder_calculations

__version__ = '0.1'


class OuterInner(enum.IntEnum):
    OUTER = 0
    INNER = 1


class SliceformCylinderGenerator(inkex.extensions.GenerateExtension):
    def add_arguments(self, pars):
        pars.add_argument('--tab', type=str, dest='tab')
        pars.add_argument('--units', type=str,
                          dest='units', default='mm',
                          help='Units')
        pars.add_argument('--outer_radius', type=float,
                          dest='outer_radius', default='35',
                          help='Outer radius')
        pars.add_argument('--inner_radius', type=float,
                          dest='inner_radius', default='26',
                          help='Inner radius')
        pars.add_argument('--height', type=float,
                          dest='height', default='40',
                          help='height')
        pars.add_argument('--num_slices', type=int,
                          dest='num_slices', default='14',
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

    def render_slice(self, angles, slice_height, fill_color,
                     outer_inner: OuterInner) -> elements.PathElement:
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

        def to_display_coordinates(p: point.Point) -> point.Point:
            '''Translate a calculated point.

            Calculations assume (0, 0) is centered at the midpoint of the
            bounding box's left side. Translate so (0, 0) is at the top left
            corner of the bounding box.

            '''
            return point.Point(p.x, p.y + outer_radius_y)

        # For each slot angle, collect three pairs of points:
        #  outer: Where the slot intersects the slice's outer edge.
        #  inner: Where the slot intersects the slice's inner edge.
        # middle: Midpoints between the outer and inner intersections.
        Intersection = collections.namedtuple(
            'Intersection', ['outer', 'middle', 'inner'])
        intersections = []
        for angle in angles:
            outer_points = cylinder_calculations.slot_corners(
                outer_radius_x, outer_radius_y, angle, self.slot_width)
            outer_points = [to_display_coordinates(op) for op in outer_points]

            inner_points = cylinder_calculations.slot_corners(
                inner_radius_x, inner_radius_y, angle, self.slot_width)
            inner_points = [to_display_coordinates(ip) for ip in inner_points]

            middle_points = [point.midpoint(inner_points[0], outer_points[0]),
                             point.midpoint(inner_points[1], outer_points[1])]

            intersections.append(Intersection(
                outer=outer_points, middle=middle_points, inner=inner_points))

        # Start at the bottom left point.
        bottom_left = point.Point(0, slice_height)
        commands = path.move_abs(bottom_left)

        # Draw the larger arc, counterclockwise from the bottom left corner.
        if outer_inner == OuterInner.OUTER:
            for intersection in intersections:
                commands += path.arc_abs(
                    outer_radius_x, outer_radius_y,
                    path.Size.SMALL, path.Winding.CCW, intersection.outer[0])
                commands += path.line_abs(intersection.middle[0])
                commands += path.line_abs(intersection.middle[1])
                commands += path.line_abs(intersection.outer[1])
            # Draw the last segment of the larger arc, ending at (0, 0).
            # point.
            commands += path.arc_abs(
                outer_radius_x, outer_radius_y,
                path.Size.SMALL, path.Winding.CCW, point.Point(0, 0))
        else:
            commands += path.arc_abs(
                outer_radius_x, outer_radius_y,
                path.Size.LARGE, path.Winding.CCW, point.Point(0, 0))

        commands += path.vline_rel(vertical_gap)

        # Draw the smaller arc, clockwise from top_left.
        if outer_inner == OuterInner.INNER:
            for intersection in reversed(intersections):
                commands += path.arc_abs(
                    inner_radius_x, inner_radius_y,
                    path.Size.SMALL, path.Winding.CW, intersection.inner[0])
                commands += path.line_abs(intersection.middle[0])
                commands += path.line_abs(intersection.middle[1])
                commands += path.line_abs(intersection.inner[1])
        # Draw the last segment of the smaller arc, ending at the bottom point.
        bottom_left_inner = point.Point(0, vertical_gap + inner_radius_y * 2)
        commands += path.arc_abs(
            inner_radius_x, inner_radius_y,
            path.Size.SMALL, path.Winding.CW, bottom_left_inner)
        commands += 'Z'

        element = elements.PathElement()
        element.style = inkex.styles.Style(style={
            'stroke-width': self.stroke_width,
            'stroke': defaults.defaults['cut_color'],
            'fill': fill_color})
        element.set_path(commands)
        return element

    def generate(self):
        self.stroke_width = str(self.svg.unittouu(
            defaults.defaults['stroke_width']))
        self.units = self.options.units

        self.outer_radius = self.to_uu(self.options.outer_radius)
        self.inner_radius = self.to_uu(self.options.inner_radius)
        self.height = self.to_uu(self.options.height)
        self.num_slices = self.options.num_slices
        self.material_thickness = self.to_uu(self.options.material_thickness)
        self.material_width = self.to_uu(self.options.material_width)

        # Spacing between templates.
        self.template_spacing = self.svg.unittouu(
            defaults.defaults['template_spacing'])

        assert self.num_slices > 0, \
            'Error: num_slices must be greater than zero'

        assert self.outer_radius > self.inner_radius, \
            'Error: Outer radius must be larger than inner radius'

        self.loxodromic_angle = cylinder_calculations.loxodromic_angle(
            self.height, self.outer_radius)

        self.slot_width = calculations.slot_width(self.material_thickness,
                                                  self.loxodromic_angle * 2)

        angles = calculations.slot_angles(self.num_slices,
                                          self.loxodromic_angle)

        outer_radius_x = self.outer_radius
        outer_radius_y = math.sqrt(self.outer_radius * self.outer_radius +
                                   (self.height / 2) * (self.height / 2))
        inner_radius_y = self.inner_radius / math.cos(self.loxodromic_angle)
        # Find the point where the horizontal line at inner_radius_y intersects
        # the outer radius. That point's x-coordinate is how far we have to
        # shift subsequent slices to the right so slices don't overlap.
        additional_slice_width = cylinder_calculations.intersect_ellipse_line(
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
                    element = self.render_slice(
                        angles, slice_height,
                        defaults.defaults['fill_colors'][outer_inner],
                        outer_inner)

                    translate = transforms.Transform()
                    translate.add_translate(top_left.x, top_left.y)
                    element.transform = translate
                    yield element

                    top_left.x += (additional_slice_width +
                                   self.template_spacing)
                top_left.y += slice_height + self.template_spacing

        # Generate two sets of slice templates. The first set has slots on the
        # outer edge, and the second set has slots on the inner edge.
        top_left = point.Point(0, 0)
        yield from generate_templates(top_left, OuterInner.OUTER)
        top_left = point.Point(
            0, num_rows * (slice_height + self.template_spacing))
        yield from generate_templates(top_left, OuterInner.INNER)


SliceformCylinderGenerator().run()
