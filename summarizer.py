import torch
import re

class LLMSummarizer:
    def __init__(self, use_mock=False):
        self.use_mock = use_mock
        if not self.use_mock:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            
            model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
            print(f"Loading {model_id}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                torch_dtype=torch.float16 # saves memory
            )
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=150
            )
            print("Model loaded successfully!")

    def summarize(self, text):
        if self.use_mock:
            return f"[FAKE SUMMARY] This is a fake summary for local testing of: {text[:30]}..."

        # prompt = f"Summarize the following text in 1 or 2 clear sentences. Text: {text}\nSummary:"
        prompt = f"Summarize the following text in exactly two clear, complete sentences.\n\nText: {text}\n\nSummary:"
        
        outputs = self.pipeline(prompt)
        raw_summary = outputs[0]["generated_text"].replace(prompt, "").strip()

        # heuristic: find the last punctuation mark, and cut everything after it
        match = re.search(r'.*[.!?]', raw_summary, flags=re.DOTALL)
        if match:
            clean_summary = match.group(0)
        else:
            clean_summary = raw_summary + "." # if no punctuation exists
        
        return clean_summary