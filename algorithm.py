import math
import numpy as np

from model.person import Person


class Algorithm:
    label = "person"
    state_normal = 0
    state_warning = 1
    state_fallen = 2

    _beta_coefficient = 0.7

    # List containing all Person object detected
    _person_list = []

    def process(self, object_list, time):
        """
        Process the list of detected objects and returns a list containing Person objects,
        each one with your state
        :param object_list: list of Objects representing detected person
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
                # Here we define alpha as the relation between height and width
                alpha = obj.height / obj.width
                # Here we define beta as the relation between highest_height and height
                beta = obj.height / (pfpf.highest_height * self._beta_coefficient)
                # Check if person is fallen in horizontal
                if alpha < 1.0:
                    # Check the time to determine the state
                    if pfpf.time is None:
                        pfpf.time = time
                        pfpf.state = self.state_warning
                    elif time - pfpf.time > 1:
                        pfpf.state = self.state_fallen
                # Check if person is fallen in vertical
                elif beta < 1.0:
                    # print("height={} | highest_height={} | beta={}".format(obj.height, pfpf.highest_height, beta))
                    # Check the time to determine the state
                    if pfpf.time is None:
                        pfpf.time = time
                        pfpf.state = self.state_warning
                    elif time - pfpf.time > 2:
                        pfpf.state = self.state_fallen
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
        :param obj: Object with data from current frame
        :return:
        """
        if person.state == self.state_normal and obj.height > person.highest_height:
            person.highest_height = obj.height
        person.movement_vector = (obj.x - person.object.x, obj.y - person.object.y)
        person.object = obj

    def _add_person(self, obj):
        """
        Create and add person in normal state to person_list
        :param obj: Object that represents a person detection
        :return:
        """
        person = Person()
        person.object = obj
        person.state = self.state_normal
        person.highest_height = obj.height
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
            if person.current_object == obj:
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
    :param obj: Object
    :return: tuple (center x, center y)
    """
    return obj.x + obj.width / 2, obj.y + obj.height / 2


def get_points_distance(point1, point2):
    """
    Gets the distance between two points
    :param point1: tuple with point 1
    :param point2: tuple with point 2
    :return: int distance
    """
    return int(math.sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2))
