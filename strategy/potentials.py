import math
import numpy as np


PITCH_ROWS = 480+1 #pixels
PITCH_COLS = 640+1 #pixels

'''POTENTIALS'''

# radial - constant gradient everywhere  coming out from one single spot
# 3 3 3 3 3 3 3
# 3 3 2 1 2 3 3
# 3 3 1 0 1 3 3
# 3 3 2 1 2 3 3
# 3 3 3 3 3 3 3

class radial:
    def __init__(self, (pos_x, pos_y), g, k):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.gradient = g
        self.constant = k

    def force_at(self, x, y):
        direction = (x-self.pos_x, y-self.pos_y)
        distance_to = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
        if distance_to != 0:
            dx = (self.constant*direction[0])/math.pow(distance_to, self.gradient + 2)
            dy = (self.constant*direction[1])/math.pow(distance_to, self.gradient + 2)
            return dx, dy
        else:
            return 0, 0

    def add_force(self, dx, dy):
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                direction = (x-self.pos_x, y-self.pos_y)
                distance_to = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
                if distance_to != 0:
                    dx[y, x] += (self.constant*direction[0])/math.pow(distance_to, self.gradient + 2)
                    dy[y, x] += (self.constant*direction[1])/math.pow(distance_to, self.gradient + 2)
        return dx, dy

    def field_at(self, x, y):
        distance_to = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
        if distance_to != 0:
            local_potential = self.constant/math.pow(distance_to, self.gradient)
            return local_potential
        else:
            return 0

    def add_field(self, local_potential):
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                distance_to = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
                if distance_to != 0:
                    local_potential[y, x] += self.constant/math.pow(distance_to, self.gradient)
        return local_potential


# infinite axial - field is only implemented between start and end points everywhere else contribution is zero
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0
# 1 1 1 1 1 1 1
# 3 3 3 3 3 3 3

class infinite_axial_inside:
    def __init__(self, (start_x, start_y), (end_x, end_y), influence_range, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.dir_x = end_x - start_x
        self.dir_y = end_y - start_y
        self.influence_range = influence_range
        self.gradient = g
        self.constant = k

    def force_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_end = rotate_vector(-angle, self.end_x, self.end_y)
        rotated_point = rotate_vector(-angle, x, y)
        distance_to = abs(rotated_point[1] - rotated_start[1])
        direction = (0, rotated_point[1] - rotated_start[1])
        if rotated_start[0] < rotated_end[0]:
            if rotated_start[0] < rotated_point[0] < rotated_end[0] and distance_to != 0:
                addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
                dx = addx
                dy = addy
                return dx, dy
            else:
                return 0, 0
        else:
            if rotated_end[0] < rotated_point[0] < rotated_start[0] and distance_to != 0:
                addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
                dx = addx
                dy = addy
                return dx, dy
            else:
                return 0, 0

    def add_force(self, dx, dy):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_end = rotate_vector(-angle, self.end_x, self.end_y)
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - rotated_start[1])
                direction = (0, rotated_point[1] - rotated_start[1])
                if rotated_start[0] < rotated_end[0]:
                    if rotated_start[0] < rotated_point[0] < rotated_end[0] and distance_to != 0:
                        addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
                        dx[y,x] += addx
                        dy[y,x] += addy
                else:
                    if rotated_end[0] < rotated_point[0] < rotated_start[0] and distance_to != 0:
                        addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
                        dx[y,x] += addx
                        dy[y,x] += addy

        return dx, dy

    def field_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_end = rotate_vector(-angle, self.end_x, self.end_y)
        rotated_point = rotate_vector(-angle, x, y)
        distance_to = abs(rotated_point[1] - rotated_start[1])
        if rotated_start[0] < rotated_end[0]:
            if rotated_start[0] < rotated_point[0] < rotated_end[0] and distance_to < self.influence_range and distance_to != 0:
                local_potential = self.constant/math.pow(distance_to, self.gradient)
                return local_potential
            else:
                return 0
        else:
            if rotated_end[0] < rotated_point[0] < rotated_start[0] and distance_to < self.influence_range and distance_to != 0:
                local_potential = self.constant/math.pow(distance_to, self.gradient)
                return local_potential
            else:
                return 0

    def add_field(self, local_potential):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_end = rotate_vector(-angle, self.end_x, self.end_y)
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - rotated_start[1])
                if rotated_start[0] < rotated_end[0]:
                    if rotated_start[0] < rotated_point[0] < rotated_end[0] and distance_to < self.influence_range and distance_to != 0:
                        local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)
                else:
                    if rotated_end[0] < rotated_point[0] < rotated_start[0] and distance_to < self.influence_range and distance_to != 0:
                        local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)

        return local_potential

