import numpy as np

try:
    from OCP.TopoDS import TopoDS_Shape  # type: ignore
    from OCP.TopExp import TopExp_Explorer  # type: ignore
    from OCP.TopAbs import TopAbs_FACE  # type: ignore
    from OCP.BRep import BRep_Tool  # type: ignore
    from OCP.BRepMesh import BRepMesh_IncrementalMesh  # type: ignore
    from OCP.TopLoc import TopLoc_Location  # type: ignore
    from OCP.TopoDS import topods_Face  # type: ignore
    OCC_OK = True
except Exception:  # pragma: no cover
    try:
        from OCC.Core.TopoDS import TopoDS_Shape  # type: ignore
        from OCC.Core.TopExp import TopExp_Explorer  # type: ignore
        from OCC.Core.TopAbs import TopAbs_FACE  # type: ignore
        from OCC.Core.BRep import BRep_Tool  # type: ignore
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh  # type: ignore
        from OCC.Core.TopLoc import TopLoc_Location  # type: ignore
        from OCC.Core.TopoDS import topods_Face  # type: ignore
        OCC_OK = True
    except Exception:  # pragma: no cover
        OCC_OK = False


def _apply_loc(pnt, loc):
    try:
        trsf = loc.Transformation()
        tp = pnt.Transformed(trsf)
        return [tp.X(), tp.Y(), tp.Z()]
    except Exception:
        return [pnt.X(), pnt.Y(), pnt.Z()]


def shape_to_mesh(shape) -> tuple[np.ndarray, np.ndarray]:
    if not OCC_OK or shape is None:
        return np.zeros((0,3), dtype=float), np.zeros((0,3), dtype=int)
    try:
        # Generate tessellation with finer deflection
        BRepMesh_IncrementalMesh(shape, 0.2)
        verts = []
        faces = []
        exp = TopExp_Explorer(shape, TopAbs_FACE)
        base_index = 0
        while exp.More():
            try:
                sh = exp.Current()
            except Exception:
                exp.Next()
                continue
            try:
                if sh.IsNull():
                    exp.Next(); continue
            except Exception:
                pass
            try:
                face = topods_Face(sh)
            except Exception:
                exp.Next(); continue
            loc = face.Location() if hasattr(face, 'Location') else TopLoc_Location()
            try:
                tri = BRep_Tool.Triangulation(face, TopLoc_Location())
            except Exception:
                tri = BRep_Tool.Triangulation(face)
            if tri is None:
                exp.Next(); continue
            try:
                if hasattr(tri, 'IsNull') and tri.IsNull():
                    exp.Next(); continue
            except Exception:
                pass
            # Grab nodes via Node(i)
            try:
                nb_nodes = int(tri.NbNodes())
            except Exception:
                nb_nodes = 0
            for i in range(1, nb_nodes + 1):
                try:
                    p = tri.Node(i)
                    verts.append(_apply_loc(p, loc))
                except Exception:
                    continue
            # Grab triangles via Triangle(i)
            try:
                nb_tris = int(tri.NbTriangles())
            except Exception:
                nb_tris = 0
            for i in range(1, nb_tris + 1):
                try:
                    t = tri.Triangle(i)
                    try:
                        i1 = t.Value(1); i2 = t.Value(2); i3 = t.Value(3)
                    except Exception:
                        try:
                            i1, i2, i3 = t.Get()
                        except Exception:
                            continue
                    faces.append([base_index + i1 - 1, base_index + i2 - 1, base_index + i3 - 1])
                except Exception:
                    continue
            base_index = len(verts)
            exp.Next()
        if not verts or not faces:
            return np.zeros((0,3), dtype=float), np.zeros((0,3), dtype=int)
        return np.array(verts, dtype=float), np.array(faces, dtype=int)
    except Exception:
        return np.zeros((0,3), dtype=float), np.zeros((0,3), dtype=int)
