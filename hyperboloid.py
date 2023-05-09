#!/usr/bin/env python3

'''Inkscape extension that generates sliceform hyperboloid templates.

Generates sliceform templates for a hyperboloid of one sheet.

'''

# Assembled similar to the cylinder model:
# https://www.youtube.com/watch?v=QfBc0fR64EQ

import math

import inkex
from inkex import elements
from inkex import transforms

from common import defaults
from common import path
from common import point

import calculations
import hyperboloid_calculations
import render

__version__ = '0.1'

epsilon = 0.000001


def near(x, y):
    return abs(x - y) < epsilon


class SliceformHyperboloidGenerator(inkex.extensions.GenerateExtension):
    def add_arguments(self, pars):
        pars.add_argument('--tab', type=str, dest='tab')
        pars.add_argument('--units', type=str,
                          dest='units', default='mm',
                          help='Units')
        pars.add_argument('--outer_edge_radius', type=float,
                          dest='outer_edge_radius', default='60',
                          help='Outer edge radius')
        pars.add_argument('--outer_waist_radius', type=float,
                          dest='outer_waist_radius', default='30',
                          help='Outer waist radius')
        pars.add_argument('--inner_radius', type=float,
                          dest='inner_radius', default='20',
                          help='Inner radius')
        pars.add_argument('--height', type=float,
                          dest='height', default='60',
                          help='height')
        pars.add_argument('--num_slices', type=int,
                          dest='num_slices', default='18',
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

    def render_slice(
            self, angles, slice_width, slice_height, fill_color,
            outer_inner: hyperboloid_calculations.OuterInner
    ) -> elements.PathElement:
        '''Draw a rectangular slice with slice_width and slice_height.

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

        '''
        half_slice_height = slice_height / 2

        # For each slot angle, collect three pairs of points:
        #  outer: Where the slot intersects the slice's outer edge.
        #  inner: Where the slot intersects the slice's inner edge.
        # middle: Midpoints between the outer and inner intersections.
        forward_intersections = []
        for angle in angles:
            outer_points = hyperboloid_calculations.slot_corners(
                self.outer_waist_radius, self.inner_radius, half_slice_height,
                hyperboloid_calculations.OuterInner.OUTER, angle,
                self.slot_width)
            if outer_points[0] is None and outer_points[1] is None:
                # Slot does not intersect the slice.
                continue

            inner_points = hyperboloid_calculations.slot_corners(
                self.outer_waist_radius, self.inner_radius, half_slice_height,
                hyperboloid_calculations.OuterInner.INNER, angle,
                self.slot_width)

            if outer_points[0] is None:
                assert inner_points[0] is None
                middle_points = [
                    None,
                    point.midpoint(inner_points[1], outer_points[1])]
            elif outer_points[1] is None:
                assert inner_points[1] is None
                middle_points = [
                    point.midpoint(inner_points[0], outer_points[0]),
                    None]
            else:
                middle_points = [
                    point.midpoint(inner_points[0], outer_points[0]),
                    point.midpoint(inner_points[1], outer_points[1])]

            forward_intersections.append(render.Intersection(
                outer=outer_points, middle=middle_points, inner=inner_points))

        # NOTE: The names 'top' and 'bottom' refer to display coordinates,
        # where the positive Y-axis points downward.
        if forward_intersections[0].outer[0] is None:
            # The first and last intersections clip the bottom left and top
            # left corners: one slot wall intersects the slice, but the other
            # does not.
            assert forward_intersections[0].middle[0] is None
            assert forward_intersections[0].inner[0] is None
            assert forward_intersections[0].outer[1] is not None
            assert forward_intersections[0].middle[1] is not None
            assert forward_intersections[0].inner[1] is not None

            assert forward_intersections[-1].outer[0] is not None
            assert forward_intersections[-1].middle[0] is not None
            assert forward_intersections[-1].inner[0] is not None
            assert forward_intersections[-1].outer[1] is None
            assert forward_intersections[-1].middle[1] is None
            assert forward_intersections[-1].inner[1] is None

            bottom_left = forward_intersections[0].outer[1]
            top_left = forward_intersections[-1].outer[0]
            inner_edge_corners = [forward_intersections[-1].inner[0],
                                  forward_intersections[0].inner[1]]

            # Remove first and last intersections, they are handled separately.
            forward_intersections = forward_intersections[1:][:-1]
        else:
            bottom_left = point.Point(self.inner_radius, half_slice_height)
            top_left = point.Point(self.inner_radius, -half_slice_height)
            inner_edge_corners = None

        # Start at the bottom left corner.
        commands = path.move_abs(bottom_left)

        # Draw the outer (bottom, right, top) edges.
        bottom_right = point.Point(self.inner_radius + slice_width,
                                   half_slice_height)
        top_right = point.Point(self.inner_radius + slice_width,
                                -half_slice_height)

        if outer_inner == hyperboloid_calculations.OuterInner.OUTER:
            # Draw the bottom edge.
            omit_bottom_right = False
            for intersection in forward_intersections:
                if not near(intersection.outer[0].y, half_slice_height):
                    # No more bottom edge intersections.
                    break
                commands += path.line_abs(intersection.outer[0])
                commands += path.line_abs(intersection.middle[0])
                commands += path.line_abs(intersection.middle[1])
                commands += path.line_abs(intersection.outer[1])

                if not near(intersection.outer[1].y, half_slice_height):
                    # The slot intersected the bottom_right corner, so don't
                    # draw the bottom_right corner.
                    omit_bottom_right = True
                    break

            if not omit_bottom_right:
                commands += path.line_abs(bottom_right)

            # Draw the right edge.
            found_right_edge = False
            omit_top_right = False
            for intersection in forward_intersections:
                if not found_right_edge:
                    if not near(intersection.outer[0].x,
                                self.inner_radius + slice_width):
                        continue
                    else:
                        found_right_edge = True

                if not near(intersection.outer[0].x,
                            self.inner_radius + slice_width):
                    # No more right edge intersections.
                    break
                commands += path.line_abs(intersection.outer[0])
                commands += path.line_abs(intersection.middle[0])
                commands += path.line_abs(intersection.middle[1])
                commands += path.line_abs(intersection.outer[1])

                if not near(intersection.outer[1].x,
                            self.inner_radius + slice_width):
                    # The slot intersected the top_right corner, so don't
                    # draw the top_right corner.
                    omit_top_right = True
                    break

            if not omit_top_right:
                commands += path.line_abs(top_right)

            # Draw the top edge.
            found_top_edge = False
            for intersection in forward_intersections:
                if not found_top_edge:
                    if not near(intersection.outer[0].y, -half_slice_height):
                        continue
                    else:
                        found_top_edge = True

                commands += path.line_abs(intersection.outer[0])
                commands += path.line_abs(intersection.middle[0])
                commands += path.line_abs(intersection.middle[1])
                commands += path.line_abs(intersection.outer[1])

            # Draw the top_left corner.
            commands += path.line_abs(top_left)

        else:
            # Draw the bottom edge.
            commands += path.line_abs(bottom_right)

            # Draw the right edge.
            commands += path.line_abs(top_right)

            # Draw the top edge.
            commands += path.line_abs(top_left)

        # Draw the left edge.
        if inner_edge_corners is not None:
            commands += path.line_abs(inner_edge_corners[0])

        reversed_intersections = render.reverse_intersections(
            forward_intersections)
        if outer_inner == hyperboloid_calculations.OuterInner.INNER:
            for intersection in reversed_intersections:
                commands += path.line_abs(intersection.inner[0])
                commands += path.line_abs(intersection.middle[0])
                commands += path.line_abs(intersection.middle[1])
                commands += path.line_abs(intersection.inner[1])

        if inner_edge_corners is not None:
            commands += path.line_abs(inner_edge_corners[1])

        commands += path.line_abs(bottom_left)
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

        self.outer_edge_radius = self.to_uu(self.options.outer_edge_radius)
        self.outer_waist_radius = self.to_uu(self.options.outer_waist_radius)
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

        assert self.outer_edge_radius > self.outer_waist_radius, \
            'Error: Outer edge radius must be larger than outer waist radius'
        assert self.outer_waist_radius > self.inner_radius, \
            'Error: Outer waist radius must be larger than inner radius'

        self.loxodromic_angle = hyperboloid_calculations.loxodromic_angle(
            self.height, self.outer_edge_radius, self.outer_waist_radius)

        self.slot_width = calculations.slot_width(self.material_thickness,
                                                  self.loxodromic_angle * 2)

        angles = calculations.slot_angles(self.num_slices,
                                          self.loxodromic_angle)

        slice_width = self.outer_waist_radius - self.inner_radius

        # Calculate the diagonal distance from the hyperboloid's center to
        # outer_edge_radius. This makes a right triangle with sides
        # outer_edge_radius and (height / 2), and hypotenuse
        # diagonal_edge_radius.
        diagonal_edge_radius = math.sqrt(self.outer_edge_radius ** 2 +
                                         (self.height / 2) ** 2)
        # Calculate half_slice_height. Make a right triangle with sides
        # outer_waist_radius and half_slice_height, and hypotenuse
        # diagonal_edge_radius.
        # diagonal_edge_radius² = outer_waist_radius² + half_slice_height²
        half_slice_height = math.sqrt(diagonal_edge_radius ** 2 -
                                      self.outer_waist_radius ** 2)
        slice_height = 2 * half_slice_height

        # Lay out templates in rows, with self.material_width as the maximum
        # row width.
        templates_per_row = math.floor(self.material_width /
                                       (slice_width + self.template_spacing))
        num_rows = math.ceil(self.num_slices / templates_per_row)

        def generate_templates(
                top_left,
                outer_inner: hyperboloid_calculations.OuterInner):
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
                        angles, slice_width, slice_height,
                        defaults.defaults['fill_colors'][outer_inner],
                        outer_inner)

                    translate = transforms.Transform()
                    translate.add_translate(top_left.x, top_left.y)
                    element.transform = translate
                    yield element

                    top_left.x += slice_width + self.template_spacing
                top_left.y += slice_height + self.template_spacing

        # Generate two sets of slice templates. The first set has slots on the
        # outer edge, and the second set has slots on the inner edge.
        top_left = point.Point(0, 0)
        yield from generate_templates(
            top_left, hyperboloid_calculations.OuterInner.OUTER)
        top_left = point.Point(
            0,
            num_rows * (slice_height + self.template_spacing))
        yield from generate_templates(
            top_left, hyperboloid_calculations.OuterInner.INNER)


SliceformHyperboloidGenerator().run()
