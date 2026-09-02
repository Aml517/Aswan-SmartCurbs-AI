import math


def calculate_distance(center1, center2):
    """
    Calculate Euclidean distance between two vehicle centers.

    Input:
        center1 = (x1, y1)
        center2 = (x2, y2)

    Output:
        Distance in pixels
    """

    x1, y1 = center1
    x2, y2 = center2

    distance = math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )

    return distance


if __name__ == "__main__":

    vehicle1_center = (140, 250)
    vehicle2_center = (440, 270)

    distance = calculate_distance(
        vehicle1_center,
        vehicle2_center
    )

    print(
        f"Vehicle 1 ↔ Vehicle 2 "
        f"Distance = {distance:.2f} pixels"
    )