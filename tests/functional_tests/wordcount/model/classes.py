
""" Class description goes here. """

from dataclay import dclayMethod
from dataclay.contrib.dummy_pycompss import task
from storage.api import StorageObject


class TextCollection(StorageObject):
    """Collection of Text objects.

    @ClassField texts list<model.classes.Text>
    """

    @dclayMethod()
    def __init__(self):
        self.texts = list()

    @dclayMethod(text="model.classes.Text")
    def add_text(self, text):
        self.texts.append(text)

    @dclayMethod(_local=True)
    def __iter__(self):
        return iter(self.texts)


class TextStats(StorageObject):
    """Store Word Count stats.

    Dictionary-like storage of word counting (also used for partial results).
    Also, convenience methods.

    @ClassField current_word_count anything
    """

    @dclayMethod(init_dict="anything")
    def __init__(self, init_dict):
        self.current_word_count = dict(init_dict)

    @task()
    @dclayMethod(target="model.classes.TextStats")
    def merge_with(self, target):
        # Cosmetics / minor rename
        dic1 = self.current_word_count
        dic2 = target.current_word_count

        # Basic merge (COMPSs verbatim)
        for k in dic2:
            if k in dic1:
                dic1[k] += dic2[k]
            else:
                dic1[k] = dic2[k]

        # Return not used because self is INOUT by default

    @dclayMethod(num_words=int, return_="anything")
    def top_words(self, num_words):
        sorted_values = sorted((count, word) for word, count in self.current_word_count.iteritems())
        return dict((word, count) for count, word in sorted_values[-num_words:])

    @dclayMethod(return_=int)
    def get_total(self):
        return sum(self.current_word_count.values())


class Text(StorageObject):
    """A "Text" (list of words).

    This object contains `words` which is expected to be a list of words.

    @ClassField words anything
    """

    @dclayMethod()
    def __init__(self):
        # This will be initialized in persistent storage with populate_from_file
        self.words = list()

    @dclayMethod(return_=int, file_path='str')
    def populate_from_file(self, file_path):
        with open(file_path, "r") as text_file:
            for line in text_file.readlines():
                self.words.extend(line.strip().lower().translate(None, ".,\"'").split())
        return len(self.words)

    @task(returns=object)
    @dclayMethod(return_="model.classes.TextStats")
    def word_count(self):
        partialResult = {}
        for entry in self.words:
            if entry in partialResult:
                partialResult[entry] += 1
            else:
                partialResult[entry] = 1
        return TextStats(partialResult)

    @dclayMethod(return_=int)
    def __len__(self):
        return len(self.words)
