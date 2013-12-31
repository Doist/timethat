import pytest
import os
import timethat as tt


def test_tt():
    for benchmark in tt.repeat(1000):
        with benchmark:
            os.path.join('foo', 'bar', 'baz')

    assert len(benchmark.results) == 1000


def test_tt_names():
    benchmark = tt.Benchmark()
    assert benchmark.name == 'test_tt_names'


def test_tt_names_from_repeat():
    benchmark = next(tt.repeat())
    assert benchmark.name == 'test_tt_names_from_repeat'


@pytest.mark.parametrize(['sec', 'scale_factor', 'string'], [
    (1, (1, 'sec'), '1.00 sec'),
    (0.1, (1e3, 'usec'), '100.00 usec'),
    (1.1e-6, (1e6, 'msec'), '1.10 msec'),
    (2e-9, (1e9, 'nsec'), '2.00 nsec'),
    (2e-10, (1e9, 'nsec'), '0.2 nsec'),
])
def test_seconds_to_str(sec, scale_factor, string):
    assert tt.scale_factor(sec) == scale_factor
    assert tt.seconds_to_str(sec) == string


def test_counter_values():
    benchmark = tt.Benchmark()
    tt.incr('foo')
    with benchmark:
        tt.incr('foo')
        tt.incr('foo')
        tt.incr('foo')
    with benchmark:
        pass
    with benchmark:
        tt.incr('foo')
        tt.incr('foo')
    assert benchmark.counter_values('foo') == [3, 0, 2]


def test_counter_names():
    benchmark = tt.Benchmark()
    with benchmark:
        tt.incr('foo')
    with benchmark:
        tt.incr('bar')
    assert benchmark.counters() == ['bar', 'foo']

def test_summary():
    benchmark = tt.Benchmark()
    with benchmark:
        tt.incr('foo')
        tt.incr('bar')
    with benchmark:
        tt.incr('bar')
    print benchmark.summary()

