from transformers import pipeline, BitsAndBytesConfig
import torch
from sentence_transformers import SentenceTransformer

# ---------- Classifier ---------
classifier = pipeline(
    "zero-shot-classification",
    model="typeform/distilbert-base-uncased-mnli",
    device=-1  # Run on CPU to save VRAM
)

# ---------- Embeddings ----------
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    device="cpu"  # Run on CPU to save VRAM
)

# ---------- Extractive QA ----------
qa_pipeline = pipeline(
    "question-answering",
    model="deepset/roberta-base-squad2",
    device=-1  # Run on CPU to save VRAM
)

# ---------- Synthesis LLM ----------
from transformers import AutoModelForCausalLM, AutoTokenizer

SYNTH_MODEL = "microsoft/phi-3-mini-4k-instruct"

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    llm_int8_enable_fp32_cpu_offload=True
)

_synth_model = None
_tokenizer = None

def synthesize(prompt: str) -> str:
    global _synth_model, _tokenizer
    if _synth_model is None:
        _synth_model = AutoModelForCausalLM.from_pretrained(
            SYNTH_MODEL,
            device_map="auto",
            quantization_config=quantization_config
        )
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(SYNTH_MODEL)
    inputs = _tokenizer(prompt, return_tensors="pt").to(_synth_model.device)
    output = _synth_model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.2,
        do_sample=False
    )
    return _tokenizer.decode(output[0], skip_special_tokens=True)
