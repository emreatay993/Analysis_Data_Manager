from PyQt5 import QtWidgets, QtCore, QtGui

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
    from OCC.Core.Aspect import Aspect_TOTP_LEFT_LOWER
    from OCC.Core.V3d import V3d_ZBUFFER
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
        self._name_to_base_color = {}
        self._palette_index = 0
        # 9-class ColorBrewer RdYlBu palette (hex)
        self._palette_hex = [
            "#d73027", "#f46d43", "#fdae61", "#fee090", "#ffffbf",
            "#e0f3f8", "#abd9e9", "#74add1", "#4575b4",
        ]
        # Distinct highlight color (bright green)
        self._highlight_rgb = (0.1, 0.8, 0.2)
        self._mode = 'none'
        self._did_initial_fit = False
        self._is_perspective = True
        self._lights_enabled = False

        # Help button overlay (top-right)
        try:
            self._help_btn = QtWidgets.QToolButton(self)
            self._help_btn.setText("?")
            self._help_btn.setToolTip("Viewer shortcuts")
            self._help_btn.setAutoRaise(True)
            self._help_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self._help_btn.clicked.connect(self._show_shortcuts_help)
            self._help_btn.raise_()
        except Exception:
            self._help_btn = None

        if OCC_QT_OK:
            self._viewer = qtViewer3d(self)
            layout.addWidget(self._viewer)
            self._ctx = self._viewer._display.Context
            self._mode = 'occt'
            try:
                print("[Viewer] Initialized OCC viewer (qtViewer3d) successfully.")
            except Exception:
                pass
            # Route key presses from the inner OCC widget to this widget's handler
            try:
                self._viewer.installEventFilter(self)
            except Exception:
                pass
            # Fit-all on double click when available
            try:
                self._viewer.sig_double_click.connect(lambda: self._viewer._display.FitAll())
            except Exception as e:
                print(e)
                pass
            # Orientation widget: show only a view cube (larger) and disable triedron
            try:
                white = Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB)
                self._viewer._display.View.TriedronDisplay(
                    Aspect_TOTP_LEFT_LOWER,
                    white, # <-- Pass the object
                    0.2,
                    V3d_ZBUFFER
                )
                #self._add_view_cube_only()
            except Exception as e:
                print(e)
                pass
            # Default: enable viewer lights and shaded model
            try:
                vwr = self._viewer._display.Viewer
                view = self._viewer._display.View
                try:
                    vwr.SetDefaultLightsOn()
                except Exception:
                    pass
                try:
                    vwr.SetLightOn()
                except Exception:
                    pass
                try:
                    vwr.UpdateLights()
                except Exception:
                    pass
                try:
                    from OCC.Core.Graphic3d import Graphic3d_TOSM_FRAGMENT  # type: ignore
                    view.SetShadingModel(Graphic3d_TOSM_FRAGMENT)
                except Exception:
                    pass
                self._lights_enabled = True
            except Exception:
                pass
            return

        if GL_OK:
            self._view = gl.GLViewWidget()
            self._view.opts['distance'] = 200
            layout.addWidget(self._view)
            try:
                self._view.installEventFilter(self)
            except Exception:
                pass
            g = gl.GLGridItem(); g.scale(10, 10, 1); self._view.addItem(g)
            self._bbox_min = None
            self._bbox_max = None
            self._mode = 'gl'
            # Orientation axes for GL fallback
            try:
                print("[Viewer] GL fallback active; adding GLAxisItem for orientation.")
                ax = gl.GLAxisItem()
                ax.setSize(x=120, y=120, z=120)
                self._view.addItem(ax)
                self._axis_item = ax
                try:
                    print("[Viewer] GL axis created (size ~120).")
                except Exception:
                    pass
            except Exception:
                self._axis_item = None
            return

        layout.addWidget(QtWidgets.QLabel("3D viewer unavailable. Install pythonocc-core (preferred) or PyOpenGL + pyqtgraph."))
        
        # Overlay axes widget (always-on)
        try:
            self._axes_overlay = _AxesOverlayWidget(self)
            self._axes_overlay.show()
            self._update_overlay_position()
        except Exception:
            self._axes_overlay = None

    def clear(self):
        if self._mode == 'occt':
            try:
                self._viewer._display.EraseAll()
                self._name_to_item.clear()
                self._name_to_base_color.clear()
                self._palette_index = 0
                self._did_initial_fit = False
            except Exception:
                pass
        elif self._mode == 'gl':
            for item in list(self._name_to_item.values()):
                self._view.removeItem(item)
            self._name_to_item.clear()
            self._name_to_base_color.clear()
            self._palette_index = 0
            self._bbox_min = None
            self._bbox_max = None
            self._did_initial_fit = False

    # ====== OCCT path ======
    def _enforce_unlit(self):
        if getattr(self, '_mode', None) != 'occt':
            return
        disp = getattr(self._viewer, '_display', None)
        if disp is None:
            return
        view = disp.View
        viewer_handle = disp.Viewer
        # Deactivate all lights at once, then disable default lights and update
        try:
            viewer_handle.SetLightOff()
        except Exception:
            pass
        try:
            viewer_handle.SetDefaultLightsOff()
        except Exception:
            pass
        try:
            viewer_handle.UpdateLights()
        except Exception:
            pass
        from OCC.Core.Graphic3d import Graphic3d_TOSM_UNLIT  # type: ignore
        view.SetShadingModel(Graphic3d_TOSM_UNLIT)
        disp.Repaint()
        self._lights_enabled = False

    def _toggle_default_lighting(self):
        if self._mode != 'occt':
            return
        disp = getattr(self._viewer, '_display', None)
        if disp is None:
            return
        view = disp.View
        viewer_handle = disp.Viewer
        if self._lights_enabled:
            # Turn off
            try:
                viewer_handle.SetLightOff()
            except Exception:
                pass
            try:
                viewer_handle.SetDefaultLightsOff()
            except Exception:
                pass
            try:
                viewer_handle.UpdateLights()
            except Exception:
                pass
            try:
                from OCC.Core.Graphic3d import Graphic3d_TOSM_UNLIT  # type: ignore
                view.SetShadingModel(Graphic3d_TOSM_UNLIT)
            except Exception:
                pass
            self._lights_enabled = False
        else:
            # Turn on
            try:
                viewer_handle.SetDefaultLightsOn()
            except Exception:
                pass
            try:
                viewer_handle.SetLightOn()
            except Exception:
                pass
            try:
                viewer_handle.UpdateLights()
            except Exception:
                pass
            try:
                # Use default shaded model
                from OCC.Core.Graphic3d import Graphic3d_TOSM_FRAGMENT  # type: ignore
                view.SetShadingModel(Graphic3d_TOSM_FRAGMENT)
            except Exception:
                pass
            self._lights_enabled = True
        try:
            disp.Repaint()
        except Exception:
            pass


    

    
    def add_occ_shape(self, name: str, shape):
        if self._mode == 'occt' and shape is not None:
            try:
                ais = AIS_Shape(shape)
                self._ctx.Display(ais, True)
                base_rgb = self._get_or_assign_base_rgb(name)
                try:
                    self._ctx.SetColor(ais, Quantity_Color(base_rgb[0], base_rgb[1], base_rgb[2], Quantity_TOC_RGB), False)
                except Exception:
                    pass
                # Ensure shaded mode and draw black edges (face boundaries)
                try:
                    # 1 == AIS_Shaded (avoid extra import of AIS_DisplayMode)
                    self._ctx.SetDisplayMode(ais, 1, False)
                except Exception:
                    pass
                try:
                    from OCC.Core.Prs3d import Prs3d_Drawer, Prs3d_LineAspect  # type: ignore
                    from OCC.Core.Aspect import Aspect_TOL_SOLID  # type: ignore
                    from OCC.Core.Quantity import Quantity_NOC_BLACK  # type: ignore
                    from OCC.Core.Graphic3d import Graphic3d_AspectFillArea3d  # type: ignore
                    # Obtain (or create) the drawer and set face boundary draw + black boundary aspect
                    try:
                        drawer = ais.Attributes()
                    except Exception:
                        drawer = None
                    if drawer is None or getattr(drawer, 'IsNull', lambda: False)():
                        drawer = Prs3d_Drawer()
                    drawer.SetFaceBoundaryDraw(True)
                    black = Quantity_Color(Quantity_NOC_BLACK)
                    line_aspect = Prs3d_LineAspect(black, Aspect_TOL_SOLID, 1.0)
                    drawer.SetFaceBoundaryAspect(line_aspect)
                    # Also set wire aspect to black for wireframe/edge views
                    try:
                        drawer.SetWireAspect(Prs3d_LineAspect(black, Aspect_TOL_SOLID, 1.0))
                    except Exception:
                        pass
                    # Ensure facet (triangle) edges are NOT drawn; rely on face boundaries only
                    try:
                        sh_aspect = drawer.ShadingAspect()
                        fill = sh_aspect.Aspect()
                        try:
                            fill.SetEdgeOff()
                        except Exception:
                            pass
                        drawer.SetShadingAspect(sh_aspect)
                    except Exception:
                        pass
                    ais.SetAttributes(drawer)
                    # Apply attribute changes immediately
                    try:
                        self._ctx.Redisplay(ais, True)
                    except Exception:
                        pass
                except Exception:
                    pass
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
                        self._ctx.SetColor(ais, Quantity_Color(self._highlight_rgb[0], self._highlight_rgb[1], self._highlight_rgb[2], Quantity_TOC_RGB), False)
                    else:
                        base_rgb = self._name_to_base_color.get(n, (0.7, 0.7, 0.7))
                        self._ctx.SetColor(ais, Quantity_Color(base_rgb[0], base_rgb[1], base_rgb[2], Quantity_TOC_RGB), False)
                except Exception:
                    continue
            self._viewer._display.Repaint()
        elif self._mode == 'gl':
            for n, item in self._name_to_item.items():
                if n == name_a or n == name_b:
                    item.setColor((self._highlight_rgb[0], self._highlight_rgb[1], self._highlight_rgb[2], 1.0))
                else:
                    base_rgb = self._name_to_base_color.get(n, (0.7, 0.7, 0.7))
                    item.setColor((base_rgb[0], base_rgb[1], base_rgb[2], 1.0))

    def highlight_names(self, names: list[str]):
        target = set(names or [])
        if self._mode == 'occt':
            for n, ais in self._name_to_item.items():
                try:
                    if n in target:
                        self._ctx.SetColor(ais, Quantity_Color(self._highlight_rgb[0], self._highlight_rgb[1], self._highlight_rgb[2], Quantity_TOC_RGB), False)
                    else:
                        base_rgb = self._name_to_base_color.get(n, (0.7, 0.7, 0.7))
                        self._ctx.SetColor(ais, Quantity_Color(base_rgb[0], base_rgb[1], base_rgb[2], Quantity_TOC_RGB), False)
                except Exception:
                    continue
            try:
                self._viewer._display.Repaint()
            except Exception:
                pass
        elif self._mode == 'gl':
            for n, item in self._name_to_item.items():
                try:
                    if n in target:
                        item.setColor((self._highlight_rgb[0], self._highlight_rgb[1], self._highlight_rgb[2], 1.0))
                    else:
                        base_rgb = self._name_to_base_color.get(n, (0.7, 0.7, 0.7))
                        item.setColor((base_rgb[0], base_rgb[1], base_rgb[2], 1.0))
                except Exception:
                    continue

    def clear_highlight(self):
        if self._mode == 'occt':
            for _, ais in self._name_to_item.items():
                try:
                    # Restore each item's base color
                    name_match = None
                    for k, v in self._name_to_item.items():
                        if v is ais:
                            name_match = k
                            break
                    base_rgb = self._name_to_base_color.get(name_match, (0.7, 0.7, 0.7))
                    self._ctx.SetColor(ais, Quantity_Color(base_rgb[0], base_rgb[1], base_rgb[2], Quantity_TOC_RGB), False)
                except Exception:
                    continue
            try:
                self._viewer._display.Repaint()
            except Exception:
                pass
        elif self._mode == 'gl':
            for name, item in self._name_to_item.items():
                try:
                    base_rgb = self._name_to_base_color.get(name, (0.7, 0.7, 0.7))
                    item.setColor((base_rgb[0], base_rgb[1], base_rgb[2], 1.0))
                except Exception:
                    continue

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
        base_rgb = self._get_or_assign_base_rgb(name)
        mesh = gl.GLMeshItem(vertexes=vertices, faces=faces, smooth=False, computeNormals=False, drawEdges=True, edgeColor=(0.0,0.0,0.0,1.0), color=(base_rgb[0], base_rgb[1], base_rgb[2], 1.0))
        mesh.setGLOptions('opaque')
        try:
            mesh.setShader(None)
        except Exception:
            pass
        self._name_to_item[name] = mesh
        self._view.addItem(mesh)
        self._accumulate_bounds(vertices)

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        try:
            self._update_overlay_position()
        except Exception:
            pass
        try:
            self._update_help_position()
        except Exception:
            pass

    def _update_overlay_position(self):
        if getattr(self, '_axes_overlay', None) is None:
            return
        margin = 10
        w = self._axes_overlay.width()
        h = self._axes_overlay.height()
        self._axes_overlay.move(max(0, self.width() - w - margin), max(0, self.height() - h - margin))

    def _update_help_position(self):
        btn = getattr(self, '_help_btn', None)
        if btn is None:
            return
        margin = 8
        w = btn.sizeHint().width()
        btn.move(max(0, self.width() - w - margin), margin)
        btn.raise_()

    def _show_shortcuts_help(self):
        msg = [
            "Keyboard shortcuts:",
            "",
            "General:",
            "  • Double-click: Fit all (when available)",
            "  • F: Fit all", 
            "  • R: Reset view",
            "",
            "Projection:",
            "  • W: Orthographic", 
            "  • P: Perspective", 
            "  • 5: Toggle Ortho/Perspective",
            "",
            "View orientations (OCCT):",
            "  • 1: Front   • 3: Right   • 7: Top   • 9: Iso",
            "  • 2: Bottom  • 4: Left    • 8: Top   • 6: Right   • 0: Back",
            "",
            "Lighting (OCCT):",
            "  • L: Toggle default lighting on/off",
        ]
        try:
            QtWidgets.QMessageBox.information(self, "3D Viewer Shortcuts", "\n".join(msg))
        except Exception:
            pass

    # ====== Keyboard shortcuts ======
    def keyPressEvent(self, event):
        try:
            k = int(event.key())
            disp = getattr(getattr(self, '_viewer', None), '_display', None)
            if self._mode == 'occt' and disp is not None:
                if k == QtCore.Qt.Key_F:
                    try:
                        disp.FitAll()
                    finally:
                        return
                if k == QtCore.Qt.Key_R:
                    try:
                        disp.ResetView()
                    finally:
                        return
                if k == QtCore.Qt.Key_L:
                    try:
                        self._toggle_default_lighting()
                    finally:
                        return
                if k == QtCore.Qt.Key_W:
                    try:
                        disp.SetOrthographicProjection()
                        self._is_perspective = False
                        # Enforce lights/headlight off after projection change
                        self._enforce_unlit()
                    finally:
                        return
                if k == QtCore.Qt.Key_P:
                    try:
                        disp.SetPerspectiveProjection()
                        self._is_perspective = True
                        # Enforce lights/headlight off after projection change
                        self._enforce_unlit()
                    finally:
                        return
                # Numpad-style view controls
                if k in (QtCore.Qt.Key_5,):
                    try:
                        if self._is_perspective:
                            disp.SetOrthographicProjection(); self._is_perspective = False
                        else:
                            disp.SetPerspectiveProjection(); self._is_perspective = True
                    finally:
                        return
                view_map = {
                    QtCore.Qt.Key_1: 'View_Front',
                    QtCore.Qt.Key_3: 'View_Right',
                    QtCore.Qt.Key_7: 'View_Top',
                    QtCore.Qt.Key_9: 'View_Iso',
                    QtCore.Qt.Key_2: 'View_Bottom',
                    QtCore.Qt.Key_4: 'View_Left',
                    QtCore.Qt.Key_8: 'View_Top',
                    QtCore.Qt.Key_6: 'View_Right',
                    QtCore.Qt.Key_0: 'View_Back',
                }
                if k in view_map:
                    fn = getattr(disp, view_map[k], None)
                    if callable(fn):
                        try:
                            fn()
                            # Re-apply unlit/no-light state after view orientation changes
                            self._enforce_unlit()
                        finally:
                            return
                    # Fallback to direct projection if wrappers are missing
                    try:
                        from OCC.Core.V3d import V3d_TypeOfOrientation, V3d_Xpos, V3d_Xneg, V3d_Ypos, V3d_Yneg, V3d_Zpos, V3d_Zneg  # type: ignore
                        v = getattr(disp, 'View', None)
                        if v is not None:
                            if k == QtCore.Qt.Key_1:
                                v.SetProj(V3d_Yneg)
                            elif k == QtCore.Qt.Key_3:
                                v.SetProj(V3d_Xpos)
                            elif k == QtCore.Qt.Key_7 or k == QtCore.Qt.Key_8:
                                v.SetProj(V3d_Zpos)
                            elif k == QtCore.Qt.Key_4:
                                v.SetProj(V3d_Xneg)
                            elif k == QtCore.Qt.Key_6:
                                v.SetProj(V3d_Xpos)
                            elif k == QtCore.Qt.Key_0:
                                v.SetProj(V3d_Ypos)
                            elif k == QtCore.Qt.Key_9:
                                v.SetProj(1.0, 1.0, 1.0)  # generic isometric
                            # Re-apply unlit/no-light state after view orientation changes
                            self._enforce_unlit()
                            return
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            super().keyPressEvent(event)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            et = int(getattr(event, 'type', lambda: -1)())
            if et == int(QtCore.QEvent.KeyPress):
                # Forward to our keyPressEvent and consume
                try:
                    self.keyPressEvent(event)
                    return True
                except Exception:
                    return False
        except Exception:
            pass
        try:
            return super().eventFilter(obj, event)
        except Exception:
            return False

    # ====== Color helpers ======
    def _hex_to_rgbf(self, hex_str: str):
        hs = hex_str.lstrip('#')
        if len(hs) == 6:
            r = int(hs[0:2], 16) / 255.0
            g = int(hs[2:4], 16) / 255.0
            b = int(hs[4:6], 16) / 255.0
            return (r, g, b)
        return (0.7, 0.7, 0.7)

    def _get_or_assign_base_rgb(self, name: str):
        if name in self._name_to_base_color:
            return self._name_to_base_color[name]
        hex_color = self._palette_hex[self._palette_index % len(self._palette_hex)]
        self._palette_index += 1
        rgb = self._hex_to_rgbf(hex_color)
        self._name_to_base_color[name] = rgb
        return rgb

    # ====== Orientation (OCC): View cube only ======
    def _add_view_cube_only(self):
        """
        A robust method to add an interactive AIS_ViewCube.
        This version removes the Z-Layer call for maximum compatibility.
        """
        try:
            from OCC.Core.AIS import AIS_ViewCube
            from OCC.Core.Graphic3d import Graphic3d_TransformPers, Graphic3d_TMF_TriedronPers
            from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

            # Erase the simple triedron if it exists
            self._viewer._display.View.TriedronErase()

            # Create and configure the view cube
            self._view_cube = AIS_ViewCube()
            self._view_cube.SetSize(100)

            # Set a light color for the cube to stand out
            light_gray = Quantity_Color(0.8, 0.8, 0.8, Quantity_TOC_RGB)
            self._view_cube.SetBoxColor(light_gray)

            # Create the persistence object to lock it in a corner
            tp = Graphic3d_TransformPers(Graphic3d_TMF_TriedronPers)
            self._view_cube.SetTransformPersistence(tp)

            # Display the cube
            self._ctx.Display(self._view_cube, True)

            # **CRITICAL FIX**
            # Force the camera to zoom to fit all objects, including the new cube.
            self._viewer._display.FitAll()

            print("[Viewer] AIS_ViewCube displayed successfully.")

        except Exception as e:
            print(f"[Viewer] Failed to add AIS_ViewCube: {e}")
            # Fallback to the simple triedron if the cube fails
            try:
                self._viewer._display.View.TriedronDisplay()
            except Exception:
                pass


