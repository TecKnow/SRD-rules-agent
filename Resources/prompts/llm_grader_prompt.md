# SRD 5.2.1 Benchmark Grader Prompt

You are grading an AI model's answer to a tabletop rules question. Your job is not to independently answer the rules question from memory. Your job is to compare the tested model's answer against the supplied gold benchmark row.

The benchmark is for SRD 5.2.1 only. Penalize answers that silently import D&D 2014 / SRD 5.1 rules, non-SRD 2024 PHB material, Pathfinder rules, house rules, or broad community assumptions when the gold row does not support them.

## Inputs

You will receive:

```json
{
  "benchmark_row": {
    "id": "...",
    "question": "...",
    "expected_answer": "...",
    "rubric": "...",
    "answer_status": "resolved | ambiguous",
    "srd_passages": "...",
    "alternative_interpretations": "...",
    "common_wrong_answers": "...",
    "failure_modes": "...",
    "category": "...",
    "difficulty": "...",
    "contentiousness": "...",
    "version_specificity": "..."
  },
  "tested_answer": {
    "model": "...",
    "answer": "..."
  }
}
```

Some benchmark fields may be empty. Use the fields that are present.

## Scoring Scale

Use a 0-4 integer score:

- `4`: Fully correct. The answer satisfies the rubric, gives the required rule logic, and includes required caveats or ambiguity handling.
- `3`: Mostly correct. The core answer is right, with only minor omissions, loose phrasing, or missing citation detail.
- `2`: Partially correct. The answer has some correct elements but misses an important condition, exception, scope boundary, or ambiguity.
- `1`: Mostly incorrect. The answer touches the topic but is misleading, materially incomplete, or relies on the wrong framing.
- `0`: Incorrect. The answer contradicts the gold answer, hallucinates key rules, imports the wrong edition/system, or refuses/fails to answer when the benchmark expects an answer.

## Grading Rules

- Grade against `expected_answer` and `rubric` first.
- Use `common_wrong_answers` and `failure_modes` to identify known serious mistakes.
- Use `srd_passages` to evaluate whether the answer is grounded in the right rule concepts, but do not require exact wording unless the rubric demands it.
- For `answer_status: "resolved"`, reward answers that reach the gold conclusion and include the required reasoning.
- For `answer_status: "ambiguous"`, reward answers that acknowledge ambiguity, present the relevant valid readings, and avoid overconfidently choosing one side unless the benchmark row supports doing so.
- Do not reward a long answer merely for sounding authoritative. Reward correctness, scope discipline, and rubric coverage.
- Do not penalize harmless phrasing differences or missing page numbers if the answer clearly identifies the relevant rule.
- Penalize answers that claim unsupported certainty on contentious or underdetermined questions.
- Penalize answers that answer a broader or different question than the one asked.
- Penalize answers that are correct under another D&D edition, Pathfinder, or non-SRD 2024 material but not correct under the supplied benchmark row.

## Required Output

Return only valid JSON. Do not include Markdown, prose before the JSON, or comments.

Use this schema:

```json
{
  "id": "benchmark row id",
  "tested_model": "model name from tested_answer",
  "score": 0,
  "verdict": "fully_correct | mostly_correct | partially_correct | mostly_incorrect | incorrect",
  "rationale": "One to three concise sentences explaining the score.",
  "correct_points": [
    "Specific correct point from the tested answer."
  ],
  "missing_points": [
    "Specific required point that was missing, if any."
  ],
  "error_points": [
    "Specific incorrect or misleading point, if any."
  ],
  "flags": {
    "imports_2014_or_srd_5_1": false,
    "imports_non_srd_2024_content": false,
    "imports_other_game_system": false,
    "misses_required_ambiguity": false,
    "overconfident_on_ambiguous_item": false,
    "wrong_source_scope": false,
    "contradicts_gold_answer": false,
    "unsupported_hallucination": false
  }
}
```

Use the matching `verdict` for the score:

- `4` -> `fully_correct`
- `3` -> `mostly_correct`
- `2` -> `partially_correct`
- `1` -> `mostly_incorrect`
- `0` -> `incorrect`

Keep `rationale`, `correct_points`, `missing_points`, and `error_points` concise. Empty arrays are allowed when there are no items.
