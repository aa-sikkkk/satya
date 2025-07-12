"""
NEBedu Multi-Task Model Training Script

This script handles the training and fine-tuning of models for the NEBedu learning system.
It supports:
- Extractive Question Answering (QnA)
- Hint Generation (generative)
- Step Recommendation (classification)

It is designed for efficient training and is extensible for future learning tasks.
"""

!pip install onnx onnxruntime optimum[onnxruntime]
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
import torch.onnx
try:
    from onnxruntime.quantization import quantize_dynamic, QuantType
    import onnx
except ImportError:
    quantize_dynamic = None
    QuantType = None
    onnx = None
try:
    from optimum.onnxruntime import ORTModelForSeq2SeqLM
    from optimum.exporters.onnx import main_export
    optimum_available = True
except ImportError:
    optimum_available = False
import shutil

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
    def __init__(self, qna_model_name="distilbert-base-uncased", t5_model_name="t5-small", output_dir="ai_model/exported_model"):
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

    def export_qna_to_onnx(self, save_dir):
        """
        Export the trained QnA model (DistilBERT) to ONNX and quantize it for CPU inference.
        """
        logger.info("Exporting QnA model to ONNX...")
        dummy_question = "What is Nepal?"
        dummy_context = "Nepal is a country in South Asia."
        inputs = self.qna_tokenizer(dummy_question, dummy_context, return_tensors="pt", max_length=128, truncation=True)
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]
        model = self.qna_model.cpu()
        onnx_path = os.path.join(save_dir, "qna.onnx")
        torch.onnx.export(
            model,
            (input_ids, attention_mask),
            onnx_path,
            input_names=["input_ids", "attention_mask"],
            output_names=["start_logits", "end_logits"],
            dynamic_axes={"input_ids": {0: "batch_size", 1: "sequence"}, "attention_mask": {0: "batch_size", 1: "sequence"}},
            opset_version=14
        )
        logger.info(f"QnA model exported to {onnx_path}")
        # Quantize ONNX
        if quantize_dynamic and QuantType:
            quant_path = os.path.join(save_dir, "qna_quantized.onnx")
            quantize_dynamic(onnx_path, quant_path, weight_type=QuantType.QInt8)
            logger.info(f"QnA quantized ONNX model saved to {quant_path}")
        else:
            logger.warning("onnxruntime.quantization not available; skipping quantization.")

    def export_hint_to_onnx(self, save_dir):
        """
        Export the trained T5 model (hint generation) to ONNX and quantize it for CPU inference.
        Uses Hugging Face Optimum for proper seq2seq export.
        Always exports to a directory named 'onnx' inside save_dir.
        """
        logger.info("Exporting Hint Generation model to ONNX (Optimum)...")
        onnx_dir = os.path.join(save_dir, "onnx")  # Always use 'onnx' as the export directory
        main_export(
            model_name_or_path=save_dir,
            output=onnx_dir,
            task="seq2seq-lm"
        )
        logger.info(f"ONNX export directory contents: {os.listdir(onnx_dir)}")
        # Quantize all .onnx files in the directory
        if quantize_dynamic and QuantType:
            for fname in os.listdir(onnx_dir):
                if fname.endswith('.onnx'):
                    onnx_model_file = os.path.join(onnx_dir, fname)
                    quant_path = os.path.join(save_dir, f"hint_quantized_{fname}")
                    logger.info(f"Quantizing {onnx_model_file} to {quant_path}")
                    quantize_dynamic(onnx_model_file, quant_path, weight_type=QuantType.QInt8)
                    logger.info(f"Hint quantized ONNX model saved to {quant_path}")
        else:
            logger.warning("onnxruntime.quantization not available; skipping quantization.")

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
        default="ai_model/exported_model",
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
        # Export QnA to ONNX and quantize
        trainer.export_qna_to_onnx(os.path.join(args.output_dir, 'qna'))
        
        # Hint Generation
        hint_dataset = trainer.prepare_hint_dataset(args.content_dir)
        trainer.train_hint(hint_dataset, epochs=args.epochs, batch_size=args.batch_size)
        # Export Hint Generation to ONNX and quantize
        trainer.export_hint_to_onnx(os.path.join(args.output_dir, 'hint'))
        
        logger.info("All training complete!")
        clean_exported_model_dir()
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise

def train_in_colab():
    """Train models in Colab with default paths, export ONNX, quantize, and zip output."""
    content_dir = "data/content"
    output_dir = "ai_model/exported_model"
    os.makedirs(content_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    trainer = NEBeduMultiTaskTrainer(output_dir=output_dir)
    # QnA
    qna_dataset = trainer.prepare_qna_dataset(content_dir)
    trainer.train_qna(qna_dataset)
    trainer.export_qna_to_onnx(os.path.join(output_dir, 'qna'))
    # Hint Generation
    hint_dataset = trainer.prepare_hint_dataset(content_dir)
    trainer.train_hint(hint_dataset)
    trainer.export_hint_to_onnx(os.path.join(output_dir, 'hint'))
    # Zip the output directory
    zip_path = output_dir + ".zip"
    shutil.make_archive(output_dir, 'zip', output_dir)
    print(f"\nTraining and export complete! Download your models from: {zip_path}\n")
    print("If running in Colab, use:")
    print("from google.colab import files\nfiles.download('ai_model/exported_model.zip')\n")
    clean_exported_model_dir()

def clean_exported_model_dir():
    """
    Remove unnecessary files from exported model directories, keeping only quantized ONNX files and tokenizer/config files.
    """
    import glob
    keep_patterns = [
        # QnA
        "qna_quantized.onnx", "tokenizer.json", "vocab.txt", "tokenizer_config.json", "special_tokens_map.json", "config.json",
        # Hint (T5)
        "hint_quantized_encoder_model.onnx", "hint_quantized_decoder_model.onnx", "hint_quantized_decoder_with_past_model.onnx",
        "tokenizer_config.json", "special_tokens_map.json", "spiece.model", "config.json", "generation_config.json"
    ]
    # QnA
    qna_dir = os.path.join("ai_model/exported_model/onnx", "qna")
    if os.path.exists(qna_dir):
        for fname in os.listdir(qna_dir):
            if not any(fname == pat for pat in keep_patterns):
                fpath = os.path.join(qna_dir, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    logger.info(f"Deleted {fpath}")
                elif os.path.isdir(fpath):
                    shutil.rmtree(fpath)
                    logger.info(f"Deleted directory {fpath}")
    # Hint
    hint_dir = os.path.join("ai_model/exported_model/onnx", "hint")
    if os.path.exists(hint_dir):
        for fname in os.listdir(hint_dir):
            if not any(fname == pat for pat in keep_patterns) and fname != "onnx":
                fpath = os.path.join(hint_dir, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    logger.info(f"Deleted {fpath}")
                elif os.path.isdir(fpath):
                    shutil.rmtree(fpath)
                    logger.info(f"Deleted directory {fpath}")
        # Clean up ONNX subdir (remove unquantized .onnx files)
        onnx_subdir = os.path.join(hint_dir, "onnx")
        if os.path.exists(onnx_subdir):
            for fname in os.listdir(onnx_subdir):
                if fname.endswith('.onnx'):
                    fpath = os.path.join(onnx_subdir, fname)
                    os.remove(fpath)
                    logger.info(f"Deleted {fpath}")

if __name__ == "__main__":
    import sys
    if any(arg.startswith('--content-dir') for arg in sys.argv):
        main()
    else:
        train_in_colab()