class _AxesOverlayWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setFixedSize(100, 100)

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        # Draw semi-transparent background circle for contrast
        bg = QtGui.QColor(255, 255, 255, 35)
        p.setBrush(bg)
        p.setPen(QtCore.Qt.NoPen)
        r = min(self.width(), self.height()) - 6
        p.drawEllipse(QtCore.QPointF(self.width() - r/2 - 3, self.height() - r/2 - 3), r/2, r/2)
        # Center near bottom-right inside the circle
        cx = self.width() - r/2 - 3
        cy = self.height() - r/2 - 3
        scale = r * 0.35

        def draw_axis(dx, dy, color, label):
            pen = QtGui.QPen(QtGui.QColor(*color), 2)
            p.setPen(pen)
            p.drawLine(QtCore.QPointF(cx, cy), QtCore.QPointF(cx + dx * scale, cy + dy * scale))
            # Arrowhead
            ah = 6
            p.drawEllipse(QtCore.QPointF(cx + dx * scale, cy + dy * scale), 1.5, 1.5)
            # Label
            p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
            p.drawText(QtCore.QPointF(cx + dx * (scale + 10), cy + dy * (scale + 10)), label)

        # Fixed isometric directions (screen space):
        # X → right, Y → up-left, Z → up-right (stylized triad)
        draw_axis(1.0, 0.0, (215, 48, 39), 'X')     # red-ish
        draw_axis(-0.6, -0.8, (29, 187, 75), 'Y')   # green
        draw_axis(0.6, -0.8, (69, 117, 180), 'Z')   # blue
        p.end()
