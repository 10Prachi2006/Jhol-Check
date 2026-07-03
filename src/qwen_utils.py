import json
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

class ScamAnalyzer:
    # Loading the model and tokenizer from the specified repository --> finetuned model for scam detection form my repo
    def __init__(self, repo_id="PrachiSandipkumar/qwen_scam_high_accuracy"):
        self.tokenizer = AutoTokenizer.from_pretrained(repo_id, trust_remote_code=True)
        
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_enable_fp32_cpu_offload=True
        )
        # Load the base model in 8-bit precision and offload to CPU
        base_model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-3B-Instruct",
            quantization_config=quantization_config,
            device_map={"": "cpu"},
            trust_remote_code=True
        )
        # Load the fine-tuned model using PEFT
        self.model = PeftModel.from_pretrained(base_model, repo_id)
        self.model.eval()

        # Define a method to parse list blocks from the text based on field names and end markers
    def parse_list_block(self, text, field_name, end_markers):
        pattern = rf"{field_name}:\s*\n(.*?)(?:\n(?:{'|'.join(end_markers)}):|$)"
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not m:
            return []
        block = m.group(1).strip()
        if block.lower() == "- none" or not block:
            return []
        return [
            line.lstrip("- ").strip()
            for line in block.split("\n")
            if line.strip().startswith("-") or line.strip().startswith("1.") or line.strip()
        ]
        
        # Define a method to parse the evidence block, extracting text and labels

    def parse_evidence_block(self, text):
        items = self.parse_list_block(text, "Evidence", ["Information Requested", "Reasoning"])
        parsed = []
        for item in items:
            m = re.match(r'"(.+?)"\s*→\s*(.+)', item)
            if m:
                parsed.append({"text": m.group(1), "label": m.group(2).strip()})
            else:
                parsed.append({"text": item, "label": "Suspicious Activity"})
        return parsed

        # Define the main method to analyze the text and extract structured scam analysis

    def analyze_text(self, context_message):
        system_prompt = (
            "You are an expert cybercrime and fraud detection analyst. "
            "Carefully inspect each message and provide structured scam analysis."
        )
        user_prompt = f"Classify this message as scam or legitimate.\n\nMessage:\n{context_message}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = self.tokenizer([text], return_tensors="pt")
        
        with torch.no_grad():
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=300, 
                temperature=0.1,
                do_sample=False
            )

            # Extract the generated text by removing the input prompt from the output
        
        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]
        decoded_batch = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        raw = decoded_batch[0].strip() if decoded_batch else ""
        
        def extract(pattern, text, default=""):
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return m.group(1).strip() if m else default

        scam = extract(r"Scam:\s*(YES|NO)", raw, "NO")
        scam_type = extract(r"Scam Type:\s*(.+?)(?:\n|$)", raw, "Other")
        risk = extract(r"Risk Level:\s*(.+?)(?:\n|$)", raw, "LOW")
        confidence = extract(r"Confidence:\s*(\d+)", raw, "0")
        
        techniques = self.parse_list_block(raw, "Techniques", ["Evidence"])
        evidence = self.parse_evidence_block(raw)
        requested = self.parse_list_block(raw, "Information Requested", ["Reasoning"])
        
        reasoning_block = extract(r"Reasoning:\s*\n(.*?)(?:\nRecommended Action)", raw)
        reasoning = [
            re.sub(r"^\d+\.\s*", "", line).strip()
            for line in reasoning_block.split("\n")
            if line.strip()
        ]
        
        actions = self.parse_list_block(raw, "Recommended Action", ["$"])
        if not actions:
            actions = ["Do not click any links.", "Report immediately via 1930."]

            # Return the structured scam analysis as a dictionary

        return {
            "scam": scam,
            "scam_type": scam_type,
            "risk_level": risk,
            "confidence": int(confidence) if confidence.isdigit() else 90,
            "techniques": techniques,
            "evidence": evidence,
            "requested_information": requested,
            "reasoning": reasoning,
            "recommended_action": actions,
            "raw_output": raw
        }