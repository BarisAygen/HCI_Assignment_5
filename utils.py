import math
import numpy as np

# Calculate distance between two points
def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def calculate_angle(pointA, pointB, pointC):
    # Vector AB
    AB = np.array([pointB[0] - pointA[0], pointB[1] - pointA[1]])
    # Vector BC
    BC = np.array([pointC[0] - pointB[0], pointC[1] - pointB[1]])

    # Dot product and magnitudes
    dot_product = np.dot(AB, BC)
    magnitude_AB = np.linalg.norm(AB)
    magnitude_BC = np.linalg.norm(BC)

    # Calculate the angle in radians and then convert to degrees
    if magnitude_AB * magnitude_BC == 0:
        return 0
    angle = math.acos(dot_product / (magnitude_AB * magnitude_BC))
    angle_degrees = math.degrees(angle)

    return angle_degrees