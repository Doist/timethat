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
