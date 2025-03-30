from pycompss.api.task import task
from pycompss.api.parameter import FILE_IN

from collections import defaultdict


class Words(object):
    def __init__(self, text=''):
        self.text = text

    @task(returns=1, file_path=FILE_IN, priority=True)
    def populate_block(self, file_path):
        """
        Reads a file and stores its content within the object.
        :param file_path: Absolute path of the file to process.
        :return: None
        """
        with open(file_path) as fp:
            self.text = fp.read()

    @task(returns=defaultdict, priority=True)
    def wordcount(self):
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
