import os
from typing import List, Tuple, Dict

# Try OCP first, then pythonocc-core
try:
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # type: ignore
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common  # type: ignore
    from OCP.TopAbs import TopAbs_ShapeEnum  # type: ignore
    from OCP.GProp import GProp_GProps  # type: ignore
    import OCP.BRepGProp as BRepGPropMod  # type: ignore
    OCC_GEOM_AVAILABLE = True
    OCC_FLAVOR = "OCP"
except Exception:  # pragma: no cover
    try:
        from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape  # type: ignore
        from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common  # type: ignore
        from OCC.Core.TopAbs import TopAbs_ShapeEnum  # type: ignore
        from OCC.Core.GProp import GProp_GProps  # type: ignore
        import OCC.Core.BRepGProp as BRepGPropMod  # type: ignore
        OCC_GEOM_AVAILABLE = True
        OCC_FLAVOR = "pythonocc-core"
    except Exception:  # pragma: no cover
        BRepExtrema_DistShapeShape = None  # type: ignore
        BRepAlgoAPI_Common = None  # type: ignore
        TopAbs_ShapeEnum = None  # type: ignore
        GProp_GProps = None  # type: ignore
        BRepGPropMod = None  # type: ignore
        OCC_GEOM_AVAILABLE = False
        OCC_FLAVOR = "none"

from app.assembly.step_loader import load_shape_for_member


def compute_contacts(project: str, assembly_id: str, members: List[Tuple[str, int]], clearance_max_mm: float = 5.0) -> List[Dict[str, str]]:
    """Fallback simple classifier used when OCC is not available.
    Pairs whose clearance exceeds clearance_max_mm are omitted.
    """
    results: List[Dict[str, str]] = []
    n = len(members)
    for i in range(n):
        for j in range(i + 1, n):
            a_part, a_rev = members[i]
            b_part, b_rev = members[j]
            relation = "clearance"
            min_gap = 0.1  # mm
            if relation == "clearance" and min_gap > clearance_max_mm:
                continue
            contact_area = 0.0
            results.append({
                "project": project,
                "assembly_id": assembly_id,
                "a_part": a_part,
                "a_rev": str(a_rev),
                "b_part": b_part,
                "b_rev": str(b_rev),
                "relation": relation,
                "min_gap_mm": f"{min_gap:.6f}",
                "contact_area_mm2": f"{contact_area:.2f}",
                "note": "stub",
            })
    return results


def _call_first_available(calls, shape, props) -> bool:
    """Try a list of callables; return True on first success."""
    for fn in calls:
        try:
            fn(shape, props)
            return True
        except Exception:
            continue
    return False


def _volume_of_shape(shape) -> float:
    if not (OCC_GEOM_AVAILABLE and BRepGPropMod and GProp_GProps):
        return 0.0
    props = GProp_GProps()
    # Build candidate callables across naming variants
    calls = []
    try:
        cls = getattr(BRepGPropMod, 'BRepGProp', None)
    except Exception:
        cls = None
    if hasattr(BRepGPropMod, 'brepgprop_VolumeProperties'):
        calls.append(lambda s, p: BRepGPropMod.brepgprop_VolumeProperties(s, p))
    if hasattr(BRepGPropMod, 'VolumeProperties'):
        calls.append(lambda s, p: BRepGPropMod.VolumeProperties(s, p))
    if hasattr(BRepGPropMod, 'BRepGProp_VolumeProperties'):
        calls.append(lambda s, p: BRepGPropMod.BRepGProp_VolumeProperties(s, p))
    if cls is not None and hasattr(cls, 'VolumeProperties_s'):
        calls.append(lambda s, p: cls.VolumeProperties_s(s, p))
    if cls is not None and hasattr(cls, 'brepgprop_VolumeProperties_s'):
        calls.append(lambda s, p: cls.brepgprop_VolumeProperties_s(s, p))
    if cls is not None and hasattr(cls, 'VolumeProperties'):
        calls.append(lambda s, p: cls.VolumeProperties(s, p))

    ok = _call_first_available(calls, shape, props)
    if not ok:
        return 0.0
    try:
        return float(props.Mass())
    except Exception:
        return 0.0


