from PyQt5 import QtWidgets

# Try pythonocc-core Qt viewer first
try:
    from OCC.Display.backend import load_backend  # type: ignore
    try:
        load_backend()  # auto-detect (e.g., qt-pyqt5) if available
    except Exception:
        load_backend("qt-pyqt5")
    from OCC.Display.qtDisplay import qtViewer3d  # type: ignore
    from OCC.Core.AIS import AIS_Shape  # type: ignore
    from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB  # type: ignore
    OCC_QT_OK = True
except Exception:
    OCC_QT_OK = False

# Fallback: pyqtgraph OpenGL viewer
try:
    import pyqtgraph as pg  # noqa: F401
    import pyqtgraph.opengl as gl
    import numpy as np
    GL_OK = True
except Exception:
    GL_OK = False
    gl = None  # type: ignore
    np = None  # type: ignore


class AssemblyViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self._name_to_item = {}
        self._mode = 'none'
        self._did_initial_fit = False

        # Controls hint removed

        if OCC_QT_OK:
            self._viewer = qtViewer3d(self)
            layout.addWidget(self._viewer)
            self._ctx = self._viewer._display.Context
            self._mode = 'occt'
            # Fit-all on double click when available
            try:
                self._viewer.sig_double_click.connect(lambda: self._viewer._display.FitAll())
            except Exception:
                pass
            return

        if GL_OK:
            self._view = gl.GLViewWidget()
            self._view.opts['distance'] = 200
            layout.addWidget(self._view)
            g = gl.GLGridItem(); g.scale(10, 10, 1); self._view.addItem(g)
            self._bbox_min = None
            self._bbox_max = None
            self._mode = 'gl'
            return

        layout.addWidget(QtWidgets.QLabel("3D viewer unavailable. Install pythonocc-core (preferred) or PyOpenGL + pyqtgraph."))

    def clear(self):
        if self._mode == 'occt':
            try:
                self._viewer._display.EraseAll()
                self._name_to_item.clear()
                self._did_initial_fit = False
            except Exception:
                pass
        elif self._mode == 'gl':
            for item in list(self._name_to_item.values()):
                self._view.removeItem(item)
            self._name_to_item.clear()
            self._bbox_min = None
            self._bbox_max = None
            self._did_initial_fit = False

    # ====== OCCT path ======
    def add_occ_shape(self, name: str, shape):
        if self._mode == 'occt' and shape is not None:
            try:
                ais = AIS_Shape(shape)
                self._ctx.Display(ais, True)
                self._name_to_item[name] = ais
                if not self._did_initial_fit:
                    self._viewer._display.FitAll()
                    self._did_initial_fit = True
            except Exception:
                pass

    def highlight_pair(self, name_a: str, name_b: str):
        if self._mode == 'occt':
            for n, ais in self._name_to_item.items():
                try:
                    if n == name_a or n == name_b:
                        self._ctx.SetColor(ais, Quantity_Color(1.0, 0.4, 0.2, Quantity_TOC_RGB), False)
                    else:
                        self._ctx.SetColor(ais, Quantity_Color(0.7, 0.7, 0.7, Quantity_TOC_RGB), False)
                except Exception:
                    continue
            self._viewer._display.Repaint()
        elif self._mode == 'gl':
            for n, item in self._name_to_item.items():
                if n == name_a or n == name_b:
                    item.setColor((1.0, 0.4, 0.2, 1.0))
                else:
                    item.setColor((0.7, 0.7, 0.7, 1.0))

    # ====== GL fallback path ======
    def _accumulate_bounds(self, vertices):
        if self._mode != 'gl':
            return
        if vertices.size == 0:
            return
        vmin = vertices.min(axis=0)
        vmax = vertices.max(axis=0)
        if getattr(self, '_bbox_min', None) is None:
            self._bbox_min = vmin.copy(); self._bbox_max = vmax.copy()
        else:
            self._bbox_min = np.minimum(self._bbox_min, vmin)
            self._bbox_max = np.maximum(self._bbox_max, vmax)
        if not self._did_initial_fit:
            center = (self._bbox_min + self._bbox_max) * 0.5
            diag = float(np.linalg.norm(self._bbox_max - self._bbox_min))
            dist = max(100.0, diag * 1.5)
            try:
                self._view.opts['center'] = pg.Vector(center[0], center[1], center[2])
                self._view.setCameraPosition(distance=dist)
                self._did_initial_fit = True
            except Exception:
                pass

    def add_mesh(self, name: str, vertices, faces, color=(0.7, 0.7, 0.7, 1.0)):
        if self._mode != 'gl':
            return
        try:
            vertices = vertices.astype('float32', copy=False)
            faces = faces.astype('int32', copy=False)
        except Exception:
            pass
        if name in self._name_to_item:
            self._view.removeItem(self._name_to_item[name])
        mesh = gl.GLMeshItem(vertexes=vertices, faces=faces, smooth=False, drawEdges=True, edgeColor=(0.2,0.2,0.2,1), color=color)
        mesh.setGLOptions('opaque')
        self._name_to_item[name] = mesh
        self._view.addItem(mesh)
        self._accumulate_bounds(vertices)
