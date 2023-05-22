#!/usr/bin/env python3

'''Inkscape extension that generates sliceform cylinder templates.

Assembly video: https://www.youtube.com/watch?v=QfBc0fR64EQ

'''


import math
import inkex
from inkex import elements
from inkex import transforms

from common import defaults
from common import path
from common import point

import calculations
import cylinder_calculations
import render

__version__ = '0.3'


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
        pars.add_argument('--slice_shape', type=str,
                          dest='slice_shape', default='c',
                          help='Slice shape')
        pars.add_argument('--material_thickness', type=float,
                          dest='material_thickness', default='.25',
                          help='Thickness of material')
        pars.add_argument('--material_width', type=float,
                          dest='material_width', default='203',
                          help='Width of material')

    def to_uu(self, n: float):
        '''Convert from self.units to user units.'''
        return self.svg.unittouu(str(n) + self.units)

    def render_slice(self, slice_shape: str, angles, slice_height, fill_color,
                     outer_inner: render.OuterInner,
                     slice_num: int) -> elements.PathElement:
        outer_radius_x = self.outer_radius
        outer_radius_y = slice_height / 2
        inner_radius_x = self.inner_radius
        inner_radius_y = self.inner_radius / math.cos(self.loxodromic_angle)

        # For each slot angle, collect three pairs of points:
        #  outer: Where the slot intersects the slice's outer edge.
        #  inner: Where the slot intersects the slice's inner edge.
        # middle: Midpoints between the outer and inner intersections.
        forward_intersections = []
        for angle in angles:
            outer_points = cylinder_calculations.slot_corners(
                outer_radius_x, outer_radius_y, angle, self.slot_width)

            inner_points = cylinder_calculations.slot_corners(
                inner_radius_x, inner_radius_y, angle, self.slot_width)

            middle_points = [point.midpoint(inner_points[0], outer_points[0]),
                             point.midpoint(inner_points[1], outer_points[1])]

            forward_intersections.append(render.Intersection(
                outer=outer_points, middle=middle_points, inner=inner_points))

        # Start at the bottom of the outer edge.
        outer_bottom = point.Point(0, outer_radius_y)
        commands = path.move_abs(outer_bottom)

        if slice_shape == 'c':
            # Draw a backwards 'C' shape. The 'C' opens to the left.
            #
            # The outer (rightmost) edge is an elliptical arc with horizontal
            # radius outer_radius_x, and vertical radius outer_radius_y. The
            # ellipse is centered at the midpoint of the bounding box's left
            # side. The arc only uses the portion of the ellipse with
            # non-negative x.
            #
            # The inner (leftmost) edge is an elliptical arc with horizontal
            # radius inner_radius_x, and vertical radius inner_radius_y. The
            # ellipse is centered at the midpoint of the bounding box's left
            # side. The arc only uses the portion of the ellipse with
            # non-negative x.
            #
            # The outer and inner edges are connected by two vertical lines
            # along the bounding box's left side
            def is_inner(i):
                return outer_inner == render.OuterInner.INNER

            # Draw the outer edge, counterclockwise from the bottom.
            #
            # NOTE: The names 'top' and 'bottom' refer to display coordinates,
            # where the positive Y-axis points downward.
            outer_top = point.Point(0, -outer_radius_y)
            commands += render.elliptical_slotted_path(
                intersections=forward_intersections,
                outer_inner=render.OuterInner.OUTER, winding=path.Winding.CCW,
                radius_x=outer_radius_x, radius_y=outer_radius_y,
                end=outer_top, skip=is_inner)

            inner_top = point.Point(0, -inner_radius_y)
            commands += path.line_abs(inner_top)

            def is_outer(i):
                return not is_inner(i)

            # Draw the inner edge, clockwise from the top.
            reverse_intersections = render.reverse_intersections(
                forward_intersections)
            inner_bottom = point.Point(0, inner_radius_y)
            commands += render.elliptical_slotted_path(
                intersections=reverse_intersections,
                outer_inner=render.OuterInner.INNER, winding=path.Winding.CW,
                radius_x=inner_radius_x, radius_y=inner_radius_y,
                end=inner_bottom, skip=is_outer)
        elif slice_shape == 'ring':
            # Draw a ring-shaped slice centered at (0, 0).
            #
            # The outer edge is an ellipse with horizontal radius
            # outer_radius_x, and vertical radius outer_radius_y.
            #
            # The inner edge is an ellipse with horizontal radius
            # inner_radius_x, and vertical radius inner_radius_y.
            def is_outer(i):
                '''Returns True iff slot `i` is on the outer edge.'''
                return i < slice_num

            right_intersections = forward_intersections
            left_intersections = render.mirror_intersections(
                render.reverse_intersections(forward_intersections))

            # Draw the right half of the outer ellipse.
            outer_top = point.Point(0, -outer_radius_y)
            commands += render.elliptical_slotted_path(
                intersections=right_intersections,
                outer_inner=render.OuterInner.OUTER, winding=path.Winding.CCW,
                radius_x=outer_radius_x, radius_y=outer_radius_y,
                end=outer_top, skip=is_outer)

            # Draw the left half of the outer ellipse.
            commands += render.elliptical_slotted_path(
                intersections=left_intersections,
                outer_inner=render.OuterInner.OUTER, winding=path.Winding.CCW,
                radius_x=outer_radius_x, radius_y=outer_radius_y,
                end=outer_bottom, skip=is_outer)
            commands += 'Z'

            # Move to the bottom of the inner ellipse.
            inner_bottom = point.Point(0, inner_radius_y)
            commands += path.move_abs(inner_bottom)

            def is_inner(i):
                return not is_outer(i)

            # Draw the right half of the inner ellipse.
            inner_top = point.Point(0, -inner_radius_y)
            commands += render.elliptical_slotted_path(
                intersections=right_intersections,
                outer_inner=render.OuterInner.INNER, winding=path.Winding.CCW,
                radius_x=inner_radius_x, radius_y=inner_radius_y,
                end=inner_top, skip=is_inner)

            # Draw the left half of the inner ellipse.
            commands += render.elliptical_slotted_path(
                intersections=left_intersections,
                outer_inner=render.OuterInner.INNER, winding=path.Winding.CCW,
                radius_x=inner_radius_x, radius_y=inner_radius_y,
                end=inner_bottom, skip=is_inner)

        commands += 'Z'

        element = elements.PathElement()
        element.style = inkex.styles.Style(style={
            'stroke-width': self.stroke_width,
            'stroke': defaults.defaults['cut_color'],
            'fill': fill_color,
            'fill-rule': 'evenodd'})
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
        self.slice_shape = self.options.slice_shape
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

        slice_height = 2 * outer_radius_y

        if self.slice_shape == 'c':
            # Find the point where the horizontal line at inner_radius_y
            # intersects the outer radius. That point's x-coordinate is how far
            # we have to shift subsequent slices to the right so slices don't
            # overlap.
            additional_slice_width = (
                cylinder_calculations.intersect_ellipse_line(
                    outer_radius_x, outer_radius_y, 0, inner_radius_y).x)
            # The first slice requires the full slice width, so compensate by
            # decreasing the material width by the width of one full slice.
            material_width = self.material_width - outer_radius_x
        else:
            assert self.slice_shape == 'ring'
            additional_slice_width = 2 * outer_radius_x
            material_width = self.material_width - additional_slice_width

        # Lay out templates in rows, with self.material_width as the maximum
        # row width.
        #
        # Each additional slice requires 'slice width' additional horizontal
        # space.
        templates_per_row = (
            1 + math.floor(material_width /
                           (additional_slice_width + self.template_spacing)))
        if self.slice_shape == 'c':
            num_slices = self.num_slices
        else:
            num_slices = math.ceil(self.num_slices / 2)
        num_rows = math.ceil(num_slices / templates_per_row)

        def generate_templates(top_left, outer_inner: render.OuterInner):
            '''Render rows of slices starting at top_left.

            outer_inner determines whether the slots appear on the outer or
            inner edge of the slice.

            Returns the point where the top left corner of the next slice
            should be rendered.
            '''
            if self.slice_shape == 'c':
                slice_range = range(self.num_slices)
            else:
                if outer_inner == render.OuterInner.OUTER:
                    slice_range = range(0, self.num_slices, 2)
                else:
                    slice_range = range(1, self.num_slices, 2)
            templates_generated = 0
            for slice_num in slice_range:
                element = self.render_slice(
                    self.slice_shape, angles, slice_height,
                    defaults.defaults['fill_colors'][outer_inner],
                    outer_inner, slice_num)

                translate = transforms.Transform()
                translate.add_translate(top_left.x, top_left.y)
                element.transform = translate
                yield element

                templates_generated += 1

                if templates_generated < templates_per_row:
                    top_left.x += (additional_slice_width +
                                   self.template_spacing)
                else:
                    templates_generated = 0
                    top_left.x = 0
                    top_left.y += slice_height + self.template_spacing

        # Generate two sets of slice templates. The first set has slots on the
        # outer edge, and the second set has slots on the inner edge.
        top_left = point.Point(0, 0)
        yield from generate_templates(top_left, render.OuterInner.OUTER)
        top_left = point.Point(
            0, num_rows * (slice_height + self.template_spacing))
        yield from generate_templates(top_left, render.OuterInner.INNER)


SliceformCylinderGenerator().run()
