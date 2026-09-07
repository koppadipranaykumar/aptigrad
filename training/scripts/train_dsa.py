import gc
import inspect
from pathlib import Path

import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import (
    LoraConfig,
    prepare_model_for_kbit_training,
)
from trl import (
    SFTConfig,
    SFTTrainer,
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

TRAIN_FILE = (
    ROOT_DIR
    / "training"
    / "training-data"
    / "dsa"
    / "train.jsonl"
)

VALIDATION_FILE = (
    ROOT_DIR
    / "training"
    / "training-data"
    / "dsa"
    / "validation.jsonl"
)

TEST_FILE = (
    ROOT_DIR
    / "training"
    / "training-data"
    / "dsa"
    / "test.jsonl"
)

OUTPUT_DIR = (
    ROOT_DIR
    / "training"
    / "adapters"
    / "dsa"
)

MODEL_NAME = "Qwen/Qwen3-0.6B"


# ============================================================
# GPU CHECK
# ============================================================

if not torch.cuda.is_available():
    raise RuntimeError(
        "CUDA is not available. "
        "PyTorch is not detecting your RTX 3050."
    )

gpu_name = torch.cuda.get_device_name(0)

gpu_memory = (
    torch.cuda.get_device_properties(0).total_memory
    / (1024 ** 3)
)

print("=" * 65)
print("              APTIGRAD — DSA TRAINING")
print("=" * 65)
print(f"GPU        : {gpu_name}")
print(f"VRAM       : {gpu_memory:.2f} GB")
print(f"Base model : {MODEL_NAME}")
print("=" * 65)
print()


# ============================================================
# FILE CHECK
# ============================================================

required_files = [
    TRAIN_FILE,
    VALIDATION_FILE,
    TEST_FILE,
]

for path in required_files:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found:\n{path}"
        )

print("Dataset files:")
print(f"  Train      : {TRAIN_FILE}")
print(f"  Validation : {VALIDATION_FILE}")
print(f"  Test       : {TEST_FILE}")
print()


# ============================================================
# LOAD DATASETS
# ============================================================

print("Loading DSA dataset...")

train_dataset = load_dataset(
    "json",
    data_files=str(TRAIN_FILE),
    split="train",
)

validation_dataset = load_dataset(
    "json",
    data_files=str(VALIDATION_FILE),
    split="train",
)

test_dataset = load_dataset(
    "json",
    data_files=str(TEST_FILE),
    split="train",
)

print(
    f"Training examples   : {len(train_dataset)}"
)

print(
    f"Validation examples : {len(validation_dataset)}"
)

print(
    f"Test examples       : {len(test_dataset)}"
)

print()


# ============================================================
# DATASET VALIDATION
# ============================================================

for name, dataset in [
    ("train", train_dataset),
    ("validation", validation_dataset),
    ("test", test_dataset),
]:
    if "messages" not in dataset.column_names:
        raise ValueError(
            f"{name}.jsonl must contain a 'messages' column."
        )

print("Dataset format check: OK")
print()


# ============================================================
# TOKENIZER
# ============================================================

print("Loading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    use_fast=True,
)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Tokenizer loaded.")
print()


# ============================================================
# 4-BIT QUANTIZATION
# ============================================================

print("Preparing 4-bit quantization...")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

print("4-bit configuration ready.")
print()


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading Qwen3-0.6B in 4-bit...")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map={"": 0},
    dtype=torch.float16,
)

model.config.use_cache = False

print("Preparing model for k-bit training...")

model = prepare_model_for_kbit_training(
    model,
    use_gradient_checkpointing=True,
)

print("Model loaded successfully.")
print()


# ============================================================
# LORA CONFIGURATION
# ============================================================

print("Preparing LoRA configuration...")

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,

    # QLoRA-style target modules
    target_modules="all-linear",

    bias="none",
    task_type="CAUSAL_LM",
)

print("LoRA configuration ready.")
print()


# ============================================================
# TRL VERSION COMPATIBILITY
# ============================================================

sft_parameters = set(
    inspect.signature(
        SFTConfig
    ).parameters.keys()
)

trainer_parameters = set(
    inspect.signature(
        SFTTrainer
    ).parameters.keys()
)

print("Detected SFTConfig parameters.")
print()


# ============================================================
# BUILD TRAINING ARGUMENTS
# ============================================================

