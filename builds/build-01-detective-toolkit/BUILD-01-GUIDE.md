# Build 1 — The First Detective Toolkit

## Purpose

This guide is your companion while reading:

- **Part 1 — The Robbery That Taught Me Transformers**
- **Part 2 — The Police Academy That Built an LLM**

Each Python script in this build is a working code example for one chapter of those articles. The scripts are not standalone exercises — they are meant to be run *while you read*, at the exact moment the article introduces the concept.

**The intended rhythm is:**

```
Read a chapter in the article
        ↓
Run the matching Python file
        ↓
Observe the output in your terminal
        ↓
Return to the article
        ↓
Repeat
```

You do not need to understand every line of code. The output is the lesson.

---

## Requirements

Python 3.8 or later. No additional packages required.

```bash
cd builds/build-01-detective-toolkit
python3 part-01-transformers/01_tokens.py
```

---

## Part 1 Roadmap

*Case: The Royal Diamond Theft*

| Article Chapter | Python File | What You Will Learn | Expected Output |
|---|---|---|---|
| Tokenization | `part-01-transformers/01_tokens.py` | How raw text is broken into individual tokens before any model processing begins | The crime report split into 16 numbered word-level tokens |
| Token IDs | `part-01-transformers/02_token_ids.py` | How every unique token receives a permanent integer ID, and why computers need numbers not words | An evidence registry of 28 unique IDs; the crime report encoded as a list of integers |
| The Tokenizer | `part-01-transformers/03_simple_tokenizer.py` | How a tokenizer encodes text to IDs and decodes IDs back to text; how unknown words are handled | Witness statement encoded and decoded perfectly; unknown words (leather, gloves, lockpicks) collapse to ID 1 |
| Embeddings | `part-01-transformers/04_embeddings.py` | How tokens become dense vectors of numbers; how similarity between suspects is measured mathematically | Five-dimensional profile cards for all four suspects; Lord Blackwell scores as the closest match to the theft profile |
| Positional Encoding | `part-01-transformers/05_positional_encoding.py` | How order is injected into token embeddings using sine and cosine signals | Crime timeline encoded as unique vectors; reversing two events produces different encoding values |
| Attention | `part-01-transformers/06_attention.py` | How a single query scores all evidence for relevance; how the output is a weighted blend, not a single choice | Five evidence items scored; the vault keypad log and Blackwell's presence score highest |
| Self-Attention | `part-01-transformers/07_self_attention.py` | How every token attends to every other token simultaneously; how each representation is enriched by the full sequence | A 5×5 attention matrix; before and after representations showing how each clue absorbs context from all others |
| Multi-Head Attention | `part-01-transformers/08_multi_head_attention.py` | How three parallel attention passes — motive, evidence, timeline — each find different patterns; how the results are combined | Three 2D outputs per clue from three specialist detectives; concatenated into one 6D vector richer than any single head |
| The Transformer Layer | `part-01-transformers/09_transformer_layer.py` | How one complete transformer layer works: self-attention, residual connection, layer norm, feed-forward, residual, layer norm | Three stages of transformation across five key clues; the repeating unit of every LLM demonstrated end to end |

---

## Part 2 Roadmap

*Case: The Police Academy*

| Article Chapter | Python File | What You Will Learn | Expected Output |
|---|---|---|---|
| Training Data | `part-02-llm-training/01_training_examples.py` | How past case files become training pairs; how a sliding window generates (context, target) examples at every position | Every word in the academy textbook becomes a prediction target; dozens of training pairs from one short paragraph |
| Next Token Prediction | `part-02-llm-training/02_next_token_prediction.py` | How a language model produces a probability distribution over the vocabulary; how inference works at its core | Ranked probability bars for five context words; words seen often after a given context score highest |
| The Loss Function | `part-02-llm-training/03_loss_function.py` | How cross-entropy loss measures the quality of a prediction; why confident wrong answers are penalised most severely | Three graded cadets — confident correct, uncertain, confident wrong — with loss scores showing the asymmetry |
| Gradient Descent | `part-02-llm-training/04_gradient_descent.py` | How a single weight is updated after each mistake; how the gradient points toward improvement; how learning rate controls step size | A weight converging from 0.05 toward 0.70 across 20 steps with loss, gradient, and weight shown at every step |
| The Training Loop | `part-02-llm-training/05_training_loop.py` | How the complete training algorithm works: forward pass, loss, gradient, weight update, repeat for 60 epochs | Before-training random predictions followed by after-training accurate predictions; loss curve across all 60 epochs |

---

## Suggested Reading Flow

Work through each chapter in order. Run the script at the moment the article introduces the concept — not before, not after.

---

**Part 1, Chapter 1 — Tokenization**

```
Read:     The section on tokenization in Part 1

Run:      python3 part-01-transformers/01_tokens.py

Observe:  The crime report broken into 16 individual tokens.
          Notice that punctuation is stripped and everything is lowercase.

Return:   Continue reading Part 1
```

---

**Part 1, Chapter 2 — Token IDs**

```
Read:     The section on token IDs and vocabulary in Part 1

Run:      python3 part-01-transformers/02_token_ids.py

Observe:  Every unique word receives a permanent integer ID.
          The crime report sentence becomes a list of numbers.

Return:   Continue reading Part 1
```

---

**Part 1, Chapter 3 — The Tokenizer**

