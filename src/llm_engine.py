import os
import json
import requests
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from .prompts import SYSTEM_PROMPT

# Load environment variables from .env file
load_dotenv()

class LLMEngine:
    def __init__(self):
        self.hf_token = os.environ.get("HF_INFERENCE_TOKEN")
        self.ds_key = os.environ.get("DEEPSEEK_API_KEY")
        self.use_local = os.environ.get("USE_LOCAL_LLM")
        
        self.tokenizer = None
        self.model = None

        if self.use_local == "true":
            self.provider = "local"
            # Import here to avoid heavy load if not used
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            model_id = "meta-llama/Llama-3.1-8B-Instruct"
            print(f"LLM Engine: Loading Local Model {model_id}... (This may take time)")
            
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_id, token=self.hf_token)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_id, 
                    token=self.hf_token,
                    device_map="auto",
                    torch_dtype=torch.float16
                )
                print("LLM Engine: Local Model Loaded Successfully.")
            except Exception as e:
                print(f"Failed to load local model: {e}")
                print("Falling back to HuggingFace API strategies.")
                self.provider = "huggingface" # Fallback setup below

        if not self.tokenizer: # If local failed or not requested
            # Determine provider (existing logic)
            if self.ds_key:
                self.provider = "deepseek"
                self.model_id = "deepseek-chat"
                print("LLM Engine: Using DeepSeek API")
            elif self.hf_token:
                self.provider = "huggingface"
                self.model_id = "Qwen/Qwen2.5-7B-Instruct" 
                self.client = InferenceClient(model=self.model_id, token=self.hf_token)
                print(f"LLM Engine: Using HuggingFace API ({self.model_id})")
            else:
                self.provider = "huggingface_public"
                self.model_id = "Qwen/Qwen2.5-7B-Instruct"
                self.client = InferenceClient(model=self.model_id)
                print("WARNING: No API Keys found. Using HuggingFace Public API (Rate limits apply).")

    def generate_d_file(self, user_prompt: str) -> dict:
        if self.provider == "local":
            return self._call_local(user_prompt)
        elif self.provider == "deepseek":
            return self._call_deepseek(user_prompt)
        else:
            return self._call_huggingface(user_prompt)

    def _call_local(self, user_prompt: str) -> dict:
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
            inputs = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(self.model.device)

            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=2048,
                temperature=0.1
            )
            
            # Decode only the new tokens
            response_text = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
            return self._clean_and_parse_json(response_text)

        except Exception as e:
            print(f"Local LLM Error: {e}")
            return {"error": "LLM_FAILURE", "details": str(e)}

    def _call_deepseek(self, user_prompt: str) -> dict:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.ds_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']
            return self._clean_and_parse_json(content)
        except Exception as e:
            print(f"DeepSeek API Failed: {e}")
            print("Falling back to HuggingFace...")
            return self._call_huggingface(user_prompt)

    def _call_huggingface(self, user_prompt: str) -> dict:
        # Ensure client exists (it might not be init if we started in DeepSeek mode)
        if not hasattr(self, 'client') or self.client is None:
            print("Initializing Backup HuggingFace Client...")
            model = "Qwen/Qwen2.5-7B-Instruct"
            token = self.hf_token
            # Handle case where token might be missing? (Though .env has it now)
            self.client = InferenceClient(model=model, token=token)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return self._clean_and_parse_json(content)
            
        except Exception as e:
            print(f"HuggingFace API Error: {e}")
            return {"error": "LLM_FAILURE", "details": str(e)}

    def _clean_and_parse_json(self, content: str) -> dict:
        # Simple cleanup if the model adds markdown code blocks
        clean_content = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_content)
        except json.JSONDecodeError:
            return {"error": "INVALID_JSON_OUTPUT", "content": clean_content}
