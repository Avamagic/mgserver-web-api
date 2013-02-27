from datetime import datetime
from flask.ext.restful import fields
from mgserver.api import Epoch
from tests import TestCase, TestCaseWithoutAuth


class TestUtils(TestCaseWithoutAuth):

    def test_epoch_field(self):
        DATETIME_UTC = datetime(2013, 2, 27, 15, 21, 53, 0, None)
        EPOCH = 1361978513

        obj = {"bar": DATETIME_UTC}
        field = Epoch()
        self.assertEquals(EPOCH, field.output("bar", obj))

    def test_epoch_invalid(self):
        obj = {"bar": "foo"}
        field = Epoch()
        with self.assertRaises(fields.MarshallingException):
            field.output("bar", obj)
