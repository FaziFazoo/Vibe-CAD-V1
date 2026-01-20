from typing import List, Literal, Optional, Union, Dict, Any
from pydantic import BaseModel, Field

# --- Sub-models for Parameters ---

class Point2D(BaseModel):
    center: List[float] = Field(..., min_items=2, max_items=2, description="[x, y] coordinates")
    
class Point3D(BaseModel):
    coordinates: List[float] = Field(..., min_items=3, max_items=3, description="[x, y, z] coordinates")

class CircleParams(BaseModel):
    center: List[float] = Field(..., min_items=2, max_items=2)
    radius: float

class LineParams(BaseModel):
    start: List[float] = Field(..., min_items=2, max_items=2)
    end: List[float] = Field(..., min_items=2, max_items=2)

class RectangleParams(BaseModel):
    center: List[float] = Field(None, min_items=2, max_items=2)
    corner1: List[float] = Field(None, min_items=2, max_items=2)
    corner2: List[float] = Field(None, min_items=2, max_items=2)
    width: Optional[float] = None
    height: Optional[float] = None

class SketchParameters(BaseModel):
    # Flattened sketch entities. Keys like "circle", "line", etc.
    # We use Dict[str, Any] broadly here because sketch content can be mixed,
    # but specific types are preferred.
    circle: Optional[CircleParams] = None
    line: Optional[LineParams] = None
    rectangle: Optional[RectangleParams] = None
    # Add other sketch primitives as needed

class SolidParams(BaseModel):
    length: Optional[float] = None
    depth: Optional[float] = None # Alternative to length
    direction: Optional[str] = "Z" # Default direction

class PlaneParams(BaseModel):
    reference: str
    offset: float

# --- Feature Models ---

class Feature(BaseModel):
    id: str
    type: Literal[
        "sketch", 
        "pad", "pocket", "shaft", "groove", "rib", 
        "plane_offset", "axis", "point"
    ]
    # Sketch-specific fields
    sketch_plane: Optional[str] = None
    
    # Solid-specific fields
    sketch: Optional[str] = None # Reference to a sketch feature ID
    
    # Generic bucket for parameters, refined by type in logic if needed
    # but we can also use specific models if we want strict validation per type
    parameters: Dict[str, Any] 

# --- Meta and Part Models ---

class MetaInfo(BaseModel):
    cad_system: Literal["CATIA_V5"] = "CATIA_V5"
    units: Literal["mm", "in"] = "mm"
    design_mode: Literal["parametric"] = "parametric"

class PartInfo(BaseModel):
    name: str = "Part1"
    origin: List[float] = [0, 0, 0]
    axis_system: str = "default"

class ReferenceGeometry(BaseModel):
    planes: List[str] = ["XY", "YZ", "ZX"]
    axes: List[str] = ["X", "Y", "Z"]

class DFile(BaseModel):
    meta: MetaInfo
    part: PartInfo
    reference_geometry: ReferenceGeometry = ReferenceGeometry()
    features: List[Feature]
    relations: List[Any] = []
    constraints: List[Any] = []
    update_order: List[str] = []

class ErrorResponse(BaseModel):
    error: Literal["AMBIGUOUS_INPUT"]
    missing_parameters: List[str]