```
Read:     The section on the tokenizer in Part 1

Run:      python3 part-01-transformers/03_simple_tokenizer.py

Observe:  The witness statement encoded to IDs and decoded back.
          Words outside the vocabulary become ID 1 (<UNK>).

Return:   Continue reading Part 1
```

---

**Part 1, Chapter 4 — Embeddings**

```
Read:     The section on embeddings in Part 1

Run:      python3 part-01-transformers/04_embeddings.py

Observe:  Suspect profile cards as 5-dimensional vectors.
          Cosine similarity ranks Blackwell as the closest match.

Return:   Continue reading Part 1
```

---

**Part 1, Chapter 5 — Positional Encoding**

```
Read:     The section on positional encoding in Part 1

Run:      python3 part-01-transformers/05_positional_encoding.py

Observe:  Each crime event gets a unique sine/cosine vector.
          Swapping two events changes their encodings — order is not free.

Return:   Continue reading Part 1
```

---

**Part 1, Chapter 6 — Attention**

```
Read:     The section on attention in Part 1

Run:      python3 part-01-transformers/06_attention.py

Observe:  Morgan's query scores all five pieces of evidence.
          Weights sum to 1. The output is a blend, not a single choice.

Return:   Continue reading Part 1
```

---

**Part 1, Chapter 7 — Self-Attention**

```
Read:     The section on self-attention in Part 1

Run:      python3 part-01-transformers/07_self_attention.py

Observe:  The 5×5 attention matrix showing every clue attending to every other.
          Compare raw vectors to the enriched vectors after attention.

Return:   Continue reading Part 1
```

---

**Part 1, Chapter 8 — Multi-Head Attention**

```
Read:     The section on multi-head attention in Part 1

Run:      python3 part-01-transformers/08_multi_head_attention.py

Observe:  Three specialists produce separate 2D outputs.
          Concatenation produces a 6D vector richer than any single head.

Return:   Continue reading Part 1
```

---

**Part 1, Chapter 9 — The Transformer Layer**

```
Read:     The section on the transformer layer in Part 1

Run:      python3 part-01-transformers/09_transformer_layer.py

Observe:  Three stages of transformation on five clues.
          The layer structure diagram. Case closed.

Finish:   Complete Part 1 — The Robbery That Taught Me Transformers
```

---

**Part 2, Chapter 1 — Training Data**

```
Read:     The section on training data in Part 2

Run:      python3 part-02-llm-training/01_training_examples.py

Observe:  Every word in the academy textbook becomes a prediction target.
          One short paragraph generates dozens of training examples.

Return:   Continue reading Part 2
```

---

**Part 2, Chapter 2 — Next Token Prediction**

```
Read:     The section on next-token prediction in Part 2

Run:      python3 part-02-llm-training/02_next_token_prediction.py

Observe:  Probability distributions with bar charts for five context words.
          Words seen often in context score highest — no magic, only statistics.

Return:   Continue reading Part 2
```

---

**Part 2, Chapter 3 — The Loss Function**

```
Read:     The section on the loss function in Part 2

Run:      python3 part-02-llm-training/03_loss_function.py

Observe:  Three cadets graded on the same question.
          Confident wrong answer receives the highest loss.

Return:   Continue reading Part 2
```

---

**Part 2, Chapter 4 — Gradient Descent**

```
Read:     The section on gradient descent in Part 2

Run:      python3 part-02-llm-training/04_gradient_descent.py

Observe:  A weight converging from 0.05 to 0.70 across 20 steps.
          Watch the loss shrink and the gradient change direction.

Return:   Continue reading Part 2
```

---

**Part 2, Chapter 5 — The Training Loop**

```
Read:     The section on the training loop in Part 2

Run:      python3 part-02-llm-training/05_training_loop.py

Observe:  Random predictions before training. Accurate predictions after.
          The loss curve across 60 epochs. Graduation.

Finish:   Complete Part 2 — The Police Academy That Built an LLM
```

---

## Build Completion

When you have run all 14 scripts and finished both articles, you will have:

- **Built a simplified transformer from first principles** — tokenization through a full transformer layer, using only Python's standard library
- **Understood how LLMs are trained** — next-token prediction, cross-entropy loss, gradient descent, and the full training loop
- **Completed the first Detective Toolkit** — the Royal Diamond Theft investigated, the Police Academy graduated

This is Build 1. It is a foundation, not a final destination.

**The next build begins after the RAG article.** Build 2 will introduce retrieval-augmented generation — where the detective gains access to an external case file archive and learns to retrieve relevant documents before answering.

---

## Learning Philosophy

These scripts intentionally simplify real transformer internals.

**What is simplified:**
- Vectors are hand-crafted or randomly initialised to small sizes (4D, 6D, 8D) so every number is readable in a terminal
- Weight matrices are tiny (8×8 at most) to make training visible within seconds
- The feed-forward network uses fixed coefficients rather than learned weights
- Self-attention uses Q = K = V rather than separate learned projections

**What is accurate:**
- The mathematical operations — dot product, softmax, cosine similarity, cross-entropy, gradient descent — are correct and unmodified
- The layer structure — self-attention → add & norm → feed-forward → add & norm — matches real transformer architecture
- The training objective — next-token prediction, loss minimisation, weight update — is identical to pre-training in GPT-style models
- The concepts map directly to the sections of the articles they accompany

**The objective is conceptual understanding, not production implementation.**

Each script corresponds to exactly one section of one article. Read the section. Run the script. The understanding compounds across all 14 files.
