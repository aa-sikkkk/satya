import os
import json
import numpy as np
import onnxruntime as ort
from transformers import T5Tokenizer, T5ForConditionalGeneration

# Set offline mode
os.environ["TRANSFORMERS_OFFLINE"] = "1"

HINT_MODEL_DIR = "ai_model/exported_model/onnx/hint/hint.onnx"
PYTORCH_MODEL_DIR = r"J:/GithubContribution/NEBedu/ai_model/exported_model/hint"
DATA_DIR = r"J:/GithubContribution/NEBedu/scripts/data_collection/data/content"

# Load tokenizers
onnx_tokenizer = T5Tokenizer.from_pretrained(HINT_MODEL_DIR)
pytorch_tokenizer = T5Tokenizer.from_pretrained(PYTORCH_MODEL_DIR)

# --- 1. Simple retrieval: find first context containing a keyword ---
def retrieve_context(question, data_dir, keyword=None):
    for fname in os.listdir(data_dir):
        if fname.endswith('.json'):
            with open(os.path.join(data_dir, fname), 'r', encoding='utf-8') as f:
                content = json.load(f)
                for topic in content.get('topics', []):
                    for subtopic in topic.get('subtopics', []):
                        for concept in subtopic.get('concepts', []):
                            context = concept.get('summary', '')
                            for q in concept.get('questions', []):
                                if isinstance(q, dict) and 'question' in q:
                                    if (keyword and keyword.lower() in context.lower()) or (question.lower() in q['question'].lower()):
                                        return context
    return None

# --- 2. User question ---
user_question = "What is a computer?"
retrieved_context = retrieve_context(user_question, DATA_DIR, keyword="computer")
if not retrieved_context:
    print("No relevant context found for the question.")
    exit()

sample_input = f"hint: {user_question} context: {retrieved_context}"
print(f"Sample Hint Input: {sample_input}")

# --- ONNX Inference ---
encoder_session = ort.InferenceSession(os.path.join(HINT_MODEL_DIR, "encoder_model.onnx"), providers=["CPUExecutionProvider"])
decoder_session = ort.InferenceSession(os.path.join(HINT_MODEL_DIR, "decoder_model.onnx"), providers=["CPUExecutionProvider"])

inputs = onnx_tokenizer(sample_input, return_tensors="np", max_length=128, truncation=True, padding="max_length")
input_ids = inputs["input_ids"]
attention_mask = inputs["attention_mask"]

encoder_outputs = encoder_session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
encoder_hidden_states = encoder_outputs[0]

max_length = 32
eos_token_id = onnx_tokenizer.eos_token_id
start_token_id = getattr(onnx_tokenizer, "decoder_start_token_id", onnx_tokenizer.pad_token_id)
decoder_input_ids = np.array([[start_token_id]], dtype=np.int64)

generated_ids = []
for step in range(max_length):
    decoder_inputs = {
        "input_ids": decoder_input_ids,
        "encoder_hidden_states": encoder_hidden_states,
        "encoder_attention_mask": attention_mask
    }
    decoder_outputs = decoder_session.run(None, decoder_inputs)
    logits = decoder_outputs[0]
    next_token_id = int(np.argmax(logits[:, -1, :], axis=-1)[0])
    print("ONNX Step", step, "logits:", logits[:, -1, :])
    print("ONNX Step", step, "predicted token id:", next_token_id)
    print("EOS token id:", eos_token_id)
    if next_token_id == eos_token_id:
        break
    decoder_input_ids = np.concatenate([decoder_input_ids, [[next_token_id]]], axis=1)
    generated_ids.append(next_token_id)

output_text = onnx_tokenizer.decode(generated_ids, skip_special_tokens=True)
print("Generated hint (ONNX):", output_text)

# --- PyTorch Inference ---
print("\n--- PyTorch T5 Inference ---")
pytorch_model = T5ForConditionalGeneration.from_pretrained(PYTORCH_MODEL_DIR)
inputs_pt = pytorch_tokenizer(sample_input, return_tensors="pt", max_length=128, truncation=True)
output_ids = pytorch_model.generate(inputs_pt.input_ids, max_length=32)
output_text_pt = pytorch_tokenizer.decode(output_ids[0], skip_special_tokens=True)
print("Generated hint (PyTorch):", output_text_pt) 
