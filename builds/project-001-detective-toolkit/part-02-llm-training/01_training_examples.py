# =============================================================================
# THE POLICE ACADEMY — Part 2, Chapter 1
#
# The Royal Diamond Theft is solved. Lord Blackwell is in custody.
# Detective Morgan is promoted and given a new assignment:
#   train the next generation of detectives.
#
# Morgan opens the academy's archive. Thousands of past case files.
# He designs one exercise — the only exercise:
#
#   "I will show you the beginning of a case report.
#    Your job: predict the next word. Every word. Every report."
#
# In AI, this is the LANGUAGE MODELLING OBJECTIVE — next-token prediction.
# It is the only training task used to pre-train every major LLM.
# =============================================================================


def make_training_examples(text, context_size=3):
    """
    Slide a window of size `context_size` over the text.
    Produce (context_tokens, next_token) pairs — one per position.

    This is the "language modelling objective": given N words, predict
    word N+1. Repeat for every word in every document ever written.
    """
    words    = text.split()
    examples = []
    for i in range(context_size, len(words)):
        context = words[i - context_size : i]
        target  = words[i]
        examples.append((context, target))
    return examples


# ---------------------------------------------------------------------------
# The academy textbook — excerpts from past case files in the archive
# ---------------------------------------------------------------------------

academy_textbook = (
    "the suspect entered the building through the window "
    "the detective found footprints near the window "
    "the witness saw the suspect flee the scene "
    "the detective arrested the suspect at dawn "
    "the evidence confirmed the guilty verdict "
    "the royal diamond was recovered from the harbour"
)

print("=" * 62)
print("  CASE FILE 10")
print()
print("  Case:")
print("  The Police Academy")
print()
print("  Article:")
print("  Part 2")
print()
print("  Chapter:")
print("  Training Data")
print()
print("  Investigation Status:")
print("  Academy — Term 1, Day 1")
print()
print("  Objective:")
print("  Convert past case files into next-token prediction training")
print("  examples using a sliding context window.")
print("=" * 62)

print("""
Detective Morgan walks into the academy lecture hall.
He drops a thick stack of case files onto the desk.

  "This is your entire curriculum," he tells the cadets.
  "I will read a sentence from a case file and stop.
   Your job: tell me the next word.

   We will do this for every word in every file in this archive.
   That is ALL pre-training is. Next word. Again. Again. Again."

The cadets look at the stack. It reaches the ceiling.
""")

examples = make_training_examples(academy_textbook, context_size=3)

print(f'Textbook excerpt: "{academy_textbook[:65]}..."\n')
print(f"Context window: 3 tokens\n")
print(f"  {'#':<4}  {'Context (what the cadet reads)':<42}  Next word")
print(f"  {'-'*60}")

for i, (ctx, target) in enumerate(examples[:14]):
    ctx_str = " ".join(ctx)
    print(f"  {i+1:<4}  [{ctx_str}]{'':<{38 - len(ctx_str)}}  → '{target}'")

print(f"\n  ... {len(examples)} total training examples from this short excerpt alone.")

print("""
  Note: in a real LLM, contexts and targets are token IDs, not raw words.
  Words are used here to keep the learning process readable.
""")

print("""
  "GPT-3 trained on 300 billion tokens," Morgan tells the class.
  "At context_size=2048, that's hundreds of billions of these pairs.
   Same mechanism. Incomprehensible scale."

  A cadet raises her hand.
  "Is that really all it takes to build something intelligent?"

  Morgan nods.
  "If you predict the next word well enough across enough text,
   you must have learned grammar, facts, reasoning — everything.
   Intelligence is a side effect of predicting well at scale."
""")

print("""
==========================

Investigation Summary

Morgan arrives at the Police Academy as the new lead instructor, bringing
the Royal Diamond Theft case files with him as curriculum material. He shows
the cadets that every sentence in every case file becomes training pairs
through a sliding window. The only question is always: what comes next?

AI Connection

Next-token prediction is the sole pre-training objective behind every major
LLM. Billions of (context, target) pairs teach grammar, facts, and reasoning
as emergent side effects of learning to predict well. There is no separate
"understanding" objective — it is all prediction at scale.

Continue Investigation

The cadets are ready. Tomorrow Morgan gives the first prediction exam.
Continue to:
    02_next_token_prediction.py
""")