def _area_of_shape(shape) -> float:
    if not (OCC_GEOM_AVAILABLE and BRepGPropMod and GProp_GProps):
        return 0.0
    props = GProp_GProps()
    calls = []
    try:
        cls = getattr(BRepGPropMod, 'BRepGProp', None)
    except Exception:
        cls = None
    if hasattr(BRepGPropMod, 'brepgprop_SurfaceProperties'):
        calls.append(lambda s, p: BRepGPropMod.brepgprop_SurfaceProperties(s, p))
    if hasattr(BRepGPropMod, 'SurfaceProperties'):
        calls.append(lambda s, p: BRepGPropMod.SurfaceProperties(s, p))
    if hasattr(BRepGPropMod, 'BRepGProp_SurfaceProperties'):
        calls.append(lambda s, p: BRepGPropMod.BRepGProp_SurfaceProperties(s, p))
    if cls is not None and hasattr(cls, 'SurfaceProperties_s'):
        calls.append(lambda s, p: cls.SurfaceProperties_s(s, p))
    if cls is not None and hasattr(cls, 'brepgprop_SurfaceProperties_s'):
        calls.append(lambda s, p: cls.brepgprop_SurfaceProperties_s(s, p))
    if cls is not None and hasattr(cls, 'SurfaceProperties'):
        calls.append(lambda s, p: cls.SurfaceProperties(s, p))

    ok = _call_first_available(calls, shape, props)
    if not ok:
        return 0.0
    try:
        return float(props.Mass())
    except Exception:
        return 0.0


def compute_contacts_occ(project: str, assembly_id: str, members: List[Tuple[str, int]], tolerance_mm: float = 0.002, clearance_max_mm: float = 5.0) -> List[Dict[str, str]]:
    if not OCC_GEOM_AVAILABLE:
        return compute_contacts(project, assembly_id, members, clearance_max_mm=clearance_max_mm)

    shapes: List[Tuple[str, int, object]] = []
    for part, rev in members:
        shape = load_shape_for_member(project, part, rev)
        shapes.append((part, rev, shape))

    results: List[Dict[str, str]] = []
    n = len(shapes)
    VOL_EPS = 1e-6  # mm^3 threshold to consider true solid overlap
    AREA_EPS = 1e-3  # mm^2 threshold to consider meaningful face/edge contact
    for i in range(n):
        for j in range(i + 1, n):
            a_part, a_rev, a_shape = shapes[i]
            b_part, b_rev, b_shape = shapes[j]
            relation = "clearance"
            min_gap = 0.0
            min_gap_str = ""
            area = 0.0
            note = ""
            if a_shape is None or b_shape is None:
                relation = "unknown"
                min_gap_str = ""
                note = "missing shape"
            else:
                try:
                    # Distance first
                    dss = BRepExtrema_DistShapeShape(a_shape, b_shape)
                    dss.Perform()
                    if dss.IsDone():
                        min_gap = float(dss.Value())
                    else:
                        note = "distance not done"
                        min_gap = 0.0

                    # Common intersection
                    common = BRepAlgoAPI_Common(a_shape, b_shape).Shape()
                    if not common.IsNull():
                        vol = _volume_of_shape(common)
                        if vol > VOL_EPS:
                            relation = "penetration"
                            min_gap_str = "N/A"
                            note = "penetration detected; depth is complex and not computed"
                        else:
                            area = _area_of_shape(common)
                            if area > AREA_EPS or abs(min_gap) <= tolerance_mm:
                                relation = "touching"
                                min_gap_str = f"{min_gap:.6f}"
                            else:
                                relation = "clearance"
                                min_gap_str = f"{min_gap:.6f}"
                    else:
                        relation = "touching" if abs(min_gap) <= tolerance_mm else "clearance"
                        min_gap_str = f"{min_gap:.6f}"
                except Exception as e:  # pragma: no cover
                    relation = "error"
                    min_gap_str = ""
                    note = str(e)
            # Apply clearance filter: omit far pairs
            try:
                if relation == "clearance" and float(min_gap_str) > clearance_max_mm:
                    continue
            except Exception:
                pass
            results.append({
                "project": project,
                "assembly_id": assembly_id,
                "a_part": a_part,
                "a_rev": str(a_rev),
                "b_part": b_part,
                "b_rev": str(b_rev),
                "relation": relation,
                "min_gap_mm": min_gap_str,
                "contact_area_mm2": f"{area:.2f}",
                "note": note,
            })
    return results
