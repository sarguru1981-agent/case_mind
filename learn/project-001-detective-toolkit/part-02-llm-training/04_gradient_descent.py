# =============================================================================
# THE POLICE ACADEMY — Part 2, Chapter 4
#
# Cadet Riley keeps predicting the wrong suspect.
# After each wrong answer, Morgan gives feedback:
#   "You predicted 0.4. The correct answer was 0.7. Adjust."
#
# Riley adjusts. A small step. Not too large. Not too small.
# The next answer is a little better. The one after that, better still.
#
# This is GRADIENT DESCENT. After each training example, the model's
# weights are nudged in the direction that would have reduced the loss.
# The LEARNING RATE controls how large each nudge is.
# =============================================================================


def predict(weight, x):
    """Linear model: ŷ = weight × evidence_strength"""
    return weight * x


def mse_loss(predicted, actual):
    """Mean Squared Error: (ŷ - y)²"""
    return (predicted - actual) ** 2


def gradient(weight, x, actual):
    """
    Derivative of MSE w.r.t. weight:
      d/dw [ (w·x - y)² ] = 2 · (w·x - y) · x
    """
    return 2 * (predict(weight, x) - actual) * x


# ---------------------------------------------------------------------------
# Training scenario:
#   Cadet Riley must learn: suspect_probability = 0.7 × evidence_strength
#   Starting weight: 0.05 — a random guess, far too low
#   Target weight: 0.70
# ---------------------------------------------------------------------------

training_examples = [
    (0.8, 0.56),   # evidence_strength 0.8 → correct suspect_prob 0.56
    (0.5, 0.35),
    (1.0, 0.70),
    (0.3, 0.21),
    (0.9, 0.63),
    (0.6, 0.42),
]

weight        = 0.05    # Riley's starting guess
learning_rate = 0.08    # how much Riley adjusts after each correction

print("=" * 62)
print("  CASE FILE 13")
print()
print("  Case:")
print("  The Police Academy")
print()
print("  Article:")
print("  Part 2")
print()
print("  Chapter:")
print("  Gradient Descent")
print()
print("  Investigation Status:")
print("  Academy — Term 1, Individual Remediation")
print()
print("  Objective:")
print("  Watch a single weight converge from 0.05 to 0.70 across")
print("  20 correction steps driven by the gradient.")
print("=" * 62)

print(f"""
Cadet Riley is learning one rule:

  suspect_probability = weight × evidence_strength

The correct weight is 0.70. Riley starts at 0.05 — a random guess.

After every exercise, Morgan writes Riley's loss on the board
and says: "Adjust. The gradient tells you which direction.
The learning rate ({learning_rate}) tells you how far."
""")

print(f"  {'Step':<5}  {'Weight':>8}  {'x':>5}  {'ŷ = w·x':>10}  "
      f"{'y (true)':>10}  {'Loss':>10}  {'Gradient':>11}")
print(f"  {'-'*73}")

for step in range(1, 21):
    x, y  = training_examples[(step - 1) % len(training_examples)]
    pred  = predict(weight, x)
    loss  = mse_loss(pred, y)
    grad  = gradient(weight, x, y)

    print(f"  {step:<5}  {weight:>8.4f}  {x:>5.1f}  {pred:>10.4f}  "
          f"{y:>10.4f}  {loss:>10.6f}  {grad:>11.6f}")

    weight = weight - learning_rate * grad

print(f"\n  Riley's final weight:  {weight:.4f}")
print(f"  Target weight:         0.7000")
print(f"  Remaining error:       {abs(weight - 0.7):.4f}")

print("""
  Morgan looks at the convergence curve on the board.

  "Each step nudges the weight toward the truth.
   Positive gradient? Move left. Negative? Move right.
   The loss shrinks. The model improves. That's all training is.

   In a real LLM, this happens for billions of parameters simultaneously,
   after every batch of training tokens, for weeks on end.
   Same update rule. Incomprehensible scale."
""")

print("""
==========================

Investigation Summary

Cadet Riley begins with a weight of 0.05 and must converge to 0.70 through
20 correction steps. After each mistake, the gradient points in the direction
of improvement. With a learning rate of 0.08, Riley's weight approaches the
target steadily — every mistake teaches the right direction to move.

AI Connection

Gradient descent is the core update rule behind every neural network.
The gradient of the loss points uphill — the model steps downhill. Learning
rate controls step size: too large and the model overshoots; too small and
it takes forever. This update happens for billions of weights simultaneously.

Continue Investigation

Riley is ready to join the full class. The complete training loop — all
cadets, all case files, 60 epochs — begins now.
Continue to:
    05_training_loop.py
""")
