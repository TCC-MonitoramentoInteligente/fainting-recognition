class Person:
    """
    Model with specific attributes needed by the algorithm
    """
    # Object saved from last frame
    object = None
    # Current object that matched with the one from last frame
    current_object = None
    # Person state
    state = None
    # Time that the person is in current state
    time = None
    # Highest height in the normal state
    highest_height = None
    # Movement vector of a person
    movement_vector = None
