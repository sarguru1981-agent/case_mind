# =============================================================================
# THE POLICE ACADEMY — Part 2, Chapter 2
#
# First exam day. Morgan reads the beginning of a case report and stops
# at a blank. He taps it with his marker.
#
#   "What comes next?"
#
# A well-trained cadet — one who has read all the case files — answers
# quickly and accurately. A cadet who hasn't studied guesses.
#
# A language model does exactly this. Given context, it produces a
# probability distribution over every word in the vocabulary.
# The most probable token is the prediction. This is INFERENCE.
# =============================================================================


def build_bigram_counts(text):
    """Count how often each word follows each other word."""
    words  = text.lower().split()
    counts = {}
    for i in range(len(words) - 1):
        ctx = words[i]
        nxt = words[i + 1]
        if ctx not in counts:
            counts[ctx] = {}
        counts[ctx][nxt] = counts[ctx].get(nxt, 0) + 1
    return counts


def predict_next(counts, context_word, top_k=4):
    """Return the top-k predicted next words with their probabilities."""
    if context_word not in counts:
        return []
    followers = counts[context_word]
    total     = sum(followers.values())
    ranked    = sorted(followers.items(), key=lambda x: x[1], reverse=True)
    return [(word, count / total) for word, count in ranked[:top_k]]


# ---------------------------------------------------------------------------
# The training corpus — past case reports from the academy archive,
# including notes from the Royal Diamond Theft investigation
# ---------------------------------------------------------------------------

training_corpus = """
the suspect entered the building the suspect fled the building
the detective found the suspect the detective found the evidence
the witness saw the suspect the witness saw the detective
the suspect left footprints the suspect left the scene
the detective solved the case the detective closed the case
the evidence confirmed the suspect the evidence confirmed the crime
the royal diamond was found the royal diamond was stolen
lord blackwell entered the museum lord blackwell fled the scene
"""

print("=" * 62)
print("  CASE FILE 11")
print()
print("  Case:")
print("  The Police Academy")
print()
print("  Article:")
print("  Part 2")
print()
print("  Chapter:")
print("  Next Token Prediction")
print()
print("  Investigation Status:")
print("  Academy — Term 1, Exam Day")
print()
print("  Objective:")
print("  Build a bigram language model from academy case files")
print("  and run the first next-token prediction exam.")
print("=" * 62)

print("""
Morgan stands at the board. He writes the beginning of a case report.
He stops. He taps the blank with his marker.

  "The case report reads: [ word ] ___. What comes next?"

The cadet who has read the archive knows.
The cadet who hasn't — guesses and gets it wrong.

A language model answers this question for every token in its
training data. Billions of answers. One objective.
""")

counts = build_bigram_counts(training_corpus)

test_prompts = ["the", "suspect", "detective", "evidence", "lord"]

for word in test_prompts:
    predictions = predict_next(counts, word, top_k=4)
    if not predictions:
        continue
    print(f'  Prompt: "...the report says [{word}] ___"')
    print(f"  Model predictions:")
    for pred_word, prob in predictions:
        bar = "█" * int(prob * 35)
        print(f"    → '{pred_word}':{'':<12}  {prob:.3f}  {bar}")
    print()

print("""  "This model has one word of context and fifteen words of vocabulary,"
  Morgan tells the class.

  "GPT-4 has 128,000 tokens of context and 100,000 vocabulary words.
   The mechanism is identical. Only the scale is different.

   The model never decides what to say.
   It calculates probabilities and samples from them.
   Language is statistics. Intelligence is scale."
""")

print("""
==========================

Investigation Summary

Morgan delivers the first exam. For each partial case report, the model
trained on academy archives produces a ranked probability distribution over
possible next words. Cadets who studied the Royal Diamond Theft files predict
accurately — those who didn't, distribute their probability too widely.

AI Connection

Language model inference is next-token prediction applied repeatedly. The
model produces a probability distribution over the full vocabulary and
samples from it. There is no "deciding" — only probabilities computed from
patterns seen during training, applied at incomprehensible scale.

Continue Investigation

The exams are collected. Morgan picks up the red pen to grade them.
Continue to:
    03_loss_function.py
""")
