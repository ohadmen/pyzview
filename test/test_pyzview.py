import unittest
import numpy as np

from pyzview import Pyzview

class TestPyzview(unittest.TestCase):

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

        Pyzview().add_rectangle("rect", np.eye(3,4)*0.1, color='r')
        Pyzview().add_marker("marker", t2, r2, s2, color='g')
        Pyzview().add_camera("camera", t3, r3, s3,k, color='b')

    def test_set_points(self):
        Pyzview().add_points("rand", np.random.rand(100, 6))

    def test_add_edges(self):
        pts=np.array([[y=='1' for y in '{0:03b}'.format(x)] for x in range(8)])*1
        pts = np.c_[pts,np.random.rand(*pts.shape)]
        edges = np.array([[0,2],[2,6],[6,4],[4,0],[1,3],[3,7],[7,5],[5,1],[0,1],[2,3],[4,5],[6,7]])
        Pyzview().remove_shape('edges')
        Pyzview().add_edges("edges",pts,edges)

    def test_add_mesh(self):
        xg, yg = np.meshgrid(np.linspace(-1, 1, 30), np.linspace(-1, 1, 30))
        r2 = xg ** 2 + yg ** 2
        s1 = 0.2
        s2 = 0.1
        zg = np.exp(-0.5 / s1 * r2) - np.exp(-0.5 / s2 * r2)
        xyz=np.stack([xg, yg, zg],axis=2)

        Pyzview().add_mesh("mesh",xyz)




if __name__ == "__main__":
    unittest.main()
