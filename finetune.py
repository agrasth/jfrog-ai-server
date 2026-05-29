#!/usr/bin/env python3
"""Fine-tune Llama 3 8B on JFrog Q&A pairs using Unsloth + LoRA.

Requires: GPU with 16GB+ VRAM. Run: python finetune.py
Output:   models/jfrog-llama3-finetuned-q4.gguf  (~4.7 GB)
Deploy:   cp models/jfrog-llama3-finetuned-q4.gguf models/llama3-8b-q4.gguf && restart server
"""
import json
import os
from datasets import Dataset


def _load_pairs(jsonl_path: str) -> Dataset:
    pairs = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return Dataset.from_list(pairs)


def _format_prompt(example: dict) -> dict:
    return {"text": (
        f"### Instruction:\n{example['instruction']}\n\n"
        f"### Response:\n{example['output']}"
    )}


def run(
    pairs_path: str = "../jfrog-ai-indexer/output/training_pairs.jsonl",
    output_gguf: str = "models/jfrog-llama3-finetuned-q4.gguf",
    base_model: str = "unsloth/Meta-Llama-3-8B-Instruct",
    epochs: int = 3,
) -> str:
    from unsloth import FastLanguageModel
    from trl import SFTTrainer, SFTConfig

    print(f"Loading base model: {base_model}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=2048,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0,
        bias="none",
    )

    print(f"Loading training pairs from {pairs_path}")
    dataset = _load_pairs(pairs_path).map(_format_prompt)
    print(f"Training on {len(dataset)} examples for {epochs} epochs")

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        args=SFTConfig(
            output_dir="models/checkpoints",
            num_train_epochs=epochs,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            logging_steps=50,
            save_steps=500,
            warmup_ratio=0.03,
            fp16=True,
        ),
    )
    trainer.train()

    os.makedirs("models", exist_ok=True)
    model.save_pretrained_gguf(output_gguf, tokenizer, quantization_method="q4_k_m")
    print(f"\nFine-tuned model saved to: {output_gguf}")
    return output_gguf


if __name__ == "__main__":
    run()
