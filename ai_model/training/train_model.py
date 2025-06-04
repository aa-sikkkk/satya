"""
NEBedu Multi-Task Model Training Script

This script handles the training and fine-tuning of models for the NEBedu learning system.
It supports:
- Extractive Question Answering (QnA)
- Hint Generation (generative)
- Step Recommendation (classification)

It is designed for efficient training and is extensible for future learning tasks.
"""

import os
import json
import torch
import logging
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForQuestionAnswering,
    DistilBertForSequenceClassification,
    T5Tokenizer,
    T5ForConditionalGeneration,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from datasets import Dataset, DatasetDict
import numpy as np
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NEBeduMultiTaskTrainer:
    """
    Handles training for QnA, hint generation, and step recommendation.
    - QnA: DistilBERT extractive QA
    - Hint Generation: T5-small generative model
    - Step Recommendation: DistilBERT classification head
    """
    def __init__(self, qna_model_name="distilbert-base-uncased", t5_model_name="t5-small", output_dir="models/neb_edu"):
        self.qna_model_name = qna_model_name
        self.t5_model_name = t5_model_name
        self.output_dir = output_dir
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # QnA
        self.qna_tokenizer = DistilBertTokenizerFast.from_pretrained(qna_model_name)
        self.qna_model = DistilBertForQuestionAnswering.from_pretrained(qna_model_name).to(self.device)
        # Hint Generation
        self.t5_tokenizer = T5Tokenizer.from_pretrained(t5_model_name)
        self.t5_model = T5ForConditionalGeneration.from_pretrained(t5_model_name).to(self.device)
        # Step Recommendation (optional, for future use)
        self.step_model = DistilBertForSequenceClassification.from_pretrained(qna_model_name, num_labels=10).to(self.device)  # num_labels can be set as needed

    def prepare_qna_dataset(self, content_dir: str) -> Dataset:
        """
        Prepare dataset for extractive QnA.
        """
        logger.info("Preparing QnA dataset...")
        training_data = []
        for root, _, files in os.walk(content_dir):
            for file in files:
                if file.endswith('.json'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        content = json.load(f)
                        training_data.extend(self._extract_qa_pairs(content))
        dataset = Dataset.from_dict({
            'question': [item['question'] for item in training_data],
            'context': [item['context'] for item in training_data],
            'answer': [item['answer'] for item in training_data]
        })
        def add_token_positions(examples):
            tokenized_examples = self.qna_tokenizer(
                examples['question'],
                examples['context'],
                truncation=True,
                max_length=512,
                padding='max_length',
                return_offsets_mapping=True
            )
            start_positions = []
            end_positions = []
            for i, offsets in enumerate(tokenized_examples['offset_mapping']):
                answer = examples['answer'][i]
                context = examples['context'][i]
                answer_start = context.find(answer)
                answer_end = answer_start + len(answer)
                start_idx = end_idx = None
                for idx, (start, end) in enumerate(offsets):
                    if start <= answer_start < end:
                        start_idx = idx
                    if start < answer_end <= end:
                        end_idx = idx
                if start_idx is None:
                    start_idx = 0
                if end_idx is None:
                    end_idx = 0
                start_positions.append(start_idx)
                end_positions.append(end_idx)
            tokenized_examples['start_positions'] = start_positions
            tokenized_examples['end_positions'] = end_positions
            tokenized_examples.pop('offset_mapping')
            return tokenized_examples
        tokenized_dataset = dataset.map(
            add_token_positions,
            batched=True,
            remove_columns=dataset.column_names
        )
        return tokenized_dataset

    def prepare_hint_dataset(self, content_dir: str) -> Dataset:
        """
        Prepare dataset for hint generation (T5-style: input = question + context, target = hint).
        """
        logger.info("Preparing hint generation dataset...")
        data = {'input_text': [], 'target_text': []}
        for root, _, files in os.walk(content_dir):
            for file in files:
                if file.endswith('.json'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        content = json.load(f)
                        for topic in content.get('topics', []):
                            for subtopic in topic.get('subtopics', []):
                                for concept in subtopic.get('concepts', []):
                                    context = concept.get('summary', '')
                                    for question in concept.get('questions', []):
                                        if (
                                            isinstance(question, dict)
                                            and 'question' in question
                                            and 'hints' in question
                                            and question['hints']
                                        ):
                                            data['input_text'].append(f"hint: {question['question']} context: {context}")
                                            data['target_text'].append(question['hints'][0])
        dataset = Dataset.from_dict(data)
        def preprocess_t5(examples):
            model_inputs = self.t5_tokenizer(
                examples['input_text'],
                max_length=128,
                truncation=True,
                padding='max_length'
            )
            labels = self.t5_tokenizer(
                examples['target_text'],
                max_length=32,
                truncation=True,
                padding='max_length'
            )['input_ids']
            model_inputs['labels'] = labels
            return model_inputs
        return dataset.map(preprocess_t5, batched=True, remove_columns=dataset.column_names)

    def _extract_qa_pairs(self, content: dict) -> list:
        """
        Extract question-answer pairs from content.
        """
        qa_pairs = []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    for topic in item.get('topics', []):
                        for subtopic in topic.get('subtopics', []):
                            for concept in subtopic.get('concepts', []):
                                context = concept.get('summary', '')
                                for question in concept.get('questions', []):
                                    if (
                                        isinstance(question, dict)
                                        and 'question' in question
                                        and 'acceptable_answers' in question
                                        and question['acceptable_answers']
                                    ):
                                        qa_pairs.append({
                                            'question': question['question'],
                                            'context': context,
                                            'answer': question['acceptable_answers'][0]
                                        })
        else:
            for topic in content.get('topics', []):
                for subtopic in topic.get('subtopics', []):
                    for concept in subtopic.get('concepts', []):
                        context = concept.get('summary', '')
                        for question in concept.get('questions', []):
                            if (
                                isinstance(question, dict)
                                and 'question' in question
                                and 'acceptable_answers' in question
                                and question['acceptable_answers']
                            ):
                                qa_pairs.append({
                                    'question': question['question'],
                                    'context': context,
                                    'answer': question['acceptable_answers'][0]
                                })
        return qa_pairs

    def train_qna(self, dataset: Dataset, epochs: int = 3, batch_size: int = 8):
        """
        Train the QnA model (DistilBERT extractive QA).
        """
        logger.info("Training QnA model...")
        training_args = TrainingArguments(
            output_dir=os.path.join(self.output_dir, 'qna'),
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            save_steps=1000,
            save_total_limit=2,
            logging_steps=100,
            learning_rate=2e-5,
            weight_decay=0.01,
            warmup_steps=500
        )
        trainer = Trainer(
            model=self.qna_model,
            args=training_args,
            train_dataset=dataset,
            data_collator=DataCollatorWithPadding(self.qna_tokenizer)
        )
        trainer.train()
        self.qna_model.save_pretrained(os.path.join(self.output_dir, 'qna'))
        self.qna_tokenizer.save_pretrained(os.path.join(self.output_dir, 'qna'))
        logger.info("QnA model training complete.")

    def train_hint(self, dataset: Dataset, epochs: int = 3, batch_size: int = 8):
        """
        Train the hint generation model (T5-small).
        """
        logger.info("Training hint generation model...")
        training_args = TrainingArguments(
            output_dir=os.path.join(self.output_dir, 'hint'),
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            save_steps=1000,
            save_total_limit=2,
            logging_steps=100,
            learning_rate=3e-4,
            weight_decay=0.01,
            warmup_steps=500
        )
        trainer = Trainer(
            model=self.t5_model,
            args=training_args,
            train_dataset=dataset,
            data_collator=DataCollatorWithPadding(self.t5_tokenizer)
        )
        trainer.train()
        self.t5_model.save_pretrained(os.path.join(self.output_dir, 'hint'))
        self.t5_tokenizer.save_pretrained(os.path.join(self.output_dir, 'hint'))
        logger.info("Hint generation model training complete.")

    # Placeholder for step recommendation training (future)
    # def train_step_recommendation(self, ...):
    #     pass

def main():
    """Main training function."""
    import argparse
    parser = argparse.ArgumentParser(description="Train NEBedu multi-task models")
    parser.add_argument(
        "--content-dir",
        type=str,
        required=True,
        help="Directory containing content files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/neb_edu",
        help="Directory to save trained models"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Training batch size"
    )
    
    args = parser.parse_args()
    
    try:
        os.makedirs(args.output_dir, exist_ok=True)
        trainer = NEBeduMultiTaskTrainer(output_dir=args.output_dir)
        
        # QnA
        qna_dataset = trainer.prepare_qna_dataset(args.content_dir)
        trainer.train_qna(qna_dataset, epochs=args.epochs, batch_size=args.batch_size)
        
        # Hint Generation
        hint_dataset = trainer.prepare_hint_dataset(args.content_dir)
        trainer.train_hint(hint_dataset, epochs=args.epochs, batch_size=args.batch_size)
        
        logger.info("All training complete!")
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 