# infinite axial - field is only implemented between start and end points everywhere else contribution is zero
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0
# 1 1 1 1 1 1 1
# 3 3 3 3 3 3 3

class infinite_axial_outside:
    def __init__(self, (start_x, start_y), (end_x, end_y), influence_range, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.dir_x = end_x - start_x
        self.dir_y = end_y - start_y
        self.influence_range = influence_range
        self.gradient = g
        self.constant = k

    def force_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_point = rotate_vector(-angle, x, y)
        distance_to = abs(rotated_point[1] - rotated_start[1])
        direction = (0, rotated_point[1]-rotated_start[1])
        if distance_to != 0:
            addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
            dx = addx
            dy = addy
            return dx, dy
        else:
            return 0, 0

    def add_force(self, dx, dy):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - rotated_start[1])
                direction = (0, rotated_point[1]-rotated_start[1])
                if distance_to != 0:
                    addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
                    dx[y,x] += addx
                    dy[y,x] += addy

        return dx, dy

    def field_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_point = rotate_vector(-angle, x, y)
        distance_to = abs(rotated_point[1] - rotated_start[1])
        if distance_to < self.influence_range and distance_to != 0:
            local_potential = self.constant/math.pow(distance_to, self.gradient)
            return local_potential
        else:
            return 0

    def add_field(self, local_potential):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        rotated_start = rotate_vector(-angle, self.start_x, self.start_y)
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - rotated_start[1])
                if distance_to < self.influence_range and distance_to != 0:
                    local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)

        return local_potential

# # finite axial inside - field is between reference points and exists everywhere
# 3 3 3 2 3 3 3
# 3 2 1 1 1 2 3
# 0 0 0 0 0 0 0
# 3 2 1 1 1 2 3
# 3 3 3 2 3 3 3

