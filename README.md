# 🚀 Project 002 – Building The Detective Archive (Part 1)

### Building the Police Department's First AI-Powered Detective Archive with RAG

---

## 📖 About This Project

Project 002 is the second practical project in **The Detective's Guide to AI** series.

After completing:

- 📖 Part 3 – *The Cold Case Files That Created RAG*
- 📖 Part 4 – *The Wrong Evidence That Made RAG Hallucinate*

the Police Department begins constructing its first AI-powered Detective Archive.

This project demonstrates, step by step, how a Retrieval-Augmented Generation (RAG) system works behind the scenes before introducing production AI frameworks.

Rather than treating RAG as a black box, every major component is implemented individually so you can understand how information flows from archived case files to an evidence-based response.

---

# 🎯 Project Objective

Build an educational Detective Archive capable of:

- Loading historical case files
- Splitting documents into searchable pages
- Creating passage fingerprints (embeddings)
- Measuring semantic similarity
- Building an evidence archive (vector store)
- Retrieving relevant evidence
- Reranking retrieved results
- Building grounded detective briefs
- Executing a complete educational RAG pipeline

---

# 📚 Prerequisites

Before starting this project, you should complete:

- ✅ Part 3 – The Cold Case Files That Created RAG
- ✅ Part 4 – The Wrong Evidence That Made RAG Hallucinate

This project assumes you already understand the theory presented in those articles.

---

# 🛠 Development Environment

Software

- Python 3.13+
- Visual Studio Code
- Git

Package Manager

- uv (recommended)
- or pip

Operating Systems

- macOS
- Linux
- Windows

---

# 📦 Libraries Used

This project intentionally uses only the Python standard library.

- math
- os
- pathlib
- textwrap

No external AI frameworks are used in this project.

Every RAG component is implemented educationally before introducing production-ready AI libraries in the next project.

---

# 📂 Project Structure

```text
project-002-detective-archive/

README.md
PROJECT-002-PLAN.md

case-files/
    millbrook_arson_2019.txt

detective-archive/
    01_intelligence_gap.py
    02_case_file_splitter.py
    03_fingerprint_engine.py
    04_relevance_scorer.py
    05_evidence_archive.py
    06_retrieval_desk.py
    07_precision_ranker.py
    08_detective_brief.py
    09_complete_archive.py

scripts/
    generate_article_assets.py
```

---

# 🏗 Construction Milestones

## 1. Knowledge Cutoff

**The Intelligence Gap**

Demonstrates why a Large Language Model cannot answer questions outside its training data.

---

## 2. Document Chunking

**The Case File Splitter**

Splits investigation files into smaller overlapping pages suitable for retrieval.

---

## 3. Embeddings

**The Fingerprint Engine**

Converts every page into a mathematical fingerprint representing its meaning.

---

## 4. Cosine Similarity

**The Relevance Scorer**

Measures how closely a detective's question matches every archived page.

---

## 5. Vector Store

**The Evidence Archive**

Stores pages together with their fingerprints and supports similarity search.

---

## 6. Retrieval

**The Retrieval Desk**

Accepts natural-language questions and retrieves the most relevant evidence.

---

## 7. Reranking

**The Precision Ranker**

Improves retrieval quality by reordering the returned evidence.

---

## 8. Prompt Augmentation & Grounding

**The Detective's Brief**

Builds the complete prompt that will be delivered to the Large Language Model.

---

## 9. Complete RAG Pipeline

**The Complete Detective Archive**

Connects every previous milestone into one complete Retrieval-Augmented Generation pipeline.

---

# ▶️ Running The Project

Execute each milestone individually.

Example:

```bash
python3 detective-archive/01_intelligence_gap.py
```

or execute the completed pipeline:

```bash
python3 detective-archive/09_complete_archive.py
```

---

# ⚠️ Educational Note

The implementations in this project are intentionally educational.

Production RAG systems typically use libraries such as:

- LangChain
- LlamaIndex
- Chroma
- FAISS
- Pinecone
- OpenAI / Anthropic SDKs

This project deliberately avoids those libraries so you can understand how a RAG pipeline works before relying on production frameworks.

The next part of Project 002 introduces those production components while continuing to build the same Detective Archive.

---

# 🎓 Learning Outcomes

After completing Project 002 (Part 1), you'll understand:

- Knowledge Cutoff
- Document Chunking
- Passage Embeddings
- Cosine Similarity
- Vector Stores
- Retrieval
- Reranking
- Prompt Augmentation
- Grounding
- Complete Retrieval-Augmented Generation Pipelines

---

# 🚀 What's Next?

The Detective Archive can now retrieve information from historical case files.

The next step is making it trustworthy.

Continue with:

> 🚀 **Project 002 – Building The Detective Archive (Part 2)**

In the next project, you'll transform this educational RAG pipeline into a production-style AI investigation system by introducing:

- Production LLM integration
- Production RAG libraries
- Evidence verification
- Fact checking
- Guardrails
- Trusted AI responses

---

**The archive is built.**

**Now it's time to make it trustworthy.**