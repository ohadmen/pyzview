from typing import Union

import zview_module
import numpy as np


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Pyzview(metaclass=Singleton):
    @staticmethod
    def _get_trimesh_indices(sz):
        indx = np.arange(sz[0] * sz[1], dtype=np.int32).reshape(sz[:2])
        tri_a = np.stack((indx[:-1, 1:], indx[:-1, :-1], indx[1:, 1:]), axis=2).reshape(-1, 3)
        tri_b = np.stack((indx[:-1, :-1], indx[1:, :-1], indx[1:, 1:]), axis=2).reshape(-1, 3)
        tri = np.r_[tri_a, tri_b]
        return tri

    @staticmethod
    def _rgba2floatcol(rgba):
        rgba = np.clip(rgba, 0, 1)
        rgbafloat = (rgba * 255).astype(np.uint8)
        rgbafloat = rgbafloat.flatten()
        rgbafloat = rgbafloat.view(np.float32)
        return rgbafloat

    @staticmethod
    def _str2rgb(colorstr):
        if colorstr == 'r':
            col = [1, 0, 0]
        elif colorstr == 'g':
            col = [0, 1, 0]
        elif colorstr == 'b':
            col = [0, 0, 1]
        elif colorstr == 'c':
            col = [0, 1, 1]
        elif colorstr == 'm':
            col = [1, 0, 1]
        elif colorstr == 'y':
            col = [1, 1, 0]
        elif colorstr == 'w':
            col = [1, 1, 1]
        elif colorstr == 'k':
            col = [0, 0, 0]
        elif colorstr == 'R':
            col = list(np.random.rand(3))
        else:
            raise RuntimeError("unknown color name")
        return col

    @classmethod
    def _get_pts_arr(cls, xyz, color, alpha):
        if len(xyz.shape) == 3:
            xyz = xyz.reshape(-1, xyz.shape[2])
        if len(xyz.shape) == 1 and xyz.shape[0] == 3:
            xyz = xyz.reshape(1, 3)
        n, ch = xyz.shape
        assert ch >= 3
        if ch == 3:
            xyzrgba = np.c_[xyz, np.ones((n, 4))]
        elif ch == 4:
            xyzrgba = np.c_[xyz[:, :3], xyz[:, 3:4] * [1, 1, 1], np.ones((n, 1))]
        elif ch == 6:
            xyzrgba = np.c_[xyz, np.ones((n, 1))]
        elif ch == 7:
            xyzrgba = xyz
        else:
            raise RuntimeError("unknown number of channels")

        assert (xyzrgba.shape[1] == 7)

        if alpha:
            xyzrgba[:, -1] = alpha
        if color is not None:
            if isinstance(color, str):
                xyzrgba[:, 3:6] = np.array(cls._str2rgb(color))
            elif hasattr(color, '__len__'):
                if len(color) == 3:  # fixed rgb
                    xyzrgba[:, 3:6] = np.array(color)
                elif color.size == n:
                    xyzrgba[:, 3:6] = color.reshape(-1, 1)
                elif color.size // 3 == n:
                    xyzrgba[:, 3:6] = color.reshape(-1, 3)
                elif color.size // 4 == n:
                    xyzrgba[:, 3:7] = color.reshape(-1, 4)
                else:
                    raise RuntimeError("unknown color option")
        rgba = cls._rgba2floatcol(xyzrgba[:, 3:])
        return np.c_[xyz[:, :3].astype(np.float32), rgba]

    def _set_cam_look_at(self, e, c, u):
        e, c, u = [x.tolist() if isinstance(x, np.ndarray) else x for x in [e, c, u]]
        return self.zv.setCameraLookAt(e, c, u)

    @staticmethod
    def _rotation_matrix(rot_vec):
        rot_vec = np.asarray(rot_vec)
        rot_vec = np.array(rot_vec)
        angle = np.linalg.norm(rot_vec)
        if angle == 0:
            return np.eye(3)
        v = rot_vec.flatten() / angle
        c = np.array(((0, -v[2], v[1]), (v[2], 0, -v[0]), (-v[1], v[0], 0)))
        r = np.eye(3) + c * np.sin(angle) + (1 - np.cos(angle)) * c @ c
        return r

    @classmethod
    def _get_tform(cls, tform_or_trs: Union[tuple, np.ndarray]):
        if isinstance(tform_or_trs, np.ndarray) and tform_or_trs.shape == (4, 4):
            tform = tform_or_trs
        elif isinstance(tform_or_trs, np.ndarray) and tform_or_trs.shape == (3, 4):
            tform = np.eye(4)
            tform[:3, :] = tform_or_trs
        elif isinstance(tform_or_trs, tuple) and len(tform_or_trs) == 3:
            t, r, s = tform_or_trs

            tform = np.eye(4)
            if r is None:
                pass
            elif isinstance(r, np.ndarray) and (r.shape == (3, 3)):
                tform[:3, :3] = r
            elif hasattr(r, '__len__') and len(r) == 3:
                tform[:3, :3] = cls._rotation_matrix(r)
            else:
                raise RuntimeError("unknown rotation strucutre")

            sv = np.eye(4)
            if s is None:
                pass
            elif isinstance(s, float) or isinstance(s, int):
                sv[0, 0] = sv[1, 1] = sv[2, 2] = s
            elif hasattr(s, '__len__') and len(s) == 3:
                for i in range(3):
                    sv[i, i] = s[i]
            else:
                raise RuntimeError("unknown scale structure")
            tform = tform @ sv
            if t is None:
                pass
            else:
                assert len(t) == 3
                tform[:3, -1] = np.asarray(t).flatten()
        else:
            raise RuntimeError("unknown transforation structure")
        return tform

    def _set_obj(self, objtype, namehandle, tform_or_trs, color=None, alpha=None):
        tform = self._get_tform(tform_or_trs)

        xyzf = self._get_pts_arr(self.objects[objtype]['v'], color, 1)
        xyzf[:, :3] = xyzf[:, :3] @ tform[:3, :3].T + tform[:3, -1]

        if isinstance(namehandle, str):
            handlenum = self.zv.getHandleNumFromString(namehandle)
            if handlenum == -1:
                f = self.objects[objtype]['f']
                handlenum = self.add_trimesh(namehandle, xyzf, f, color, alpha)
            else:
                self.zv.updateColoredPoints(handlenum, xyzf)
            return handlenum
        else:
            self.zv.updateColoredPoints(namehandle, xyzf)
            return namehandle

    def __init__(self):
        self.zv = zview_module.interface()  # get interface
        s = 1 / np.sqrt(3)
        self.objects = dict()
        self.objects['marker'] = {'v': np.array([[-1, -s, 0], [0, 2 * s, 0], [1, -s, 0], [0, 0, np.sqrt(8) * s]]) / 2,
                                  'f': np.array([[0, 3, 1], [1, 3, 2], [0, 2, 3], [0, 2, 1]]),
                                  'counter': 0}
        self.objects['rect'] = {'v': np.array(
            [[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0], [0, 0, 1], [0, 1, 1], [1, 1, 1], [1, 0, 1]]) * 2 - 1,
                                'f': np.array(
                                    [[3, 1, 0], [3, 1, 2], [3, 6, 2], [3, 7, 6], [0, 1, 5], [0, 5, 4], [0, 7, 4],
                                     [0, 3, 7],
                                     [1, 2, 6],
                                     [1, 6, 5],
                                     [5, 6, 7], [4, 5, 7]])}
        self.objects['camera'] = {'v': np.array(
            [[0, 0, 0], [1, 1, 1], [-1, 1, 1], [-1, -1, 1], [1, -1, 1], [1, 0, 0], [1, 0.1, 0], [0, 1, 0],
             [0.1, 1, 0]]),
            'f': np.array(
                [[0, 1, 2],
                 [0, 2, 3],
                 [0, 3, 4],
                 [0, 4, 1],
                 [1, 2, 3], [1, 3, 4],
                 [0, 6, 5], [0, 7, 8]])}

    def add_rectangle(self, name, tform_or_trs, color=None, alpha=None):
        """
        :param name: object name or handle
        :param tform_or_trs: 4x4 transofrmation, or (translation,rotation,scale) tuple
        :param color: color rgb triplet, or  single char ('r','g','b','k' ,'c','m','y')
        :param alpha: transparency
        :return: handle to the drawn object
        exmaple:
        zv = Pyzview()
        zv.add_rectangle("rect",np.eye(4),color='r')
        t = (0,0,3)
        r = (0,0,np.pi/4)
        s = (1,2,3)
        zv.add_rectangle("rect", (t,r,s), color='r')
        """
        return self._set_obj('rect', name, tform_or_trs, color, alpha)

    def add_marker(self, name, t, r=np.eye(3), scale=1.0, color=None, alpha=None):
        """
        :param scale: marker scale
        :param name: object name or handle
        :param t:translation
        :param r: rotation
        :param color: color rgb triplet, or  single char ('r','g','b','k' ,'c','m','y')
        :param alpha: transparency
        :return: handle to the drawn object
        exmaple:
        zv = Pyzview()
        zv.add_marker("rect",np.eye(4),color='r')
        t = (0,0,3)
        r = (0,0,np.pi/4)
        s = (1,2,3)
        zv.add_rectangle("rect", t,r,s, color='r')
        """
        return self._set_obj('marker', name, (t, r, scale), color, alpha)

    def add_camera(self, namehandle, t, r, scale=1.0, k=np.eye(3), color=None, alpha=None):
        tform = self._get_tform((t, r, None))
        v = self.objects['camera']['v'] * scale
        v[1:5] = v[1:5] @ np.linalg.inv(k).T
        v = v @ tform[:3, :3].T + tform[:3, -1]

        xyzf = self._get_pts_arr(v, color, alpha)
        xyzf[0:1] = self._get_pts_arr(v[0:1], 'w', alpha)
        xyzf[5:7] = self._get_pts_arr(v[5:7], 'r', alpha)
        xyzf[7:9] = self._get_pts_arr(v[7:9], 'g', alpha)
        xyzf = xyzf.copy()
        if isinstance(namehandle, str):
            handlenum = self.zv.getHandleNumFromString(namehandle)
            if handlenum == -1:
                f = self.objects['camera']['f']
                handlenum = self.zv.addColoredMesh(namehandle, xyzf, f)
            else:
                self.zv.updateColoredPoints(handlenum, xyzf)
            return handlenum
        else:
            self.zv.updateColoredPoints(namehandle, xyzf)
            return namehandle

    def add_trimesh(self, string, xyz, faces, color=None, alpha=None):
        if len(xyz.shape) != 2:
            raise RuntimeError("expecting nxD for D>=3")
        xyzf = self._get_pts_arr(xyz, color, alpha)
        k = self.zv.addColoredMesh(string, xyzf, faces)
        if k == -1:
            raise RuntimeWarning("could not get response from zview app")
        return k

    def add_edges(self, string, xyz, edgepair, color=None, alpha=None):
        if len(xyz.shape) != 2:
            raise RuntimeError("expecting nxD for D>=3")
        xyzf = self._get_pts_arr(xyz, color, alpha)
        k = self.zv.addColoredEdges(string, xyzf, edgepair)
        if k == -1:
            raise RuntimeWarning("could not get response from zview app")
        return k

    def add_mesh(self, namehandle, xyz, color=None, alpha=None):
        if len(xyz.shape) != 3:
            raise RuntimeError("expecting nxmxD for D>=3")
        xyzf = self._get_pts_arr(xyz.reshape(-1, xyz.shape[2]), color, alpha)
        if isinstance(namehandle, str):
            handlenum = self.zv.getHandleNumFromString(namehandle)
            if handlenum == -1:
                faces = self._get_trimesh_indices(xyz.shape)
                handlenum = self.zv.addColoredMesh(namehandle, xyzf, faces)
            else:
                self.zv.updateColoredPoints(handlenum, xyzf)
            return handlenum
        else:
            self.zv.updateColoredPoints(namehandle, xyzf)
            return namehandle

    def remove_shape(self, namehandle):
        if isinstance(namehandle, str):
            namehandle = self.zv.getHandleNumFromString(namehandle)
            if namehandle == -1:
                return

        return self.zv.removeShape(namehandle)

    def add_points(self, namehandle, xyz, color=None, alpha=None):
        xyzf = self._get_pts_arr(xyz, color, alpha)
        if isinstance(namehandle, str):
            handlenum = self.zv.getHandleNumFromString(namehandle)
            if handlenum == -1:
                handlenum = self.zv.addColoredPoints(namehandle, xyzf)
            else:
                ok = self.zv.updateColoredPoints(handlenum, xyzf)
                if not ok:
                    #visualization data is stored in a vertex buffer. If you are tryig to update an array which is bigger than the vertex buffer, than we have a problem...
                    raise RuntimeError(
                        "could not update points with the different size. create a new set for new point size")
            return handlenum
        else:
            self.zv.updateColoredPoints(namehandle, xyzf)
            return namehandle

    KEY_ESC = 16777216
    KEY_ENTER = 16777220

    def get_last_keystroke(self):
        return self.zv.getLastKeyStroke()
