import math
import numpy as np


class Person:
    # object saved from last frame
    object = None
    # Current object that matched with the one from last frame
    current_object = None
    # Final state
    state = None
    # Time that the person is in the state
    time = None
    # Time that the person is in stopped state
    stopped_time = None
    # Highest height in the normal state
    highest_height = None
    # Box coordinates from last update
    position = None


class FaintingRecognition:
    label = "person"

    state_normal = "Normal"
    state_horizontal_warning = "Horizontal warning"
    state_vertical_warning = "Vertical warning"
    state_movement_alert = "Movement alert"
    state_fallen = "Fallen"

    _beta_coefficient = 0.7

    _horizontal_time = 1
    _vertical_time = 2
    _stopped_time = 3

    # List containing all Person object detected
    _person_list = []

    def event(self, object_list, time):
        pl = self.process(object_list, time)
        event = None
        for p in pl:
            if p.state == self.state_fallen:
                return self.state_fallen
            elif p.state == self.state_movement_alert:
                event = self.state_movement_alert
        return event

    def process(self, object_list, time):
        """
        Process the list of detected objects and returns a list containing Person objects,
        each one with your state
        :param object_list: list of dicts representing detected person
        :param time: relative time in seconds, in video context
        :return: list containing Person objects with their state
        """
        self._match_object_with_person(object_list)
        self._clean_person_list()

        for obj in object_list:
            # Person from previous frame
            pfpf = self._get_person(obj)

            if pfpf is None:
                self._add_person(obj)
            else:
                if is_moving(pfpf):
                    pfpf.stopped_time = None
                    pfpf.time = None
                    pfpf.state = self.state_normal
                else:
                    if pfpf.stopped_time is None:
                        pfpf.stopped_time = time

                    # Here we define alpha as the relation between height and width
                    alpha = obj['height'] / obj['width']
                    # Here we define beta as the relation between highest_height and height
                    beta = obj['height'] / (pfpf.highest_height * self._beta_coefficient)

                    # Check if person is fallen in horizontal
                    if alpha < 1.0:
                        # Check the time to determine the state
                        if pfpf.time is None:
                            pfpf.time = time
                            pfpf.state = self.state_horizontal_warning
                        elif time - pfpf.time > self._horizontal_time:
                            pfpf.state = self.state_fallen
                    # Check if person is fallen in vertical
                    elif beta < 1.0:
                        # Check the time to determine the state
                        if pfpf.time is None:
                            pfpf.time = time
                            pfpf.state = self.state_vertical_warning
                        elif time - pfpf.time > self._vertical_time:
                            pfpf.state = self.state_fallen
                    elif pfpf.stopped_time is not None and time - pfpf.stopped_time > self._stopped_time:
                        pfpf.state = self.state_movement_alert
                    else:
                        # Reset
                        pfpf.state = self.state_normal
                        pfpf.time = None

                self._update_person(pfpf, obj)

        return self._person_list

    def _update_person(self, person, obj):
        """
        Updates person transitioning from previous frame to current frame
        :param person: Person object with data from previous frame to be updated
        :param obj: dict with data from current frame
        :return:
        """
        if person.state == self.state_normal and obj['height'] > person.highest_height:
            person.highest_height = obj['height']
        person.object = obj

    def _add_person(self, obj):
        """
        Create and add person in normal state to person_list
        :param obj: dict that represents a person detection
        :return:
        """
        person = Person()
        person.object = obj
        person.state = self.state_normal
        person.highest_height = obj['height']
        person.position = (obj['x'], obj['y'], obj['x2'], obj['y2'])
        self._person_list.append(person)

    def _clean_person_list(self):
        """
        Clean person that is no more in the frame
        :return:
        """
        for person in self._person_list:
            # Person that do not match with any object means that the the person is no more in the frame
            if person.current_object is None:
                self._person_list.remove(person)

    def _get_person(self, obj):
        """
        Gets the nearest stored person, according to box position
        :param obj: Current person detected
        :return: The same person, stored in previous frame
        """
        for person in self._person_list:
            if person.current_object is not None and person.current_object == obj:
                return person
        return None

    def _match_object_with_person(self, object_list):
        """
        Given a Person, finds the nearest object and sets it to the 'current_object' field
        :param object_list: objects detected
        :return:
        """
        matrix_distance = []
        for person in self._person_list:
            person.current_object = None
            row_distance = []
            for obj in object_list:
                distance = get_points_distance(get_box_center(obj), get_box_center(person.object))
                row_distance.append(distance)
            matrix_distance.append(row_distance)

        md = np.array(matrix_distance)
        n = min(md.shape)
        # Get the index of n min distances values of a flatten matrix
        match_index = md.flatten().argsort()[:n]
        for flatten_index in match_index:
            # Converts the index of flatten matrix to (row, column)
            i, j = int(flatten_index / md.shape[1]), int(flatten_index % md.shape[1])
            self._person_list[i].current_object = object_list[j]


def get_box_center(obj):
    """
    Get the box center coordinate, once box detection comes with
    top left x and y
    :param obj: dict
    :return: tuple (center x, center y)
    """
    return obj['x'] + obj['width'] / 2, obj['y'] + obj['height'] / 2


def get_points_distance(point1, point2):
    """
    Gets the distance between two points
    :param point1: tuple with point 1
    :param point2: tuple with point 2
    :return: int distance
    """
    return int(math.sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2))


def is_moving(person):
    """
    Check if person is moving
    If the current position is outside of the last box saved,
    so the person is considered in movement
    :param person: Person object
    :return: bool
    """
    x, y, x2, y2 = 0, 1, 2, 3
    # Box position from last update
    box = person.position
    # Current position
    cp = (person.current_object.cx, person.current_object.cy)

    # (0, 0) coordinate is in the top left point
    # Check if current position is inside of the last saved box
    if cp[x] < box[x] or cp[x] > box[x2] or cp[y] < box[y] or cp[y] > box[y2]:
        person.position = (person.current_object.x, person.current_object.y,
                           person.current_object.x2, person.current_object.y2)
        return True
    else:
        return False
