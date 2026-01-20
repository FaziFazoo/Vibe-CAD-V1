from .llm_engine import LLMEngine
from .custom_types import DFile, ErrorResponse
from .bridge import CatiaBridge
import json
from pydantic import ValidationError

class CADCompiler:
    def __init__(self):
        self.llm = LLMEngine()
        self.bridge = CatiaBridge(mode="mock")  # Default to mock for safety

    def normalize_prompt(self, raw_prompt: str) -> str:
        # Simple cleanup
        return raw_prompt.strip()

    def compile(self, raw_prompt: str) -> dict:
        """
        Returns a dict. Can be a valid D-File or an error dict.
        """
        clean_prompt = self.normalize_prompt(raw_prompt)
        
        print(f"Compiling prompt: {clean_prompt}")
        
        raw_result = self.llm.generate_d_file(clean_prompt)
        
        # Check if LLM returned a known error structure
        if "error" in raw_result:
            return raw_result
            
        # Validate against DFile schema
        try:
            d_file = DFile(**raw_result)
            return d_file.dict()
        except ValidationError as e:
            return {
                "error": "SCHEMA_VALIDATION_FAILED",
                "details": e.errors(),
                "raw_output": raw_result
            }

    def run(self, d_file_dict: dict, mode: str = "mock"):
        """
        Executes the D-File dict.
        """
        try:
            d_file = DFile(**d_file_dict)
            self.bridge.mode = mode
            if mode == "real":
                 # Re-init attempt for real connection if needed
                 self.bridge = CatiaBridge(mode="real")
            
            logs = self.bridge.execute(d_file)
            
            # Check for errors in logs
            errors = [l for l in logs if "Error" in str(l) or "Skipped" in str(l)]
            status = "success" if not errors else "completed_with_errors"
            
            return {
                "status": status, 
                "mode": mode,
                "logs": logs,
                "errors": errors
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
