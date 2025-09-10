import os
from typing import List, Tuple, Dict

# Placeholder: In a full OCC-enabled environment, compute true distances.


def compute_contacts(project: str, assembly_id: str, members: List[Tuple[str, int]]) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    n = len(members)
    for i in range(n):
        for j in range(i + 1, n):
            a_part, a_rev = members[i]
            b_part, b_rev = members[j]
            # Demo placeholder classification
            relation = "clearance"
            min_gap = 0.1  # mm
            contact_area = 0.0
            results.append({
                "project": project,
                "assembly_id": assembly_id,
                "a_part": a_part,
                "a_rev": str(a_rev),
                "b_part": b_part,
                "b_rev": str(b_rev),
                "relation": relation,
                "min_gap_mm": str(min_gap),
                "contact_area_mm2": str(contact_area),
                "note": "stub",
            })
    return results
