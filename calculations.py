import math


def slot_width(material_thickness: float, lie_flat_angle: float):
    '''Calculate slot width, based on thickness and desired flatness.

    lie_flat_angle is the maximum angle that intersecting slices can be
    rotated to in their slots, assuming the sliceform is constructed from
    rigid material. Sliceforms constructed from soft materials can be
    pressed beyond lie_flat_angle.

                       ╱
                      ╱╲ material_thickness
                     ╱  ╲╱
                        ╱

             ▕    ╱   ╱  lie_flat_angle
   top       ▕ b ╱c  ╱       ▁▁
   ▔▔▔▔▔▔▔▔▔▔▔▔▔╱▔▔▔╱▔▔▔▔▔▔  ▕
              d╱   ╱         ▕ material_thickness
   bottom     ╱   ╱          ▕
   ▔▔▔▔▔▔▔▔▔▔╱   ╱▔▔▔▔▔▔▔▔▔  ▔▔
        left╱   ╱right

             ▕━━━━━━━▏slot_width
             ▕━━▕━━━━▏
               b   c
    '''
    # d is the length of the diagonal line from 'top' to 'bottom', along
    # 'left'.
    #
    # c is the length of the horizontal line from 'left' to 'right', along
    # 'top'.
    #
    # Draw the vertical line through the intersection of 'bottom' and 'left'. b
    # is the length of the horizontal line from this vertical line to the
    # intersection of 'top' and 'left'.
    #
    # slot_width = b + c
    # b = slot_width - c
    #
    # Construct a small right triangle surrounding c, with the horizontal line
    # segment c as the hypotenuse, and the right angle at the top:
    #
    #   sin(lie_flat_angle) = material_thickness / c
    #   c = material_thickness / sin(lie_flat_angle)  [Equation 0]
    #
    # Construct a right triangle surrounding d, with the diagonal line segment
    # d as the hypotenuse, and the right angle in the top left:
    #
    #   tan(lie_flat_angle) = material_thickness / b
    #   tan(lie_flat_angle) = material_thickness / (slot_width - c)
    #
    # Substitute Equation 0 and solve for slot_width:
    #
    #   tan(lie_flat_angle) = material_thickness /
    #                         (slot_width - (material_thickness /
    #                                        sin(lie_flat_angle)))
    #   slot_width - (material_thickness /
    #                 sin(lie_flat_angle)) = (material_thickness /
    #                                         tan(lie_flat_angle))
    #   slot_width = (material_thickness / tan(lie_flat_angle) +
    #                 material_thickness / sin(lie_flat_angle))
    return (material_thickness / math.tan(lie_flat_angle) +
            material_thickness / math.sin(lie_flat_angle))


def slot_angles(num_slices, loxodromic_angle):
    '''Calculate slot angles in radians.

    These are the angles for the slots in each slice, relative to the midpoint
    of the bounding box's left side.

    '''
    # There are (num_slices - 1) intersections, because a slice S intersects
    # all other slices going the other direction, except for the slice that's
    # exactly opposite S. It doesn't matter if the number of slices is even or
    # odd, there is always one slice exactly opposite S.
    angles = []
    for k in range(1, num_slices):
        t = k * 2 * math.pi / num_slices
        # This is the second equation on page 4 from
        # https://www.heldermann-verlag.de/jgg/jgg15/j15h1mone.pdf
        angles.append(
            math.acos(
                math.sin(t / 2) /
                math.sqrt(1 +
                          (math.pow(math.tan(loxodromic_angle), 2) *
                           math.pow(math.cos(t / 2), 2)))))

    adjusted_angles = []
    half_slices = math.floor(num_slices / 2)
    for i, angle in enumerate(angles):
        if i >= half_slices:
            adjusted_angles.append(-angle)
        else:
            adjusted_angles.append(angle)
    return adjusted_angles


def solve_quadratic(a, b, c):
    '''Return the positive solution to a quadratic equation

    a * x^2 + b * x + c = 0
    x = (-b ± sqrt(b^2 - 4ac)) / 2a

    '''
    return (-b + math.sqrt(b*b - 4 * a * c)) / (2 * a)
