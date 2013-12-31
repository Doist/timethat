"""
**timethat** -- timeit on steroids, a module for benchmarking.

Dependency: numpy

Timethat helps you to define you own setups and teardowns without creating
separate functions for that. The drawback is that you have to define the
testing cycle explicitly by yourself

Example
----------

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


Working with counters
-------------------------

As you optimize your code, you may be interested in getting some extra metrics
along the way: how many times a database calls were made, same for specific
function calls, cache hits / misses, etc.

There is a special counter function to help you with that. All you need is to
call it when you want to count a resource or operation:

.. code-block:: python

    ...
    tt.incr('get_user_cache_miss')
    ...
    tt.incr('mysql_select')

The counter will be incremented only if it's been executed within a benchmark
context.

Hint: you won't probably be able to patch your library / framework just to
insert a bunch of :func:`incr` calls there. Instead, if your framework can
do it, you may add a special in-benchmark signal handler calling `tt.incr(...)`
whenever you need.

To work with results, here are a number of counter-specific methods. Basic
functions are:

- :func:`Benchmark.counters()` -- get the set of all benchmark counters
  (as the set of strings)
- :func:`Benchmark.counter_values(counter_name)` -- get values of the the
  specific counter, one per test

Additionally, there are functions :func:`counter_percentile`,
:func:`counter_percentile_str`, :func:`counter_mean` and
:func:`counter_mean_str` to get results in a more convenient way.

The :func:`summary` method takes counters into account and returns the result
with time and all counters statistics, if any.
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


active_benchmarks = {}


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


def incr(counter_name, value=1):
    for benchmark in active_benchmarks.values():
        benchmark.incr(counter_name, value)


class Benchmark(object):
    """
    The benchmark object
    """
    counter_prefix = '- '

    def __init__(self, name=None, timer=default_timer):
        self.timer = timer
        self.results = []
        self.ts = 0
        self.name = name or self.get_default_name()
        self.gcold = True
        self.iteration = 0
        self._counters = []
        self._current_counter = None

    def __enter__(self):
        self.start()

    def start(self):
        active_benchmarks[id(self)] = self
        self._current_counter = {}
        self.iteration += 1
        self.gcold = gc.isenabled()
        gc.disable()
        self.ts = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def stop(self):
        self.results.append(time.time() - self.ts)
        self._counters.append(self._current_counter)
        self._current_counter = None
        if self.gcold:
            gc.enable()
        active_benchmarks.pop(id(self), None)

    def incr(self, counter_name, value=1):
        if self._current_counter is not None:
            current_val = self._current_counter.get(counter_name, 0)
            self._current_counter[counter_name] = current_val + value

    def get_default_name(self):
        try:
            ret = inspect.stack()[2][3]
            if ret == 'repeat':  # called from timethat.repeat()
                ret = inspect.stack()[3][3]
            return ret
        except IndexError:
            return '<benchmark>'

    def percentile(self, q=[2.5, 97.5]):
        if not self.results:
            return [0] * len(q)
        return np.percentile(self.results, q)

    def percentile_str(self):
        min_val, max_val = self.percentile()
        return '95%% range [%s, %s]' % (
            seconds_to_str(min_val), seconds_to_str(max_val))

    def mean(self):
        return np.mean(self.results)

    def mean_str(self):
        return seconds_to_str(self.mean())

    def summary(self, name_length=None, mean_length=15, range_length=30):
        if name_length is None:
            name_length = self.get_max_name_length() + 2
        fmt = '{:%s}{:%s}{:%s}' % (name_length, mean_length, range_length)
        lines = []
        lines.append(fmt.format(self.name, self.mean_str(), self.percentile_str()))
        for counter in self.counters():
            name = '%s%s' % (self.counter_prefix, counter)
            mean = self.counter_mean_str(counter)
            perc = self.counter_percentile_str(counter)
            lines.append(fmt.format(name, mean, perc))
        return '\n'.join(lines)

    #--- formatter helpers

    def get_max_name_length(self):
        """
        Get maximum name length. Take into account the benchmark name itself,
        and names of all counters
        """
        values = [len(self.name)]
        values += (len(c) + len(self.counter_prefix) for c in self.counters())
        return max(values)

    #--- counter-specific data

    def counters(self):
        """
        Get the names of all benchmark counters
        """
        names = set()
        for c in self._counters:
            names.update(c.keys())
        return sorted(names)

    def counter_values(self, counter_name):
        """
        Get values of the the specific counter, one per test

        :param counter_name: counter name
        :return: list of counter values
        """
        return [c.get(counter_name, 0) for c in self._counters]

    def counter_percentile(self, counter_name, q=[2.5, 97.5]):
        values = self.counter_values(counter_name)
        if not values:
            return [0] * len(q)
        return np.percentile(values, q)

    def counter_percentile_str(self, counter_name, quiet=True):
        """
        Get the string representation of counter percentile values.
        If quiet, and minimum value is equal to maximum, then return
        an empty string

        :param counter_name: counter name as a string
        :param quiet: set this to False, if you don't want to hide
            "95% range [...]" text, even if there is no deviation at all
        """
        min_val, max_val = self.counter_percentile(counter_name)
        if min_val == max_val and quiet:
            return ''
        return '95%% range [%s, %s]' % (_to_int(min_val), _to_int(max_val))

    def counter_mean(self, counter_name):
        """
        Get the mean value of the counter

        :param counter_name: counter name as a string
        """
        return np.mean(self.counter_values(counter_name))

    def counter_mean_str(self, counter_name):
        """
        Get the string representation of the mean counter value. Ensures the
        value is represented as int, if it's possible
        """
        val = self.counter_mean(counter_name)
        return str(_to_int(val))


def _to_int(val):
    """
    If floating point value can be coerced to integer, convert and return
    integer, otherwise return floating point value
    """
    if int(val) == val:
        return int(val)
    return val


def repeat(num=1000, name=None, timer=default_timer):
    """
    Simple iterator which returns the same benchmark object num times.

    :param num: number of iterations
    :param name: benchmark name
    :param timer: timer function
    """
    return itertools.repeat(Benchmark(name=name, timer=timer), num)
