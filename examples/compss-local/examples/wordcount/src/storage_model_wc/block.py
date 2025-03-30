from collections import defaultdict

from dataclay import DataClayObject, activemethod

try:
    from pycompss.api.task import task
    from pycompss.api.parameter import FILE_IN
except ImportError:
    # Required since the pycompss module is not ready during the registry
    from dataclay.contrib.dummy_pycompss import task, FILE_IN


class Words(DataClayObject):
    text: str

    def __init__(self, text: str = ""):
        self.text = text

    # Not activemethod because it requires access to the filesystem and file_path,
    # which is managed by COMPSs within the worker container
    @task(file_path=FILE_IN, priority=True)
    def populate_block(self, file_path: str) -> None:
        """
        Reads a file and stores its content within the object.
        :param file_path: Absolute path of the file to process.
        """
        with open(file_path) as fp:
            # The following line populates the persistent object
            self.text = fp.read()

    @task(returns=1, priority=True)
    @activemethod
    def wordcount(self) -> dict:
        """
        Wordcount over a Words object.
        :param block: Block with text to perform word counting.
        :return: dictionary with the words and the number of appearances.
        """
        data = self.text.split()
        result = defaultdict(int)
        for word in data:
            result[word] += 1
        return result
