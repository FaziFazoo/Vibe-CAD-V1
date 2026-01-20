# Antigravity Vibe CAD - Run Instructions

## Prerequisites
- Python 3.8+
- [Optional] CATIA V5 installed (for Real execution mode)
- [Optional] HuggingFace API Token (for LLM inference)

## 1. Setup

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment
Create a `.env` file (optional) or set the environment variable for HuggingFace:
```bash
# Windows PowerShell
$env:HF_INFERENCE_TOKEN = "your_hf_token_here"
```
*Note: If no token is provided, the system may hit public rate limits or fail depending on the model availability.*

## 2. Run the Server

To start the FastAPI backend:
```bash
uvicorn src.server:app --reload
```
The server will start at `http://127.0.0.1:8000`.

## 3. Usage

### Compile a Design (API)
You can use `curl` or Postman.

**Request:**
POST `http://127.0.0.1:8000/compile`
```json
{
  "prompt": "Create a cylindrical chamber, radius 50 mm, length 200 mm, axis along Z."
}
```

**Response:**
Returns a JSON D-File.

### Execute a Design (API)
POST `http://127.0.0.1:8000/execute`
```json
{
  "mode": "mock", 
  "d_file": { ... content of d-file ... }
}
```
Set `"mode": "real"` to attempt connection to a local CATIA V5 instance.

## 4. PyCATIA Mapping
The system uses `src/bridge.py` to map JSON features to COM calls.
- `sketch` -> `HybridShapeFactory`
- `pad` -> `ShapeFactory.AddNewPad`
- `pocket` -> `ShapeFactory.AddNewPocket`

See `examples/example_output.json` for the expected data format.
