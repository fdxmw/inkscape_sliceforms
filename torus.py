#!/usr/bin/env python3

'''Inkscape extension that generates sliceform torus templates.

Paper with equations: https://www.heldermann-verlag.de/jgg/jgg15/j15h1mone.pdf
Assembly video: https://www.youtube.com/watch?v=WVE-HeVFJ1k

'''

import math
import inkex
from inkex import elements
from inkex import transforms

from common import defaults
from common import path
from common import point

import calculations
import render
import torus_calculations

__version__ = '0.3.1'


class SliceformTorusGenerator(inkex.extensions.GenerateExtension):
    def add_arguments(self, pars):
        pars.add_argument('--tab', type=str, dest='tab')
        pars.add_argument('--units', type=str,
                          dest='units', default='mm',
                          help='Units')
        pars.add_argument('--major_radius', type=float,
                          dest='major_radius', default='40',
                          help='Major radius')
        pars.add_argument('--minor_radius', type=float,
                          dest='minor_radius', default='17.5',
                          help='minor radius')
        pars.add_argument('--num_slices', type=int,
                          dest='num_slices', default='10',
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

    def render_slice(self, angles, fill_color, outer_inner: render.OuterInner,
                     top_point) -> elements.PathElement:
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
        #
        # NOTE: The names 'top' and 'bottom' refer to display coordinates,
        # where the positive Y-axis points downward.
        bottom_point = top_point
        top_point = point.Point(0, -top_point.y)

        # For each slot angle, collect three pairs of points:
        #  outer: Where the slot intersects the slice's outer edge.
        #  inner: Where the slot intersects the slice's inner edge.
        # middle: Midpoints between the outer and inner intersections.
        forward_intersections = []
        for angle in angles:
            outer_points = torus_calculations.slot_corners(
                self.major_radius, self.minor_radius, self.slot_width, angle)

            inner_points = torus_calculations.slot_corners(
                self.major_radius, -self.minor_radius, self.slot_width, angle)

            middle_points = [point.midpoint(inner_points[0], outer_points[0]),
                             point.midpoint(inner_points[1], outer_points[1])]

            forward_intersections.append(render.Intersection(
                outer=outer_points, middle=middle_points, inner=inner_points))

        # Start at the bottom point.
        commands = path.move_abs(bottom_point)

        def is_inner(i):
            '''Returns True iff slot `i` is on the inner edge.'''
            return outer_inner == render.OuterInner.INNER

        # Draw the outer (larger) arc of the crescent moon, counterclockwise
        # from the bottom point.
        if outer_inner == render.OuterInner.OUTER:
            commands += render.elliptical_slotted_path(
                intersections=forward_intersections,
                outer_inner=render.OuterInner.OUTER,
                winding=path.Winding.CCW, radius_x=self.major_radius,
                radius_y=self.major_radius, end=top_point, skip=is_inner)
        else:
            commands += path.arc_abs(
                self.major_radius, self.major_radius,
                path.Size.LARGE, path.Winding.CCW, top_point)

        def is_outer(i):
            return not is_inner(i)

        # Draw the inner (smaller) arc of the crescent moon, clockwise from the
        # top point.
        reverse_intersections = render.reverse_intersections(
            forward_intersections)
        commands += render.elliptical_slotted_path(
            intersections=reverse_intersections,
            outer_inner=render.OuterInner.INNER, winding=path.Winding.CW,
            radius_x=self.major_radius, radius_y=self.major_radius,
            end=bottom_point, skip=is_outer)

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

        self.major_radius = self.to_uu(self.options.major_radius)
        self.minor_radius = self.to_uu(self.options.minor_radius)
        self.num_slices = self.options.num_slices
        self.material_thickness = self.to_uu(self.options.material_thickness)
        self.material_width = self.to_uu(self.options.material_width)

        # Spacing between templates.
        self.template_spacing = self.svg.unittouu(
            defaults.defaults['template_spacing'])

        assert self.num_slices > 0, \
            'Error: num_slices must be greater than zero'

        assert self.major_radius > self.minor_radius, \
            'Error: Major radius must be larger than minor radius'

        # loxodromic_angle is the slice angle, relative to the base of the
        # torus.
        #
        # Note: Slice edges are tangent to the surface of the torus. This
        # implies that, if you look at a cross-section, the tip of each slice
        # contacts the surface at right angles, so the tip contact points are
        # *not* at the highest and lowest points of the surface - they are
        # slightly inside the hole.
        #
        # This equation is equivalent to the first equation on page 3 from
        # https://www.heldermann-verlag.de/jgg/jgg15/j15h1mone.pdf
        self.loxodromic_angle = math.asin(self.minor_radius /
                                          self.major_radius)

        self.slot_width = calculations.slot_width(self.material_thickness,
                                                  self.loxodromic_angle * 2)

        angles = calculations.slot_angles(self.num_slices,
                                          self.loxodromic_angle)

        # top_point is the top left point where the inner and outer edges
        # meet. Note that the top left corner of the bounding box is a
        # different point. Calculate this point's coordinates by intersecting a
        # vertical line through (0, 0) with the outer edge.
        top_point = torus_calculations.intersect_circle_line(
            self.major_radius, self.minor_radius, math.pi / 2, 0)

        # Find the point where the horizontal line through top_point intersects
        # with the current slice's outer edge. That point's x-coordinate is how
        # far we have to shift subsequent slices to the right so slices don't
        # overlap.
        additional_slice_width = torus_calculations.intersect_circle_line(
            self.major_radius, self.minor_radius, 0, top_point.y).x
        slice_height = self.major_radius * 2

        # Lay out templates in rows, with self.material_width as the maximum
        # row width.

        # The first slice requires the full slice width, so compensate by
        # decreasing the material width by the width of one full slice. Find
        # the point where the horizontal line through (0, 0) intersects the
        # outer edge.
        first_slice_width = torus_calculations.intersect_circle_line(
            self.major_radius, self.minor_radius, 0, 0).x
        material_width = self.material_width - first_slice_width
        templates_per_row = (
            1 + math.floor(material_width /
                           (additional_slice_width + self.template_spacing)))
        num_rows = math.ceil(self.num_slices / templates_per_row)

        # Generate two rows of slice templates. The top row has slots on the
        # outer edge, and the bottom row has slots on the inner edge.
        def generate_templates(top_left: point.Point,
                               outer_inner: render.OuterInner):
            templates_generated = 0
            while templates_generated < self.num_slices:
                top_left.x = 0
                num_templates = min(templates_per_row,
                                    self.num_slices - templates_generated)
                templates_generated += num_templates
                for _ in range(num_templates):
                    element = self.render_slice(
                        angles, defaults.defaults['fill_colors'][outer_inner],
                        outer_inner, top_point)

                    translate = transforms.Transform()
                    translate.add_translate(top_left.x, top_left.y)
                    element.transform = translate
                    yield element

                    top_left.x += (additional_slice_width +
                                   self.template_spacing)
                top_left.y += slice_height + self.template_spacing

        top_left = point.Point(0, 0)
        yield from generate_templates(top_left, render.OuterInner.OUTER)
        top_left = point.Point(
            0, num_rows * (slice_height + self.template_spacing))
        yield from generate_templates(top_left, render.OuterInner.INNER)


SliceformTorusGenerator().run()
