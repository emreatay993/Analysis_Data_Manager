try:
    from OCP.STEPControl import STEPControl_Reader  # type: ignore
    from OCP.IFSelect import IFSelect_RetDone  # type: ignore
    from OCP.TopoDS import TopoDS_Shape  # type: ignore
    from OCP.BRepMesh import BRepMesh_IncrementalMesh  # type: ignore
    OCC_AVAILABLE = True
except Exception:  # pragma: no cover
    STEPControl_Reader = None  # type: ignore
    IFSelect_RetDone = None  # type: ignore
    TopoDS_Shape = None  # type: ignore
    BRepMesh_IncrementalMesh = None  # type: ignore
    OCC_AVAILABLE = False


def load_step_shape(path: str):
    if not OCC_AVAILABLE:
        return None
    reader = STEPControl_Reader()
    status = reader.ReadFile(path)
    if status != IFSelect_RetDone:
        return None
    ok = reader.TransferRoots()
    if not ok:
        return None
    shape = reader.OneShape()
    # mesh to ensure triangulation when needed
    BRepMesh_IncrementalMesh(shape, 0.5)
    return shape
