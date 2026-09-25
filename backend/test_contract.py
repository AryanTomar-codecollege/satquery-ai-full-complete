from app.services.geospatial import boxes_overlap
from app.services.agent import select_task

assert boxes_overlap(
    {"left": 0, "bottom": 0, "right": 10, "top": 10},
    {"left": 5, "bottom": 5, "right": 15, "top": 15},
)
assert not boxes_overlap(
    {"left": 0, "bottom": 0, "right": 10, "top": 10},
    {"left": 20, "bottom": 20, "right": 30, "top": 30},
)
assert select_task(
    "What changed between these images?",
    "auto",
    [{"filename": "a.tif"}, {"filename": "b.tif"}],
) == "change_detection"
assert select_task("Locate the buildings", "auto", [{"filename": "a.tif"}]) == "grounding"
assert select_task("Show the CRS", "metadata", [{"filename": "a.tif"}]) == "metadata"
print("Contract checks passed.")