class finite_axial_inside:
    def __init__(self, (start_x, start_y), (ref_x, ref_y), g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = ref_x
        self.end_y = ref_y
        self.dir_x = start_x - ref_x
        self.dir_y = start_y - ref_y
        self.gradient = g
        self.constant = k

    def force_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        rotated_point = rotate_vector(-angle, x, y)
        a = rotated_point[0]-left_ref
        b = right_ref - rotated_point[0]
        distance_to = rotated_point[1] - start_field[1]
        if distance_to != 0 and a != 0 or distance_to != 0 and b != 0:
            outx = self.constant*((1/math.pow(math.sqrt(b**2 + distance_to**2), self.gradient))-(1/math.pow(math.sqrt(a**2 + distance_to**2), self.gradient)))
            outy = (self.constant*((b/math.pow(math.sqrt(b**2 + distance_to**2), self.gradient))+(a/math.pow(math.sqrt(a**2 + distance_to**2), self.gradient))))/distance_to
            addx, addy = rotate_vector(angle, outx, outy)
            dx = addx
            dy = addy
            return dx, dy
        else:
            return 0, 0

    def add_force(self, dx, dy):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                a = rotated_point[0]-left_ref
                b = right_ref - rotated_point[0]
                distance_to = rotated_point[1] - start_field[1]
                if distance_to != 0 and a != 0 or distance_to != 0 and b != 0:
                    outx = self.constant*((1/math.pow(math.sqrt(b**2 + distance_to**2), self.gradient))-(1/math.pow(math.sqrt(a**2 + distance_to**2), self.gradient)))
                    outy = (self.constant*((b/math.pow(math.sqrt(b**2 + distance_to**2), self.gradient))+(a/math.pow(math.sqrt(a**2 + distance_to**2), self.gradient))))/distance_to
                    addx, addy = rotate_vector(angle, outx, outy)
                    dx[y,x] += addx
                    dy[y,x] += addy

        return dx, dy

    def field_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]
        rotated_point = rotate_vector(-angle, x, y)
        b = right_ref - rotated_point[0]
        a = left_ref - rotated_point[0]
        distance_to = rotated_point[1] - start_field[1]
        denominator = (a + math.sqrt(a**2 + distance_to**2))
        numerator = (b + math.sqrt(b**2 + distance_to**2))
        if denominator != 0 and numerator != 0:
            local_potential = self.constant*math.log(numerator/(denominator*self.gradient), math.e)
            return local_potential
        else:
            return 0

    def add_field(self, local_potential):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                b = right_ref - rotated_point[0]
                a = left_ref - rotated_point[0]
                distance_to = rotated_point[1] - start_field[1]
                denominator = (a + math.sqrt(a**2 + distance_to**2))
                numerator = (b + math.sqrt(b**2 + distance_to**2))
                if denominator != 0 and numerator != 0:
                    local_potential[y,x] += self.constant*math.log(numerator/(denominator*self.gradient), math.e)

        return local_potential


# finite axial outside - field will start at start point and exist on the opposite side to the ref point anc continue of
# the pitch
# 3 3 3 2 3 3 3
# 3 2 1 1 1 2 3
# 0 0 0 0 0 0 0
# 3 2 1 1 1 2 3
# 3 3 3 2 3 3 3

class finite_axial_outside:
    def __init__(self, (start_x, start_y), (ref_x, ref_y), influence, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.ref_x = ref_x
        self.ref_y = ref_y
        self.dir_x = start_x - ref_x
        self.dir_y = start_y - ref_y
        self.gradient = g
        self.constant = k
        self.influence = influence

    def force_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.start_x + normalize((self.dir_x, self.dir_y))[0]*600,  self.start_y + normalize((self.dir_x, self.dir_y))[1]*600)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        rotated_point = rotate_vector(-angle, x, y)
        a = rotated_point[0]-left_ref
        b = right_ref - rotated_point[0]
        distance_to = rotated_point[1] - start_field[1]
        if distance_to != 0 and a != 0 or distance_to != 0 and b != 0:
            outx = self.constant*((1/math.pow(math.sqrt(b**2 + distance_to**2), self.gradient))-(1/math.pow(math.sqrt(a**2 + distance_to**2), self.gradient)))
            outy = (self.constant*((b/math.pow(math.sqrt(b**2 + distance_to**2), self.gradient))+(a/math.pow(math.sqrt(a**2 + distance_to**2), self.gradient))))/distance_to
            addx, addy = rotate_vector(angle, outx, outy)
            dx = addx
            dy = addy
            return dx, dy
        else:
            return 0, 0

    def add_force(self, dx, dy):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.start_x + normalize((self.dir_x, self.dir_y))[0]*600,  self.start_y + normalize((self.dir_x, self.dir_y))[1]*600)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                a = rotated_point[0]-left_ref
                b = right_ref - rotated_point[0]
                distance_to = rotated_point[1] - start_field[1]
                if distance_to != 0 and a != 0 or distance_to != 0 and b != 0:
                    outx = self.constant*((1/math.pow(math.sqrt(b**2 + distance_to**2), self.gradient))-(1/math.pow(math.sqrt(a**2 + distance_to**2), self.gradient)))
                    outy = (self.constant*((b/math.pow(math.sqrt(b**2 + distance_to**2), self.gradient))+(a/math.pow(math.sqrt(a**2 + distance_to**2), self.gradient))))/distance_to
                    addx, addy = rotate_vector(angle, outx, outy)
                    dx[y,x] += addx
                    dy[y,x] += addy

        return dx, dy

    def field_at(self, x, y):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.start_x + normalize((self.dir_x, self.dir_y))[0]*600,  self.start_y + normalize((self.dir_x, self.dir_y))[1]*600)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        rotated_point = rotate_vector(-angle, x, y)
        b = right_ref - rotated_point[0]
        a = left_ref - rotated_point[0]
        distance_to = rotated_point[1] - start_field[1]
        denominator = (a + math.sqrt(a**2 + distance_to**2))
        numerator = (b + math.sqrt(b**2 + distance_to**2))
        if denominator != 0 and numerator != 0:
            result = self.constant*math.log(numerator/(denominator*self.gradient), math.e)
            local_potential = result
            return local_potential
        else:
            return 0

    def add_field(self, local_potential):
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.start_x + normalize((self.dir_x, self.dir_y))[0]*600,  self.start_y + normalize((self.dir_x, self.dir_y))[1]*600)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                b = right_ref - rotated_point[0]
                a = left_ref - rotated_point[0]
                distance_to = rotated_point[1] - start_field[1]
                denominator = (a + math.sqrt(a**2 + distance_to**2))
                numerator = (b + math.sqrt(b**2 + distance_to**2))
                if denominator != 0 and numerator != 0:
                    result = self.constant*math.log(numerator/(denominator*self.gradient), math.e)
                    local_potential[y,x] += result

        return local_potential

