import os
from pathlib import Path
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Path Configuration
BASE_DIR = Path(__file__).resolve().parent
dataset_file = str(BASE_DIR / "dataset.jsonl")
output_model_dir = str(BASE_DIR / "outputs")
export_gguf_path = str(BASE_DIR / "aptigrad_model")

# Safe sequence length for 4GB VRAM GPU
max_seq_length = 1024

def format_prompts(batch, tokenizer):
    texts = []
    for messages in batch["messages"]:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        texts.append(text)
    return {"text": texts}


if __name__ == "__main__":
    print("Loading base Llama-3.2-3B-Instruct model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Llama-3.2-3B-Instruct",
        max_seq_length=max_seq_length,
        load_in_4bit=True
    )

    # 2. Add QLoRA Adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
    )

    # Enable VRAM memory optimization
    model.gradient_checkpointing_enable()

    # 3. Load & Shuffle Dataset
    print(f"Loading dataset from: {dataset_file}")
    dataset = load_dataset("json", data_files={"train": dataset_file}, split="train")

    print("Shuffling 54,482 dataset entries to ensure balanced topic distribution...")
    dataset = dataset.shuffle(seed=42)

    print("Formatting prompts...")
    dataset = dataset.map(
        lambda batch: format_prompts(batch, tokenizer), 
        batched=True,
        num_proc=None
    )

    # 4. Trainer Configuration (Optimized for 4GB GPU VRAM)
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=None,
        args=TrainingArguments(
            per_device_train_batch_size=1,        # Fits 4GB VRAM
            gradient_accumulation_steps=8,         # Effective batch size = 8
            num_train_epochs=1,                    # Trains across all 54.4k entries once
            learning_rate=2e-4,
            lr_scheduler_type="cosine",            # Smooth decay prevents repetitive string collapse
            warmup_ratio=0.03,                     # Prevents early gradient spikes
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            output_dir=output_model_dir,
            optim="adamw_8bit",                    # 8-bit Adam optimizer saves ~1GB VRAM
        ),
    )

    print("Starting Fine-Tuning Execution...")
    trainer.train()

    print("Exporting Fine-Tuned Weights to GGUF format...")
    model.save_pretrained_gguf(export_gguf_path, tokenizer, quantization_method="q4_k_m")
    print(f"Export Complete! GGUF saved in: {export_gguf_path}")