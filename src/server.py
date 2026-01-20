from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .compiler import CADCompiler
import uvicorn
import os

app = FastAPI(title="Antigravity Vibe CAD API", version="1.0")
compiler = CADCompiler()

class PromptRequest(BaseModel):
    prompt: str

class ExecuteRequest(BaseModel):
    d_file: dict
    mode: str = "mock"

@app.post("/compile")
def compile_prompt(request: PromptRequest):
    result = compiler.compile(request.prompt)
    if "error" in result:
        # We return 200 OK even for business errors (like AMBIGUOUS_INPUT)
        # so the client can handle them gracefully, or 400 if strictly needed.
        # But let's return it as the body.
        return result
    return result

@app.post("/execute")
def execute_design(request: ExecuteRequest):
    result = compiler.run(request.d_file, mode=request.mode)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "Antigravity Vibe CAD"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