# solid - modeled as a circle, from center 'forbidden' is unreachable and outside the influence area is unreachable
# 0 2 3 3 3 2 0
# 1 3 9 9 9 3 1
# 2 3 9 9 9 3 2
# 1 3 9 9 9 3 1
# 0 2 3 3 3 2 0

class solid_field:
    def __init__(self, (pos_x, pos_y), g, k, forbidden, influence_area):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.gradient = g
        self.constant = k
        self.forbidden = forbidden
        self.influence_area = influence_area

    def force_at(self, x, y):
        direction = (x-self.pos_x, y-self.pos_y)
        separation = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
        if separation > self.forbidden and separation-self.forbidden != 0:
            dx = (self.constant*direction[0])/math.pow(separation-self.forbidden, self.gradient+2)
            dy = (self.constant*direction[1])/math.pow(separation-self.forbidden, self.gradient+2)
            return dx, dy
        elif separation != 0:
            dx = direction[0]*(self.constant + self.constant/math.pow(separation, self.gradient+2))
            dy = direction[1]*(self.constant + self.constant/math.pow(separation, self.gradient+2))
            return dx, dy
        else:
            return 0, 0

    def add_force(self, dx, dy):
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                direction = (x-self.pos_x, y-self.pos_y)
                separation = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
                if separation > self.forbidden and separation-self.forbidden != 0:
                    dx[y,x] += (self.constant*direction[0])/math.pow(separation-self.forbidden, self.gradient+2)
                    dy[y,x] += (self.constant*direction[1])/math.pow(separation-self.forbidden, self.gradient+2)
                elif separation != 0:
                    dx[y,x] += direction[0]*(self.constant + self.constant/math.pow(separation, self.gradient+2))
                    dy[y,x] += direction[1]*(self.constant + self.constant/math.pow(separation, self.gradient+2))
        return dx, dy

    def field_at(self, x, y):
        separation = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
        if separation > self.forbidden and separation != 0:
            local_potential = self.constant/math.pow(separation-self.forbidden, self.gradient)
            return local_potential
        else:
            if self.constant <= 0:
                local_potential = -100*self.constant
                return local_potential
            else:
                local_potential = 100*self.constant
                return local_potential

    def add_field(self, local_potential):
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                separation = math.sqrt((x-self.pos_x)**2 + (y-self.pos_y)**2)
                if separation > self.forbidden and separation != 0:
                    local_potential[y,x] += self.constant/math.pow(separation-self.forbidden, self.gradient)
                else:
                    if self.constant <= 0:
                        local_potential[y,x] += -100*self.constant
                    else:
                        local_potential[y,x] += 100*self.constant

        return local_potential

