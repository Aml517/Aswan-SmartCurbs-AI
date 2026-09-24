def pixel_to_real_distance(pixel_distance, reference_pixel_distance,
                            reference_real_distance):
    """
    Estimate real-world distance using a known reference distance.

    pixel_distance: measured distance in pixels
    reference_pixel_distance: known pixel distance
    reference_real_distance: known real-world distance, e.g. meters
    """

    if reference_pixel_distance <= 0:
        raise ValueError("Reference pixel distance must be greater than zero.")

    scale = reference_real_distance / reference_pixel_distance

    return pixel_distance * scale


if __name__ == "__main__":

    print("Calibration Prototype")
    print("----------------------")

    print("Real-world distance estimation requires:")
    print("1. Camera calibration")
    print("2. Known reference distance")
    print("3. Perspective transformation")

    print("\nCurrent prototype uses pixel distance only.")