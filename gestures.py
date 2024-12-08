import utils

def is_zoom_detected(landmarks):
    # Draw the filled green circle for the index finger tip (after drawing connections)
    index_tip = landmarks[8]  # Index finger tip
    middle_tip =landmarks[12] # middle finger tip
    thumb_tip = landmarks[4]
    ring_pip = landmarks[14]

    index_middle_distance = utils.calculate_distance(middle_tip,index_tip)
    thumb_ring_distance = utils.calculate_distance(thumb_tip,ring_pip)


    if (50 < thumb_ring_distance < 100) and (index_middle_distance < 18):
        return True
    return False


def is_hover_gesture(landmarks, element_positions):
    """
    Detect if the index fingertip is hovering over any UI element.
    :param landmarks: List of hand landmark positions.
    :param element_positions: List of bounding box positions [(x1, y1, x2, y2), ...].
    :return: Index of the hovered element or -1 if no hover is detected.
    """
    index_tip = landmarks[8]  # Index fingertip position (x, y)

    for idx, (x1, y1, x2, y2) in enumerate(element_positions):
        if x1 <= index_tip[0] <= x2 and y1 <= index_tip[1] <= y2:
            return idx  # Return the index of the hovered element

    return -1  # No hover detected

def detect_zoom_direction(landmarks,previous_distance):
    index_tip = landmarks[8]  # Index finger tip
    thumb_tip = landmarks[4]  # Thumb tip
    middle_tip =landmarks[12]

    result=""

    # Calculate the distances
    thumb_index_distance = utils.calculate_distance(thumb_tip, index_tip)
    thumb_middle_distance = utils.calculate_distance(thumb_tip, middle_tip)
    
    # Calculate the average distance for zooming
    average_distance = (thumb_index_distance + thumb_middle_distance) / 2
    # Determine zoom gesture
    if previous_distance is not None:
        if average_distance < previous_distance - 10:  # Zoom in
            result = "out"
        elif average_distance > previous_distance + 10:  # Zoom out
            result = "in"

    previous_distance = average_distance
    return result,previous_distance


def is_scroll_gesture(landmarks):
    """Detects scrolling when index (8) and middle finger (12) are aligned."""
    index_tip = landmarks[8]  # Tip of the index finger
    middle_tip = landmarks[12]  # Tip of the middle finger
    ring_pip = landmarks[14]
    thumb_tip = landmarks[4]

    is_aligned_horizontally = abs(index_tip[0] - middle_tip[0]) < 20  # y-coordinates aligned
    is_ring_with_thumb = utils.calculate_distance(ring_pip,thumb_tip) < 50

    # Return True if aligned either vertically or horizontally
    # return is_aligned_vertically or is_aligned_horizontally
    return is_ring_with_thumb and is_aligned_horizontally  


# Detecting the scroll direction
def detect_scroll_direction(landmarks, previous_index_x, previous_index_y):
    """Detects if the user is scrolling and determines the direction, with deviation tolerance."""
    index_tip_x = landmarks[8][0]  # x-coordinate of the index finger tip
    index_tip_y = landmarks[8][1]  # y-coordinate of the index finger tip

    # If this is the first frame, initialize the previous position
    if previous_index_x is None or previous_index_y is None:
        return "none", index_tip_x, index_tip_y

    # Define thresholds
    major_threshold = 20  # Major movement threshold (to determine primary direction)
    minor_threshold = 5   # Minor deviation threshold (to ignore small side movements)

    # Calculate differences
    delta_x = index_tip_x - previous_index_x
    delta_y = index_tip_y - previous_index_y

    # Determine scrolling direction with tolerance
    if abs(delta_y) > major_threshold and abs(delta_x) < minor_threshold:
        # If vertical movement is significant and horizontal movement is within minor deviation
        if delta_y > 0:
            direction = "down"
        else:
            direction = "up"
    elif abs(delta_x) > major_threshold and abs(delta_y) < minor_threshold:
        # If horizontal movement is significant and vertical movement is within minor deviation
        if delta_x > 0:
            direction = "right"
        else:
            direction = "left"
    else:
        # No significant movement or mixed movement
        direction = "none"

    # Update previous positions
    return direction, index_tip_x, index_tip_y

def is_click_gesture(landmarks):
    """Detects the CLICK gesture."""
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    distance = utils.calculate_distance(thumb_tip, index_tip)
    return distance < 20  # Adjust threshold as needed