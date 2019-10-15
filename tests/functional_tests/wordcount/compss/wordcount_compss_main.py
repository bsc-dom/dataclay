#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Class description goes here. """

import sys
import logging
from model.classes import TextStats, TextCollection
from pycompss.api.task import task

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2017 Barcelona Supercomputing Center (BSC-CNS)'
logger = logging.getLogger(__name__)


@task(returns=TextStats)
def wordCount(data):
    """Construct a frequency word TextStats object from a Text object.
    :param data: a Text (model, see model/__init__.py)
    :return: a TextStats (model, see model/__init__.py)
    """
    return data.word_count()


@task(returns=TextStats, priority=True)
def merge_two_dicts(dic1, dic2):
    """ Update a dictionary with another dictionary.
    :param dic1: first TextStats
    :param dic2: second TextStats
    :return: dic1+=dic2
    """
    return dic1.merge_with(dic2)


if __name__ == "__main__":
    from pycompss.api.api import compss_wait_on

    # Get the dataset (word collection) _persistent_ name
    nameDataset = sys.argv[1]

    data = TextCollection.get_by_alias(nameDataset)

    # From all data execute a wordcount on it
    partialResult = map(wordCount, data)

    # Accumulate the partial results to get the final result.
    result = reduce(merge_two_dicts, partialResult)

    # Wait for result
    result = compss_wait_on(result)

    logger.info("Most used words in text:\n%s" % result.top_words(10))
    logger.info("Words: %d" % result.get_total()) 
