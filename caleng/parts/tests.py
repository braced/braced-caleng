from django.test import TestCase
from caleng.parts.tstubs import SimpleTStub, CornerTStub

class TStubTestCase(TestCase):
    def setUp(self):
        print("TESTING Lb and LB*")

    def test_lb_works(self):
        self.assertEqual(1, 1)
        self.assertEqual(1, 1)
