# Build 1 — Building The First Detective Toolkit

> **New to Build 1?**
>
> Start with **[BUILD-01-GUIDE.md](BUILD-01-GUIDE.md)**.
>
> Then follow the guide chapter by chapter.

---

## What Is This?

A collection of simple, beginner-friendly Python examples that explain core
transformer and LLM concepts through a detective story metaphor.

Every file is a standalone script you can run directly with `python`. No web
servers, no APIs, no neural-network libraries — just the ideas, made concrete.

---

## Which Articles Does This Support?

| Build | Article |
|-------|---------|
| Part 1 | **The Robbery That Taught Me Transformers** |
| Part 2 | **The Police Academy That Built an LLM** |

---

## How to Run

```bash
# From the repo root
cd builds/build-01-detective-toolkit

# Run any example directly
python3 part-01-transformers/01_tokens.py
python3 part-02-llm-training/05_training_loop.py
```

No dependencies to install. Python 3.8+ is all you need.

---

## What Each File Teaches

### Part 1 — Transformers (`part-01-transformers/`)

| File | Concept | Detective Metaphor |
|------|---------|-------------------|
| `01_tokens.py` | Tokenization | Breaking a crime report into individual clues |
| `02_token_ids.py` | Token IDs / Vocabulary | Assigning case numbers to each clue |
| `03_simple_tokenizer.py` | Encode & Decode | The evidence management system |
| `04_embeddings.py` | Token Embeddings | Suspect profile cards as vectors |
| `05_positional_encoding.py` | Positional Encoding | The order of events at the crime scene |
| `06_attention.py` | Attention Scores | Detective focusing on the most relevant clues |
| `07_self_attention.py` | Self-Attention | Each clue cross-examining all other clues |
| `08_multi_head_attention.py` | Multi-Head Attention | Multiple detectives, each with a different angle |
| `09_transformer_layer.py` | Transformer Layer | The full case-review meeting |

### Part 2 — LLM Training (`part-02-llm-training/`)

| File | Concept | Detective Metaphor |
|------|---------|-------------------|
| `01_training_examples.py` | Training Data | The academy textbook: context → next word |
| `02_next_token_prediction.py` | Next Token Prediction | The cadet's exam: what comes next? |
| `03_loss_function.py` | Cross-Entropy Loss | Grading the cadet's predictions |
| `04_gradient_descent.py` | Gradient Descent | Each mistake updates the cadet's mental model |
| `05_training_loop.py` | The Training Loop | The full academy curriculum, end to end |

---

## Important Note

These examples are **simplified concept demonstrations**, not production ML code.

- Vectors are hand-crafted or randomly initialized to illustrate shape and flow.
- Weight matrices are tiny (8×8 at most) so you can read every number.
- Math uses only Python's `math` and `random` standard library modules.
- Real transformers use PyTorch/JAX, learned projections, layer stacks, and
  billions of parameters — but the core ideas here are the same ones.

The goal is understanding, not performance.
