"""
**timethat** -- timeit on steroids, a module for benchmarking.

Dependency: numpy

Timethat helps you to define you own setups and teardowns without creating
separate functions for that. The drawback is that you have to define the
testing cycle explicitly by yourself

A simple and pretty much useless example, where we want to test the speed of
reading data from JSON file

.. code-block:: python

    import timethat as tt
    import os
    import json

    for benchmark in tt.repeat(1000, name='my benchmark'):
        # setup actions
        data = {'key': 'value'}
        with open('test.json', 'w') as fd:
            json.dump(data, fd)
        # the test itself
        with benchmark:  # that's how we mark that we are in the benchmark
            with open('test.json') as fd:
                data = json.load(fd)
        # teardown actions
        os.unlink('test.json')


Then you may call ``benchmark.summary``, and get the summary of the results.
Mean execution time, as well as the range which 95% of results fit in.

.. code-block:: python

    >>> print benchmark.summary()
    my benchmark                       37.61 msec     95% range [28.85 msec, 101.09 msec]

Although it's somewhat uncommon, the ``benchmark`` variable is the same
in all cycles of the loop. If you feel uncomfortable with it, you may create
the object explicitly

.. code-block:: python

    benchmark = tt.Benchmark(name='my benchmark')
    for i in xrange(1000):
        ...
        # here the same code goes
"""
import inspect
import time
import sys
import numpy as np
import gc
import itertools


if sys.platform == "win32":
    # On Windows, the best timer is time.clock()
    default_timer = time.clock
else:
    # On most other platforms the best timer is time.time()
    default_timer = time.time


def seconds_to_str(seconds):
    """
    Helper function to convert seconds as floating values to string with scaled values
    """
    factor, unit = scale_factor(seconds)
    value = seconds * factor
    if value >= 1:
        return '%.2f %s' % (value, unit)
    else:
        return '%s %s' % (value, unit)


def scale_factor(seconds):
    """
    Helper function to convert seconds as floating values to string with scaled values
    """
    variants = ['usec', 'msec', 'nsec']

    if seconds >= 1:
        return 1, 'sec'

    factor = 1
    for variant in variants:
        factor *= 1e3
        if seconds * factor >= 1:
            return factor, variant

    return factor, variant


class Benchmark(object):
    """
    The benchmark object
    """

    def __init__(self, name=None, timer=default_timer):
        self.timer = timer
        self.results = []
        self.ts = 0
        self.name = name or self.get_default_name()
        self.gcold = True
        self.iteration = 0

    def __enter__(self):
        self.iteration += 1
        self.gcold = gc.isenabled()
        gc.disable()
        self.ts = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.results.append(time.time() - self.ts)
        if self.gcold:
            gc.enable()

    def get_default_name(self):
        try:
            ret = inspect.stack()[2][3]
            if ret == 'repeat':  # called from timethat.repeat()
                ret = inspect.stack()[3][3]
            return ret
        except IndexError:
            return '<benchmark>'

    def percentile(self, q=[2.5, 97.5]):
        return np.percentile(self.results, q)

    def percentile_str(self):
        min_val, max_val = self.percentile()
        return '95%% range [%s, %s]' % (
            seconds_to_str(min_val), seconds_to_str(max_val))

    def mean(self):
        return np.mean(self.results)

    def mean_str(self):
        return seconds_to_str(self.mean())

    def summary(self, name_length=35, mean_length=15, range_length=30):
        format = '{:%s}{:%s}{:%s}' % (name_length, mean_length, range_length)
        return format.format(self.name, self.mean_str(), self.percentile_str())


def repeat(num=1000, name=None, timer=default_timer):
    """
    Simple iterator which returns the same benchmark object num times.

    :param num: number of iterations
    :param name: benchmark name
    :param timer: timer function
    """
    return itertools.repeat(Benchmark(name=name, timer=timer), num)
