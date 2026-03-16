import torch
import re
import gc # Garbage Collector for memory management

class LLMSummarizer:
    def __init__(self, model_id="Qwen/Qwen2.5-1.5B-Instruct", use_mock=False):
        self.use_mock = use_mock
        self.current_model_id = model_id
        self.pipeline = None
        
        if not self.use_mock:
            self.load_model(model_id)

    def load_model(self, model_id):
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        
        # clean up old model to save VRAM
        if self.pipeline is not None:
            del self.pipeline
            del self.model
            del self.tokenizer
            gc.collect()
            torch.cuda.empty_cache()
            
        print(f"Loading model: {model_id}...")
        self.current_model_id = model_id
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True # required for newer models
            )
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=150
            )
            return f"Successfully loaded {model_id}"
        except Exception as e:
            return f"Error loading model: {str(e)}"

    def summarize(self, text):
        if self.use_mock:
            return f"[FAKE SUMMARY] This is a fake summary for local testing of: {text[:30]}..."

        # prompt = f"Summarize the following text in 1 or 2 clear sentences. Text: {text}\nSummary:"
        prompt = f"Summarize the following content in exactly two clear, complete sentences.\n\nText: {text}\n\nSummary:"
        
        outputs = self.pipeline(prompt)
        raw_summary = outputs[0]["generated_text"].replace(prompt, "").strip()

        # heuristic: find the last punctuation mark, and cut everything after it
        match = re.search(r'.*[.!?]', raw_summary, flags=re.DOTALL)
        if match:
            clean_summary = match.group(0)
        else:
            clean_summary = raw_summary + "." # if no punctuation exists
        
        return clean_summary