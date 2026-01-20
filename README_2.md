# Vibe CAD (PyCATIA Edition)

## 1. Objective

Build an AI-driven **Vibe CAD** system that converts **natural language engineering design prompts** into **structured, machine-readable CAD parameters** executable via **PyCATIA** in **CATIA V5**.

Scope deliberately excludes:

* Physics validation
* Feasibility checks
* Manufacturing checks

The system focuses purely on **intent → parametric geometry extraction**.

---

## 2. High-Level Architecture

```
User Prompt
   ↓
Prompt Preprocessor
   ↓
LLM (HuggingFace – Free Model)
   ↓
Structured CAD Parameter Extractor (JSON)
   ↓
PyCATIA Execution Layer
   ↓
CATIA V5 Parametric Model
```

---

## 3. Core Design Philosophy

* Treat **CAD as a programming language**
* Geometry = Functions + Parameters
* No explanations, only intent preservation
* Deterministic output schema
* Fully parametric & editable

---

## 4. LLM Selection (Free / HuggingFace)

### Recommended Models (Free Tier Compatible)

| Model               | Why                          | Notes                     |
| ------------------- | ---------------------------- | ------------------------- |
| Mistral-7B-Instruct | Strong instruction following | Best default              |
| Mixtral-8x7B        | Better reasoning             | Heavy, needs quantization |
| Qwen2.5-7B-Instruct | Very good structured output  | Highly recommended        |
| LLaMA-3-8B-Instruct | Clean JSON outputs           | Needs HF access approval  |

**Minimum Requirement:**

* Must support instruction-following
* Must reliably output JSON

---

## 5. Prompt Engineering Contract (Critical)

The LLM is **NOT a chat assistant**.
It behaves as a **CAD Compiler**.

### System Prompt (Core)

```
You are a CAD automation compiler.
Input: Natural language engineering design.
Output: Structured CAD parameters only.
No explanations.
No validation.
Assume CATIA V5.
All geometry is parametric.
```

---

## 6. Canonical Output Schema (D-File Schema)

This is the **D-File** (Design File) your system operates on.

```json
{
  "meta": {
    "cad_system": "CATIA_V5",
    "units": "mm",
    "design_mode": "parametric"
  },
  "part": {
    "name": "",
    "origin": [0, 0, 0],
    "axis_system": "default"
  },
  "reference_geometry": {
    "planes": ["XY", "YZ", "ZX"],
    "axes": ["X", "Y", "Z"]
  },
  "features": [
    {
      "id": "",
      "type": "",
      "sketch_plane": "",
      "parameters": {}
    }
  ],
  "relations": [],
  "constraints": [],
  "update_order": []
}
```

---

## 7. Supported Feature Types (Initial MVP)

### Sketch-Based

* line
* circle
* arc
* spline
* rectangle

### Solid Features

* pad
* pocket
* shaft
* groove
* rib

### Reference

* plane_offset
* axis
* point

---

## 8. Example: Natural Language → D-File

### Input Prompt

> Create a cylindrical chamber, radius 50 mm, length 200 mm, axis along Z.

### Output D-File

```json
{
  "meta": {
    "cad_system": "CATIA_V5",
    "units": "mm",
    "design_mode": "parametric"
  },
  "part": {
    "name": "cylindrical_chamber",
    "origin": [0, 0, 0],
    "axis_system": "default"
  },
  "features": [
    {
      "id": "sketch_1",
      "type": "sketch",
      "sketch_plane": "XY",
      "parameters": {
        "circle": {
          "center": [0, 0],
          "radius": 50
        }
      }
    },
    {
      "id": "pad_1",
      "type": "pad",
      "sketch": "sketch_1",
      "parameters": {
        "length": 200,
        "direction": "Z"
      }
    }
  ]
}
```

---

## 9. PyCATIA Execution Layer (Mapping Logic)

Each feature maps **1:1** to PyCATIA calls.

| D-File Feature | PyCATIA Object            |
| -------------- | ------------------------- |
| sketch         | HybridShapeFactory        |
| pad            | ShapeFactory.AddNewPad    |
| pocket         | ShapeFactory.AddNewPocket |
| shaft          | ShapeFactory.AddNewShaft  |

Execution order strictly follows `update_order` or feature sequence.

---

## 10. Error Handling Strategy

### Ambiguous Prompt

LLM must respond with:

```json
{
  "error": "AMBIGUOUS_INPUT",
  "missing_parameters": []
}
```

### Invalid Geometry (Ignored)

System **does not care**.
Execution layer handles failures.

---

## 11. Deployment Strategy (Zero Cost Path)

* LLM: HuggingFace Inference (free tier / local)
* Backend: Python + FastAPI
* CAD Bridge: PyCATIA (local machine)
* UI: Simple web input or CLI

---

## 12. Roadmap (  Edition)

Phase 1: Text → Parametric Solids
Phase 2: Assemblies
Phase 3: Constraints & Relations
Phase 4: Design Variants
Phase 5: Voice → CAD

---

## 13. What Makes This " "

* No manual sketching
* No UI dependency
* Design by intent, not clicks
* CAD becomes programmable

