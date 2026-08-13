# =============================================================================
# THE COLD CASE FILES — Part 3, Milestone 1
#
# Detective Morgan has been asked a question about the Millbrook Arson
# of 2019. He opens the department's intelligence desk — the same system
# that has answered hundreds of case queries without hesitation.
#
# He asks the question.
#
# The desk goes quiet.
#
# The case was filed in 2019. The system was trained on records up to
# the end of 2018. The Millbrook Arson does not exist in its knowledge.
#
# But the case file does exist. It has been sitting in the archive
# since 2019, containing the exact answer Detective Morgan needs.
#
# This is the gap the Detective Archive will close.
# =============================================================================

import os


# ---------------------------------------------------------------------------
# SimulatedLLM
#
# A language model with a fixed training cutoff. Knows only what was
# included in its training data. Always returns a string — a real LLM
# never returns silence, it returns "I don't know."
#
# Later milestones will replace this class with a production library.
# The interface — llm.ask(question) — stays the same throughout.
# ---------------------------------------------------------------------------

class SimulatedLLM:

    TRAINING_CUTOFF = "December 2018"

    _TRAINING_DATA = {
        "riverside bank robbery 2015": (
            "Three suspects identified from CCTV analysis. "
            "Primary suspect convicted April 2016. Case closed."
        ),
        "northgate pharmacy break-in 2017": (
            "Forced entry via rear window. Controlled substances taken. "
            "Suspect matched to fingerprint records. Convicted October 2017."
        ),
        "harbour road vehicle theft 2018": (
            "Seven individuals linked to 34 thefts across Millbrook County. "
            "Five convictions secured after undercover operation. Case closed."
        ),
    }

    def ask(self, question):
        question_lower = question.lower()
        for case_key, answer in self._TRAINING_DATA.items():
            # Match on meaningful words (length > 3) from the case key.
            # Real LLMs use learned representations — but the knowledge
            # boundary is identical: absent from training data, absent from recall.
            words = [w for w in case_key.split() if len(w) > 3]
            if sum(1 for w in words if w in question_lower) >= 2:
                return answer
        return (
            "I have no information relevant to that question. "
            f"It may concern a case outside my training data "
            f"(cutoff: {self.TRAINING_CUTOFF})."
        )


llm = SimulatedLLM()


def load_case_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    path = os.path.join(project_dir, "case-files", filename)
    with open(path, "r") as f:
        return f.read()


# ---------------------------------------------------------------------------
# The queries
# ---------------------------------------------------------------------------

known_query     = "Riverside Bank Robbery 2015 — what was the outcome?"
cold_case_query = "What accelerant was used in the Millbrook Arson of 2019?"


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

print("=" * 66)
print("  MILESTONE 1")
print()
print("  Milestone:")
print("  The Intelligence Gap")
print()
print("  Case:")
print("  The Millbrook Arson — Cold Case MCA-2019-0847")
print()
print("  Article:")
print("  Part 3 — The Cold Case Files That Created RAG")
print()
print("  Investigation Status:")
print("  Department Intelligence Desk — Present Day")
print()
print("  Objective:")
print("  Demonstrate why the Detective Archive is needed.")
print("=" * 66)

print(f"""
Detective Morgan opens the department intelligence desk.
The desk was trained on Millbrook County records up to {llm.TRAINING_CUTOFF}.
For any case in that window, it answers instantly and accurately.

He tests it with a case he already knows the answer to.
""")


# --- Query 1: a case the desk knows ---

print("-" * 66)
print("  QUERY 1 — A case the desk knows")
print("-" * 66)
print()
print(f'  Question: "{known_query}"')
print()

print("  Intelligence Desk:")
print(f'    "{llm.ask(known_query)}"')

print()
print("  The desk answers without hesitation.")
print(f"  The Riverside case is in its training data.")


# --- Query 2: the cold case ---

print()
print("-" * 66)
print("  QUERY 2 — A case the desk does not know")
print("-" * 66)
print()
print(f'  Question: "{cold_case_query}"')
print()

cold_case_response = llm.ask(cold_case_query)

print("  Intelligence Desk:")
print()
print(f'    "{cold_case_response}"')
print()

print("  The desk goes quiet.")
print()
print("  Not a failure of intelligence.")
print("  A failure of information.")
print()
print(f"  The case was filed in March 2019.")
print(f"  The training cutoff was {llm.TRAINING_CUTOFF}.")
print(f"  One quarter of silence is all it took.")


# --- Open the case file from disk ---

print()
print("-" * 66)
print("  THE COLD CASE FILE — on disk")
print("-" * 66)
print()
print("  The answer was never lost.")
print("  It was filed in 2019 and has been in the archive ever since.")
print()
print("  Loading: case-files/millbrook_arson_2019.txt")
print()

case_text = load_case_file("millbrook_arson_2019.txt")
print("=" * 66)
print(case_text)
print("=" * 66)


# --- The gap ---

print()
print("-" * 66)
print("  THE GAP")
print("-" * 66)
print()
print(f'  Question: "{cold_case_query}"')
print()
print("  Intelligence Desk:")
print(f'    "{cold_case_response}"')
print()
print("  Cold Case File (on disk):")
print('    "...petroleum distillate was confirmed as the primary')
print('     accelerant, identified from residue samples recovered')
print('     at the origin point in the northwest corner..."')
print()
print("  The answer was never missing.")
print("  The system just could not see it.")

print("""
==========================

Investigation Summary

Detective Morgan's intelligence system cannot answer a question about
the Millbrook Arson of 2019 — not because the answer doesn't exist,
but because the case was filed after the system's training cutoff.
The answer sits in a cold case file on disk, untouched and inaccessible.

This is the knowledge gap. It is not a failure of reasoning. It is a
structural limitation: a language model can only work with what it was
trained on. Any information beyond the cutoff — or simply never
included — is invisible, regardless of how capable the model is.

AI Connection

Every LLM has a training cutoff. Anything beyond it — new cases,
new documents, private records, internal files — is outside the model's
reach. Retrieval-Augmented Generation (RAG) exists to bridge this gap:
it supplies the model with documents it was never trained on, at the
moment it needs them.

The Detective Archive is that supply system.
The case files are already there. The archive will make them reachable.

Continue Investigation

The archive cannot be built without first making the case files
searchable. A complete case file cannot be indexed as a single unit —
it must be broken into individually retrievable pages first.

Open:
    02_case_file_splitter.py
""")
