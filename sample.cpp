What we are doing, in simple words
The problem

Doctors often prescribe medicines without checking everything about the patient: their other medicines, allergies, diseases and age. This can cause harm. Examples are two medicines that are dangerous together, a medicine the patient is allergic to, or the same medicine given twice under different brand names.

PS4 asks us to build a system that catches these mistakes before the patient takes the medicine, and explains why.

Our solution: MedGuard

A web app for doctors and pharmacists.

The doctor enters the patient details (age, weight, diseases, allergies, current medicines) and the new prescription.
The system converts brand names into real medicine names. For example, Dolo and Crocin are both paracetamol.
It checks for five kinds of problems:
dangerous medicine + medicine combinations
a medicine that is unsafe for the patient's disease
duplicate medicines
wrong dose
allergy conflicts
It shows warnings with a severity color, a clear reason, and a suggested action.
Where the AI comes in
Known problems come from a trusted database of rules and interactions, and every rule has a source. This part is reliable.
Unknown pairs are where our AI model helps. Databases don't list every possible pair of medicines, so the model predicts the risk for pairs that aren't listed. It reads the structure of both medicines (their molecule graphs) and estimates whether they may interact.
The AI is only a second opinion. It is labeled "predicted, lower confidence" and never overrides the database.
A language model (LLM) writes the warnings in plain sentences, but only from facts the system found. It never decides what is safe.
What the user sees

A clean screen where you type the patient and the medicines, then get a report of colored warning cards. Each card has a "Why?" button. There is also a graph showing which medicines clash, and a picture of the molecules with the important atoms highlighted for AI predictions.

Why this can win
It covers every requirement in PS4.
Warnings are explained, which PS4 specifically asks for.
It works with Indian brand names, which is realistic and rare in other projects.
The AI is tested honestly, including on medicines it has never seen.