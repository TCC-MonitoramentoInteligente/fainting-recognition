class Algorithm:

    normal_state = 0
    event_detected_state = 1

    def process(self, object_list):
        """
        Process the list of detected objects to return the current state
        :param object_list: list with detected objects
        :return: state
        """
        raise NotImplementedError()

    def process_gui(self, object_list):
        """
        Process the list of detected objects to return graphical data
        :param object_list: list with detected objects
        :return: list of Objects related with event
        """
        raise NotImplementedError()
