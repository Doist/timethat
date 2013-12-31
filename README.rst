
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
