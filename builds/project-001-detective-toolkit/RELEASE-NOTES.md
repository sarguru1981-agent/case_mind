# Build 1 — Release Notes

**Version:** Build 1  
**Codename:** The First Detective Toolkit

**Related Articles:**
- Part 1 — The Robbery That Taught Me Transformers
- Part 2 — The Police Academy That Built an LLM

---

## Overview

Build 1 teaches the complete foundation of how a large language model is constructed and trained — from raw text to a working training loop.

The learning is structured as two investigations. In Part 1, Detective Morgan works the Royal Diamond Theft and, piece by piece, assembles the transformer architecture: how text is broken into tokens, how tokens become vectors, how the model encodes position, how attention mechanisms connect distant ideas, and how a full transformer layer processes all of it. By the end of Part 1, the reader has built every major component of a transformer from scratch using nothing but Python's standard library.

In Part 2, Morgan moves to the Police Academy as a training instructor. The cadets represent the model itself — learning from data, making predictions, receiving a loss signal, following a gradient, and iterating through a full training loop. By the end of Part 2, the reader understands exactly how a language model learns from text and why next-token prediction at scale produces genuinely capable intelligence.

All 14 scripts are runnable immediately with `python3`. No frameworks. No dependencies beyond the standard library.

---

## Included

### Part 1 — The Transformer Toolkit (`part-01-transformers/`)

Nine scripts covering the complete transformer architecture:

| Script | Chapter |
|--------|---------|
| `01_tokens.py` | Tokenization |
| `02_token_ids.py` | Token IDs |
| `03_simple_tokenizer.py` | The Tokenizer |
| `04_embeddings.py` | Embeddings |
| `05_positional_encoding.py` | Positional Encoding |
| `06_attention.py` | Attention |
| `07_self_attention.py` | Self-Attention |
| `08_multi_head_attention.py` | Multi-Head Attention |
| `09_transformer_layer.py` | The Transformer Layer |

### Part 2 — The LLM Training Toolkit (`part-02-llm-training/`)

Five scripts covering the complete pre-training process:

| Script | Chapter |
|--------|---------|
| `01_training_examples.py` | Training Data |
| `02_next_token_prediction.py` | Next Token Prediction |
| `03_loss_function.py` | The Loss Function |
| `04_gradient_descent.py` | Gradient Descent |
| `05_training_loop.py` | The Training Loop |

### Supporting Files

- **`BUILD-01-GUIDE.md`** — recommended reading order, prerequisites, and a chapter-by-chapter walkthrough. The right starting point for any first-time reader.
- **`README.md`** — quick-start reference: how to run scripts, folder structure, and what each part covers.
- **`scripts/generate_article_assets.py`** — generates all article assets (plain-text outputs, HTML terminal cards, PNG screenshots) for every script in Build 1. Requires `Pillow` for PNG generation; everything else uses the standard library.

---

## Learning Outcomes

After completing Build 1, the reader will understand:

- **Tokenization** — how raw text is split into discrete units a model can process
- **Token IDs** — how tokens are mapped to integers and stored in a vocabulary
- **The Tokenizer** — how encoding and decoding work as inverse operations
- **Embeddings** — how token IDs become dense vectors that carry semantic meaning
- **Positional Encoding** — how transformers encode word order using sine/cosine signals
- **Attention** — how a model scores every piece of evidence against a single query
- **Self-Attention** — how every token simultaneously attends to every other token
- **Multi-Head Attention** — how multiple attention heads examine the same input from independent perspectives
- **The Transformer Layer** — how self-attention, residual connections, normalisation, and feed-forward processing combine into a single reusable block
- **Training Data** — how a sliding window over raw text generates billions of next-token prediction examples
- **Next Token Prediction** — how a model produces a probability distribution over its entire vocabulary for every position
- **The Loss Function** — how cross-entropy quantifies prediction quality and penalises confident wrong answers
- **Gradient Descent** — how the loss signal is used to nudge every weight in the direction that reduces error
- **The Training Loop** — how tokenisation, prediction, loss, and gradient descent combine into the single loop that produces a trained language model

---

## Repository Philosophy

Build 1 intentionally prioritises conceptual understanding over implementation completeness.

The mathematics is faithful to how transformers and LLMs actually work — the softmax, the scaled dot-product, the sinusoidal positional encoding, the cross-entropy loss, and the gradient update rule are all correct. What is simplified is scale: small vocabularies, small embedding dimensions, and tiny datasets are used so that every number on screen is readable and traceable by hand.

This is a deliberate choice. A reader who can follow a 5×5 attention matrix and see why one clue attends more strongly to another has built genuine intuition. That intuition transfers directly to understanding what GPT-4 is doing across 96 heads and 175 billion parameters — the mechanism is identical, only the scale differs.

Future builds extend this toolkit rather than replacing it. The concepts from Build 1 are the vocabulary that every subsequent build assumes. Nothing here becomes obsolete.

---

## What's Next

The next milestone begins after the Retrieval-Augmented Generation articles.

Having completed Build 1, the reader understands how a language model is constructed and trained. The RAG series examines what happens when that model is connected to external knowledge — how retrieval, chunking, embedding search, and context injection extend a model beyond its training data.

After those articles, the reader will build:

**Build 2** — a working retrieval-augmented generation pipeline, constructed using everything learned in Build 1 and the RAG series.