# step - an infinite line drawn through the point in the first argument in the direction of the vector in the
# second argument. The clockwise segment to the vector is cut off where as the anticlockwise segment acts like a
# infinite axial field over the entire pitch. also must be between start and end
# 9 9 9 9 9 9 9
# 9 9 9 9 9 9 9
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0


class step_field_inside:
    def __init__(self, (start_x, start_y), (end_x, end_y), (dir_x, dir_y), influence_range, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.influence_range = influence_range
        self.gradient = g
        self.constant = k

    def force_at(self, x, y):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field
            left_ref = end_field
        else:
            left_ref = start_field
            right_ref = end_field

        rotated_point = rotate_vector(-angle, x, y)
        distance_to = abs(rotated_point[1] - start_field[1])
        step = dot_product(step_direction, (x - self.start_x, y - self.start_y))
        if left_ref[0] < rotated_point[0] < right_ref[0] and distance_to != 0:
            direction = (0, rotated_point[1] - start_field[1])
            if step > 0: # in direction step_direction
                addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
                dx = addx
                dy = addy
                return dx, dy
            else:
                addx, addy = rotate_vector(angle, 0, -direction[1]*(self.constant + self.constant/math.pow(distance_to, self.gradient+2)))
                dx = addx
                dy = addy
                return dx, dy
        elif rotated_point[0] <= left_ref[0] and step > 0:
            direction = (rotated_point[0] - left_ref[0], rotated_point[1] - left_ref[1])
            distance_to = np.linalg.norm(direction)
            if distance_to != 0:
                addx, addy = rotate_vector(angle, (self.constant*direction[0])/math.pow(distance_to, self.gradient + 2), (self.constant*direction[1])/math.pow(distance_to, self.gradient + 2))
                dx = addx
                dy = addy
                return dx, dy
            else:
                return 0, 0
        elif rotated_point[0] >= right_ref and step > 0:
            direction = (rotated_point[0] - right_ref[0], rotated_point[1] - right_ref[1])
            distance_to = np.linalg.norm(direction)
            if distance_to != 0:
                addx, addy = rotate_vector(angle, (self.constant*direction[0])/math.pow(distance_to, self.gradient + 2), (self.constant*direction[1])/math.pow(distance_to, self.gradient + 2))
                dx = addx
                dy = addy
                return dx, dy
            else:
                return 0, 0
        else:
            return 0, 0

    def add_force(self, dx, dy):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field
            left_ref = end_field
        else:
            left_ref = start_field
            right_ref = end_field

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - start_field[1])
                step = dot_product(step_direction, (x - self.start_x, y - self.start_y))
                if left_ref[0] < rotated_point[0] < right_ref[0] and distance_to != 0:
                    direction = (0, rotated_point[1] - start_field[1])
                    if step > 0: # in direction step_direction
                        addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
                        dx[y,x] += addx
                        dy[y,x] += addy
                    else:
                        addx, addy = rotate_vector(angle, 0, -direction[1]*(self.constant + self.constant/math.pow(distance_to, self.gradient+2)))
                        dx[y,x] += addx
                        dy[y,x] += addy
                elif rotated_point[0] <= left_ref[0] and step > 0:
                    direction = (rotated_point[0] - left_ref[0], rotated_point[1] - left_ref[1])
                    distance_to = np.linalg.norm(direction)
                    if distance_to != 0:
                        addx, addy = rotate_vector(angle, (self.constant*direction[0])/math.pow(distance_to, self.gradient + 2), (self.constant*direction[1])/math.pow(distance_to, self.gradient + 2))
                        dx[y,x] += addx
                        dy[y,x] += addy
                elif rotated_point[0] >= right_ref and step > 0:
                    direction = (rotated_point[0] - right_ref[0], rotated_point[1] - right_ref[1])
                    distance_to = np.linalg.norm(direction)
                    if distance_to != 0:
                        addx, addy = rotate_vector(angle, (self.constant*direction[0])/math.pow(distance_to, self.gradient + 2), (self.constant*direction[1])/math.pow(distance_to, self.gradient + 2))
                        dx[y,x] += addx
                        dy[y,x] += addy

        return dx, dy

    def field_at(self, x, y):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        rotated_point = rotate_vector(-angle, x, y)
        distance_to = abs(rotated_point[1] - start_field[1])
        step = dot_product(step_direction, (x - self.start_x, y - self.start_y))
        if left_ref < rotated_point[0] < right_ref and distance_to != 0:
            if step > 0: # in direction step_direction
                if distance_to < self.influence_range:
                    local_potential = self.constant/math.pow(distance_to, self.gradient)
                    return local_potential
                else:
                    return 0
            else:
                if self.constant <= 0:
                    local_potential = 100*self.constant + self.constant/math.pow(distance_to, self.gradient)
                    return local_potential
                else:
                    local_potential = 100*self.constant - self.constant/math.pow(distance_to, self.gradient)
                    return local_potential

        elif rotated_point[0] <= left_ref and step > 0:
            distance_to = math.sqrt((rotated_point[0]-left_ref)**2 + distance_to**2)
            if distance_to != 0:
                local_potential = self.constant/math.pow(distance_to, self.gradient)
                return local_potential
            else:
                return 0
        elif rotated_point[0] >= right_ref and step > 0:
            distance_to = math.sqrt((rotated_point[0]-right_ref)**2 + distance_to**2)
            if distance_to != 0:
                local_potential = self.constant/math.pow(distance_to, self.gradient)
                return local_potential
            else:
                return 0
        else:
            return 0

    def add_field(self, local_potential):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        end_field = rotate_vector(-angle, self.end_x, self.end_y)

        if start_field[0] > end_field[0]:
            right_ref = start_field[0]
            left_ref = end_field[0]
        else:
            left_ref = start_field[0]
            right_ref = end_field[0]

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):
                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - start_field[1])
                step = dot_product(step_direction, (x - self.start_x, y - self.start_y))
                if left_ref < rotated_point[0] < right_ref and distance_to != 0:
                    if step > 0: # in direction step_direction
                        if distance_to < self.influence_range:
                            local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)
                    else:
                        if self.constant <= 0:
                            local_potential[y,x] += 100*self.constant + self.constant/math.pow(distance_to, self.gradient)
                        else:
                            local_potential[y,x] += 100*self.constant - self.constant/math.pow(distance_to, self.gradient)
                elif rotated_point[0] <= left_ref and step > 0:
                    distance_to = math.sqrt((rotated_point[0]-left_ref)**2 + distance_to**2)
                    if distance_to != 0:
                        local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)
                elif rotated_point[0] >= right_ref and step > 0:
                    distance_to = math.sqrt((rotated_point[0]-right_ref)**2 + distance_to**2)
                    if distance_to != 0:
                        local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)

        return local_potential

