import unittest
import numpy as np

from pyzview import Pyzview


class TestPyzview(unittest.TestCase):
    def setUp(self) -> None:
        self.zv = Pyzview()


    def test_set_object(self):

        t1 = (0, 0, .3)
        t2 = (0, 0, .6)
        t3 = (0, 0, 2)
        r1 = (0, 0, np.pi / 4)
        r2 = np.eye(3)
        r3 = (0, np.pi, 0)
        s1 = (.1, .2, .3)
        s2 = .2
        s3 = 0.5
        k = np.array([[1.5,0,0],[0,2,0],[0,0,1]])

        self.zv.set_rectangle("rect", np.eye(3,4)*0.1, color='r')
        self.zv.set_marker("marker", (t2, r2, s2), color='g')
        self.zv.set_camera("camera", (t3, r3, s3),k, color='b')

    def test_set_points(self):
        self.zv.set_points("rand", np.random.rand(100, 6))

    def test_add_mesh(self):
        xg, yg = np.meshgrid(np.linspace(-1, 1, 30), np.linspace(-1, 1, 30))
        r2 = xg ** 2 + yg ** 2
        s1 = 0.2
        s2 = 0.1
        zg = np.exp(-0.5 / s1 * r2) - np.exp(-0.5 / s2 * r2)
        xyz=np.stack([xg, yg, zg],axis=2)

        self.zv.set_mesh("mesh",xyz)




if __name__ == "__main__":
    unittest.main()
