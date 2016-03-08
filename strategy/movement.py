import numpy as np


# Directions robot is facing after the movement
TOP = 0
RIGHT = 1
BOTTOM = 2
LEFT = 3


def get_movement_direction(field, commands):
    """Finds command to be called and robot direction after the movement"""
    field[[0, 2, 4, 0, 4, 0, 2, 4], [0, 0, 0, 2, 2, 4, 4, 4]] = np.inf
    # field is 5x5 numpy array
    y, x = np.where(field == field.min())
    indices = np.array([x, y]).T.tolist()
    print indices
    if [2, 2] in indices:
        return None, TOP
    elif [2, 1] in indices or [1, 0] in indices or [3, 0] in indices:
        return commands.forward, TOP
    elif [1, 1] in indices or [0, 1] in indices:
        return commands.forward_left, LEFT
    elif [3, 1] in indices or [4, 1] in indices:
        return commands.forward_right, RIGHT
    elif [1, 2] in indices:
        return commands.sharp_left, LEFT
    elif [3, 2] in indices:
        return commands.sharp_right, RIGHT
    elif [2, 3] in indices or [1, 4] in indices or [3, 4] in indices:
        return commands.backward, BOTTOM
    elif [1, 3] in indices or [0, 3] in indices:
        return commands.backward_left, LEFT
    elif [3, 3] in indices or [4, 3] in indices:
        return commands.backward_right, RIGHT
