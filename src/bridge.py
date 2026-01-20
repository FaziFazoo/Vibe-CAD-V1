from .custom_types import DFile, Feature
import traceback

class CatiaBridge:
    def __init__(self, mode: str = "mock"):
        self.mode = mode
        self.catia = None
        self.part = None
        self.hsf = None # HybridShapeFactory
        self.sf = None  # ShapeFactory (Solid)
        
        if self.mode == "real":
            try:
                from pycatia import catia
                from pycatia.mec_mod_interfaces.part import Part
                self.catia = catia()
                # Assuming user has an active document or we create one
                self.document = self.catia.active_document
                self.part = self.document.part
                self.hsf = self.part.hybrid_shape_factory
                self.sf = self.part.shape_factory
            except ImportError:
                print("PyCATIA not found. Falling back to Mock mode.")
                self.mode = "mock"
            except Exception as e:
                print(f"CATIA connection failed: {e}. Falling back to Mock mode.")
                self.mode = "mock"

    def execute(self, d_file: DFile):
        print(f"--- Executing D-File: {d_file.part.name} [{self.mode.upper()}] ---")
        
        ordered_features = d_file.features
        if d_file.update_order:
             feature_map = {f.id: f for f in d_file.features}
             ordered_features = [feature_map[fid] for fid in d_file.update_order if fid in feature_map]

        execution_log = []
        for feature in ordered_features:
            result = self.execute_feature(feature)
            if result:
                execution_log.append(result)
            
        if self.mode == "real":
            self.part.update()
        
        return execution_log

    def execute_feature(self, feature: Feature):
        if self.mode == "mock":
            print(f"[MOCK] Executing Feature: {feature.type} (ID: {feature.id}) Params: {feature.parameters}")
            return None

        # REAL IMPLEMENTATION STUBS
        try:
            if feature.type == "sketch":
                self._create_sketch(feature)
            elif feature.type == "pad":
                self._create_pad(feature)
            elif feature.type == "pocket":
                self._create_pocket(feature)
            elif feature.type == "plane_offset":
                self._create_plane_offset(feature)
            else:
                print(f"Warning: Feature type {feature.type} not ready for real execution.")
                return f"Skipped {feature.id} (not implemented)"
        except Exception as e:
            msg = f"Error executing feature {feature.id}: {e}"
            print(msg)
            traceback.print_exc()
            return msg
        return None

    def _create_sketch(self, feature: Feature):
        try:
            # 1. Resolve Sketch Plane
            # For MVP, simple mapping of strings to absolute planes
            plane_name = feature.sketch_plane
            reference = None
            
            origin_elements = self.part.origin_elements
            if plane_name == "XY":
                reference = origin_elements.plane_xy
            elif plane_name == "YZ":
                reference = origin_elements.plane_yz
            elif plane_name == "ZX":
                reference = origin_elements.plane_zx
            else:
                # Try to find by name (advanced)
                pass

            if not reference:
                print(f"Error: Could not resolve plane {plane_name}")
                return

            # 2. Create Sketch in Main Body (Better for Pads)
            main_body = self.part.main_body
            sketches = main_body.sketches
            sketch = sketches.add(reference)
            sketch.name = feature.id
            
            # 3. Open Edition
            factory_2d = sketch.factory_2d
            sketch.open_edition()
            
            # 4. Draw Geometry
            params = feature.parameters
            
            if "circle" in params and params["circle"]:
                c_params = params["circle"]
                # JSON is [x, y], CATIA needs separate args
                # CreateCircle(CenterX, CenterY, Radius, StartAngle, EndAngle)
                # Note: PyCATIA usually wraps these. 
                # Raw COM check: Factory2D.CreateCircle(x, y, r, 0, 0) -> Circle2D
                # But we might need to cast input to float
                cx, cy = float(c_params["center"][0]), float(c_params["center"][1])
                radius = float(c_params["radius"])
                circle = factory_2d.create_circle(cx, cy, radius, 0, 6.2831853)
                # circle.center_point = ... (automatic in create)
                
            if "line" in params and params["line"]:
                l_params = params["line"]
                p1 = l_params["start"]
                p2 = l_params["end"]
                factory_2d.create_line(float(p1[0]), float(p1[1]), float(p2[0]), float(p2[1]))
                
            if "rectangle" in params and params["rectangle"]:
                r = params["rectangle"]
                # Support Center + Width + Height
                if "center" in r and "width" in r and "height" in r:
                    cx, cy = float(r["center"][0]), float(r["center"][1])
                    w, h = float(r["width"]), float(r["height"])
                    
                    x_min = cx - w/2
                    x_max = cx + w/2
                    y_min = cy - h/2
                    y_max = cy + h/2
                    
                    # p1(bl) -> p2(br) -> p3(tr) -> p4(tl)
                    # Line 1: Bottom
                    factory_2d.create_line(x_min, y_min, x_max, y_min)
                    # Line 2: Right
                    factory_2d.create_line(x_max, y_min, x_max, y_max)
                    # Line 3: Top
                    factory_2d.create_line(x_max, y_max, x_min, y_max)
                    # Line 4: Left
                    factory_2d.create_line(x_min, y_max, x_min, y_min)
                
                # Support Corner1 + Corner2
                elif "corner1" in r and "corner2" in r:
                    # Implement if needed, but LLM usually prefers center/width
                    pass

            # 5. Close Edition
            sketch.close_edition()
            self.part.update()
            print(f"Created Sketch: {feature.id}")

        except Exception as e:
            print(f"Failed to create sketch: {e}")
            traceback.print_exc()
            raise e

    def _create_pad(self, feature: Feature):
        try:
            # 1. Find Profile (Sketch)
            sketch_id = feature.sketch
            
            target_sketch = None
            try:
                # Search in Main Body Sketches
                main_body = self.part.main_body
                target_sketch = main_body.sketches.item(sketch_id)
            except:
                print(f"Could not find sketch {sketch_id} in Main Body")
                return

            # 2. PROPER REFERENCE CREATION
            # "Pad" requires a Reference to the Profile? 
            # Logic Update: AddNewPad expects Sketch object if in MainBody.
            # sketch_ref = self.part.create_reference_from_object(target_sketch)
            
            # 3. Create Pad using ShapeFactory
            pad = self.sf.add_new_pad(target_sketch, float(feature.parameters["length"]))
            
            # 3b. Direction (Optional)
            if "direction" in feature.parameters and feature.parameters["direction"] != "Z":
                # For basic pads, direction is usually normal to sketch.
                # Custom direction requires another reference (line/plane).
                pass
            
            pad.name = feature.id
            self.part.update()
            print(f"Created Pad: {feature.id}")

        except Exception as e:
            print(f"Failed to create pad: {e}")
            traceback.print_exc()
            raise e

    def _create_pocket(self, feature: Feature):
        pass

    def _create_plane_offset(self, feature: Feature):
        pass
