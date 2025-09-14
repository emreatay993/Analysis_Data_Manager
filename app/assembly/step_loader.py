# Try OCP (CadQuery) first, then fallback to pythonocc-core (OCC.Core)
try:
    from OCP.STEPControl import STEPControl_Reader  # type: ignore
    from OCP.IFSelect import IFSelect_RetDone  # type: ignore
    from OCP.TopoDS import TopoDS_Shape  # type: ignore
    from OCP.BRepMesh import BRepMesh_IncrementalMesh  # type: ignore
    OCC_AVAILABLE = True
    OCC_FLAVOR = "OCP"
except Exception:  # pragma: no cover
    try:
        from OCC.Core.STEPControl import STEPControl_Reader  # type: ignore
        from OCC.Core.IFSelect import IFSelect_RetDone  # type: ignore
        from OCC.Core.TopoDS import TopoDS_Shape  # type: ignore
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh  # type: ignore
        OCC_AVAILABLE = True
        OCC_FLAVOR = "pythonocc-core"
    except Exception:  # pragma: no cover
        STEPControl_Reader = None  # type: ignore
        IFSelect_RetDone = None  # type: ignore
        TopoDS_Shape = None  # type: ignore
        BRepMesh_IncrementalMesh = None  # type: ignore
        OCC_AVAILABLE = False
        OCC_FLAVOR = "none"

from app.data import store


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
    # Mesh to ensure triangulation when needed (mesh len is arbitrary here)
    BRepMesh_IncrementalMesh(shape, 1.0)
    return shape


def load_shape_for_member(project: str, part_base: str, rev_index: int):
    if not OCC_AVAILABLE:
        return None
    revs = store.read_all(project, "revisions.csv")
    for r in revs:
        if r.get("project") == project and r.get("part_base") == part_base and r.get("rev_index") == str(rev_index):
            path = r.get("step_path", "")
            if path:
                return load_step_shape(path)
    return None