# step - an infinite line drawn through the point in the first argument in the direction of the vector in the
# second argument. The clockwise segment to the vector is cut off where as the anticlockwise segment acts like a
# infinite axial field over the entire pitch. also must be between start and end
# 9 9 9 9 9 9 9
# 9 9 9 9 9 9 9
# 3 3 3 3 3 3 3
# 1 1 1 1 1 1 1
# 0 0 0 0 0 0 0


class step_field:
    def __init__(self, (start_x, start_y), (dir_x, dir_y), influence_range, g, k):
        self.start_x = start_x
        self.start_y = start_y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.influence_range = influence_range
        self.gradient = g
        self.constant = k

    def force_at(self, x, y):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_point = rotate_vector(-angle, x, y)
        distance_to = abs(rotated_point[1] - start_field[1])
        direction = (0, rotated_point[1]-start_field[1])

        if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0 and distance_to != 0: # in direction step_direction
            addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
            dx = addx
            dy = addy
            return dx, dy
        elif distance_to != 0:
            addx, addy = rotate_vector(angle, 0, -direction[1]*(self.constant + self.constant/math.pow(distance_to, self.gradient+2)))
            dx = addx
            dy = addy
            return dx, dy
        else:
            return 0, 0

    def add_force(self, dx, dy):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):

                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - start_field[1])
                direction = (0, rotated_point[1]-start_field[1])

                if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0 and distance_to != 0: # in direction step_direction
                    addx, addy = rotate_vector(angle, 0, self.constant*direction[1]/math.pow(distance_to, self.gradient+2))
                    dx[y,x] += addx
                    dy[y,x] += addy
                elif distance_to != 0:
                    addx, addy = rotate_vector(angle, 0, -direction[1]*(self.constant + self.constant/math.pow(distance_to, self.gradient+2)))
                    dx[y,x] += addx
                    dy[y,x] += addy

        return dx, dy

    def field_at(self, x, y):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)
        rotated_point = rotate_vector(-angle, x, y)
        distance_to = abs(rotated_point[1] - start_field[1])
        if distance_to != 0:
            if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0: # in direction step_direction
                local_potential = self.constant/math.pow(distance_to, self.gradient)
                return local_potential
            else:
                if self.constant <= 0:
                    local_potential = -100*self.constant
                    return local_potential
                else:
                    local_potential = 100*self.constant
                    return local_potential
        else:
            if self.constant <= 0:
                local_potential = -100*self.constant
                return local_potential
            else:
                local_potential = 100*self.constant
                return local_potential

    def add_field(self, local_potential):
        step_direction = rotate_vector(90, self.dir_x, self.dir_y) # points towards the aloud region
        angle = math.degrees(math.atan2(self.dir_y, self.dir_x))
        start_field = rotate_vector(-angle, self.start_x, self.start_y)

        for x in range(0, PITCH_COLS):
            for y in range(0, PITCH_ROWS):

                rotated_point = rotate_vector(-angle, x, y)
                distance_to = abs(rotated_point[1] - start_field[1])
                if distance_to != 0:
                    if dot_product(step_direction, (x - self.start_x, y - self.start_y)) > 0: # in direction step_direction
                        local_potential[y,x] += self.constant/math.pow(distance_to, self.gradient)
                    else:
                        if self.constant <= 0:
                            local_potential[y,x] += -100*self.constant
                        else:
                            local_potential[y,x] += 100*self.constant
                else:
                    if self.constant <= 0:
                        local_potential[y,x] += -100*self.constant
                    else:
                        local_potential[y,x] += 100*self.constant

        return local_potential


def rotate_vector(angle, x, y): # takes degrees
    angle = math.radians(angle)
    return x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle)

def np_rotate_vector(angle, x, y): # takes degrees
    angle = math.radians(angle)
    return np.subtract(np.multiply(x,np.cos(angle)),np.multiply(y,np.sin(angle))), np.add(np.multiply(x,np.sin(angle)),np.multiply(y,np.cos(angle)))

def normalize((x, y)):
    return x/math.sqrt(x**2 + y**2), y/math.sqrt(x**2 + y**2)

def dot_product((ax, ay),(bx, by)):
    return ax*bx + ay*by

def np_dot_product(a, b):
    return np.add(np.multiply(a[0],b[0]), np.multiply(a[1],b[1]))

def get_play_direction(world):
    if world.we_have_computer_goal and world.room_num == 1 or not world.we_have_computer_goal and world.room_num == 0:
        return 1, 0
    elif world.we_have_computer_goal and world.room_num == 0 or not world.we_have_computer_goal and world.room_num == 1:
        return -1, 0

def magnitude((x, y)):
    return math.sqrt(x**2 + y**2)

