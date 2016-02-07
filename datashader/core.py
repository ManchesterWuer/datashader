from __future__ import absolute_import, division, print_function

import numpy as np
from datashape.predicates import istabular
from odo import discover

from .utils import Dispatcher, ngjit


class Axis(object):
    def __eq__(self, other):
        return (type(self) == type(other))

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(type(self))

    def scale_and_translation(self, range, n):
        start, end = map(self.mapper, range)
        s = (n - 1)/(end - start)
        t = -start * s
        return s, t

    def compute_index(self, n, st):
        px = np.arange(n)
        s, t = st
        return self.inverse_mapper((px - t)/s)


class LinearAxis(Axis):
    @staticmethod
    @ngjit
    def mapper(x):
        return x

    inverse_mapper = mapper


class LogAxis(Axis):
    @staticmethod
    @ngjit
    def mapper(x):
        return np.log10(x)

    @staticmethod
    @ngjit
    def inverse_mapper(x):
        return 10**x


_axis_lookup = {'linear': LinearAxis(),
                'log': LogAxis()}


class Canvas(object):
    def __init__(self, plot_width=600, plot_height=600,
                 x_range=None, y_range=None,
                 x_axis_type='linear', y_axis_type='linear'):
        self.plot_width = plot_width
        self.plot_height = plot_height
        self.x_range = tuple(x_range) if x_range else x_range
        self.y_range = tuple(y_range) if y_range else y_range
        self.x_axis = _axis_lookup[x_axis_type]
        self.y_axis = _axis_lookup[y_axis_type]

    def points(self, source, x, y, agg):
        from .glyphs import Point
        return bypixel(source, self, Point(x, y), agg)


pipeline = Dispatcher()


def bypixel(source, canvas, glyph, summary):
    dshape = discover(source)
    if not istabular(dshape):
        raise ValueError("source must be tabular")
    schema = dshape.measure
    glyph.validate(schema)
    summary.validate(schema)
    return pipeline(source, schema, canvas, glyph, summary)