training_kwargs = {
    "output_dir": str(OUTPUT_DIR),

    # --------------------------------------------------------
    # FIRST SAFE TRAINING RUN
    # --------------------------------------------------------

    "num_train_epochs": 1,

    # --------------------------------------------------------
    # GPU MEMORY
    # --------------------------------------------------------

    "per_device_train_batch_size": 1,
    "per_device_eval_batch_size": 1,

    "gradient_accumulation_steps": 8,

    "gradient_checkpointing": True,

    # --------------------------------------------------------
    # LEARNING
    # --------------------------------------------------------

    "learning_rate": 1e-4,
    "lr_scheduler_type": "cosine",

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    "logging_steps": 1,

    # --------------------------------------------------------
    # SAVING
    # --------------------------------------------------------

    "save_strategy": "steps",
    "save_steps": 20,
    "save_total_limit": 2,

    # --------------------------------------------------------
    # IMPORTANT:
    # Disable AMP gradient scaling.
    #
    # Your previous error was:
    #
    # _amp_foreach_non_finite_check_and_unscale_cuda
    # not implemented for BFloat16
    #
    # Turning off fp16/bf16 avoids that scaler path.
    # --------------------------------------------------------

    "fp16": False,
    "bf16": False,

    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    "report_to": "none",
}


# ============================================================
# WARMUP COMPATIBILITY
# ============================================================

if "warmup_steps" in sft_parameters:
    training_kwargs["warmup_steps"] = 1

elif "warmup_ratio" in sft_parameters:
    training_kwargs["warmup_ratio"] = 0.05


# ============================================================
# SEQUENCE LENGTH COMPATIBILITY
# ============================================================

if "max_length" in sft_parameters:
    training_kwargs["max_length"] = 512

elif "max_seq_length" in sft_parameters:
    training_kwargs["max_seq_length"] = 512


# ============================================================
# EVALUATION COMPATIBILITY
# ============================================================

if "eval_strategy" in sft_parameters:

    training_kwargs["eval_strategy"] = "steps"

elif "evaluation_strategy" in sft_parameters:

    training_kwargs["evaluation_strategy"] = "steps"


if "eval_steps" in sft_parameters:
    training_kwargs["eval_steps"] = 20


# ============================================================
# PACKING
# ============================================================

if "packing" in sft_parameters:
    training_kwargs["packing"] = False


# ============================================================
# ASSISTANT-ONLY LOSS
# ============================================================

if "assistant_only_loss" in sft_parameters:

    training_kwargs["assistant_only_loss"] = True

    print(
        "Assistant-only loss: ENABLED"
    )

else:

    print(
        "Assistant-only loss: "
        "NOT AVAILABLE in this TRL version"
    )


# ============================================================
# CREATE SFT CONFIG
# ============================================================

print()
print("Creating SFTConfig...")

training_args = SFTConfig(
    **training_kwargs
)

print("SFTConfig created successfully.")
print()


# ============================================================
# CREATE TRAINER ARGUMENTS
# ============================================================

trainer_kwargs = {
    "model": model,
    "args": training_args,
    "train_dataset": train_dataset,
    "eval_dataset": validation_dataset,
    "peft_config": lora_config,
}


# ============================================================
# TOKENIZER / PROCESSING CLASS COMPATIBILITY
# ============================================================

if "processing_class" in trainer_parameters:

    trainer_kwargs[
        "processing_class"
    ] = tokenizer

elif "tokenizer" in trainer_parameters:

    trainer_kwargs[
        "tokenizer"
    ] = tokenizer

else:

    raise RuntimeError(
        "Could not determine how to pass "
        "the tokenizer to SFTTrainer."
    )


# ============================================================
# CREATE TRAINER
# ============================================================

print("Creating SFTTrainer...")

trainer = SFTTrainer(
    **trainer_kwargs
)

print("SFTTrainer created successfully.")
print()


# ============================================================
# MEMORY CLEANUP
# ============================================================

gc.collect()
torch.cuda.empty_cache()


# ============================================================
# START TRAINING
# ============================================================

print("=" * 65)
print("                 STARTING TRAINING")
print("=" * 65)
print()

print("Training on:")
print(
    f"  {len(train_dataset)} training examples"
)

print(
    f"  {len(validation_dataset)} validation examples"
)

print(
    f"  {len(test_dataset)} test examples"
)

print()

trainer.train()


# ============================================================
# SAVE ADAPTER
# ============================================================

print()
print("=" * 65)
print("                 SAVING DSA ADAPTER")
print("=" * 65)
print()

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

trainer.save_model(
    str(OUTPUT_DIR)
)

tokenizer.save_pretrained(
    str(OUTPUT_DIR)
)


# ============================================================
# CLEANUP
# ============================================================

del trainer
del model

gc.collect()
torch.cuda.empty_cache()


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 65)
print("                TRAINING COMPLETE")
print("=" * 65)
print()

print("DSA adapter saved to:")
print(OUTPUT_DIR)

print()
print("Aptigrad DSA training finished successfully.")