import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer

def fine_tune_model():
    """
    This script fine-tunes the Gemma 2B model on a synthetic dataset.
    It requires a machine with a GPU to run in a reasonable amount of time.
    """
    MODEL_NAME = "google/gemma-2b-it"
    DATASET_PATH = "data/processed/finetuning_data.jsonl"
    OUTPUT_DIR = "src/model/fine_tuned_gemma"

    # Load the dataset
    dataset = load_dataset('json', data_files=DATASET_PATH, split='train')

    # Load the tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",
        torch_dtype=torch.bfloat16
    )

    # Tokenize the dataset
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=512)

    tokenized_dataset = dataset.map(tokenize_function, batched=True)

    # Set up the training arguments
    training_arguments = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=1,
        optim="paged_adamw_32bit",
        save_steps=100,
        logging_steps=10,
        learning_rate=2e-4,
        weight_decay=0.001,
        fp16=False,
        bf16=True,
        max_grad_norm=0.3,
        max_steps=-1,
        warmup_ratio=0.03,
        group_by_length=True,
        lr_scheduler_type="constant",
    )

    # Create a Trainer instance
    trainer = Trainer(
        model=model,
        train_dataset=tokenized_dataset,
        args=training_arguments,
        data_collator=lambda data: {'input_ids': torch.stack([f['input_ids'] for f in data]),
                                    'attention_mask': torch.stack([f['attention_mask'] for f in data]),
                                    'labels': torch.stack([f['input_ids'] for f in data])}
    )

    # Start the training
    print("Starting model fine-tuning...")
    trainer.train()
    print("Fine-tuning finished.")

    # Save the trained model
    trainer.save_model(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}")

if __name__ == '__main__':
    fine_tune_model()
