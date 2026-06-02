---
license: cc-by-4.0
task_categories:
- text-classification
- text-generation
- table-question-answering
- question-answering
language:
- en
size_categories:
- n<1K
configs:
- config_name: easy
  data_files:
  - split: test
    path: easy.json
- config_name: medium
  data_files:
  - split: test
    path: medium.json
---

# D&D 5.2.1 SRD RAG Evaluation Dataset

A high-quality Question-Answering (QA) dataset built by the Datapizza AI Lab from the Dungeons & Dragons 5th Edition System Reference Document (SRD) version 5.2.1, designed to evaluate Retrieval Augmented Generation (RAG) systems.

## Dataset Summary

This dataset contains 56 question-answer pairs across two difficulty tiers (Easy and Medium), each designed to test different aspects of RAG system capabilities. The dataset is built from 20 markdown documents parsed from the D&D 5e SRD PDF, covering game rules, character creation, spells, monsters, and more.

### Dataset Statistics

- **Total Questions**: 56
  - **Easy Tier**: 25 questions
  - **Medium Tier**: 31 questions
- **Source Documents**: 20 markdown files from D&D 5e SRD
- **Domain**: Tabletop role-playing game rules and mechanics

## Dataset Description

### Easy Tier

The Easy tier provides a baseline that is cheap and scalable. Questions and answers are generated automatically from the source documents, making this tier ideal for establishing reproducible baselines in RAG evaluation.

**Characteristics:**
- Direct, single-source retrieval
- Straightforward factual queries
- Cost-effective to reproduce and scale

### Medium Tier

The Medium tier features questions (with optional hints) and answers that require more sophisticated reasoning. This tier reflects real evaluator intent and is more diagnostic of retrieval and reasoning gaps.

**Characteristics:**
- Multi-hop reasoning requirements
- Complex queries requiring synthesis across multiple sources
- Two question types:
  - **multi_hop**: Answered using Claude Agent Skills for multi-step reasoning
  - **wide**: Answered using LLM Retriever for wide-coverage questions

## Dataset Structure

### Data Fields

Each entry in the dataset contains the following fields:

```json
{
  "id": int,
  "question": string,
  "answer": string,
  "passages": [
    {
      "content": string,
      "document_path": string,
      "start_char": int,
      "end_char": int
    }
  ]
}
```

**Field Descriptions:**
- `id`: Unique identifier for the question-answer pair
- `question`: The question text
- `answer`: The answer text (may include citations and detailed explanations in Medium tier)
- `passages`: List of relevant passages used to answer the question
  - `content`: The text content of the passage
  - `document_path`: Path to the source document
  - `start_char`: Starting character position in the source document
  - `end_char`: Ending character position in the source document

### Data Examples

**Easy Tier Example:**

```json
{
  "id": 0,
  "question": "Compare the restoration abilities of the Pit Fiend, Planetar, Rakshasa, and Solar. What are the key differences in how their bodies react upon death and where they are revived?",
  "answer": "The key differences in how their bodies react upon death and where they are revived are as follows:\n\n**Reaction of Body upon Death:**\n* **Pit Fiend:** Its body disappears in sulfurous smoke.\n* **Rakshasa:** Its body turns to ichor.\n* **Planetar and Solar:** Their bodies disappear.\n\n**Revival Location:**\n* **Pit Fiend and Rakshasa:** They are revived somewhere in the Nine Hells.\n* **Planetar and Solar:** They are revived somewhere in Mount Celestia.",
  "passages": [
    {
      "content": "**Diabolical Restoration.** If the pit fiend dies outside the Nine Hells, its body disappears in sulfurous smoke, and it gains a new body instantly, reviving with all its Hit Points somewhere in the Nine Hells.",
      "document_path": "DND5eSRD_313-332.md",
      "start_char": 8877,
      "end_char": 9087
    }
  ]
}
```

**Medium Tier Example:**

```json
{
  "id": 0,
  "question": "How many spell slots does a character that has multiclassed a single level in every single class available in the SRD have?",
  "answer": "## Answer\n\nA character with 1 level in each of the 12 SRD classes has a total of **12 spell slots**, but they come from two separate features:\n\n### 1. Spellcasting Feature: 11 slots\n- **4** 1st-level slots\n- **3** 2nd-level slots  \n- **3** 3rd-level slots\n- **1** 4th-level slot\n\n### 2. Pact Magic Feature: 1 slot  \n- **1** 1st-level slot",
  "passages": [
    {
      "content": "## Multiclassing\nMulticlassing allows you to gain levels in multiple classes...",
      "document_path": "DND5eSRD_019-035.md",
      "start_char": 24136,
      "end_char": 31809
    }
  ]
}
```

## Dataset Creation

### Source Data

The dataset is derived from the Dungeons & Dragons 5th Edition System Reference Document 5.2.1, which is publicly available under the CC-BY-4.0 license. The SRD was split and parsed from PDF to Markdown format, resulting in 20 markdown documents.

### Data Generation Pipeline

The dataset was created using a multi-stage pipeline:

1. **Preprocessing**: PDF parsing to Markdown format
2. **Easy Tier Generation**: Automated question-answer generation from parsed documents with human expert review step
3. **Medium Tier Generation**: 
   - Human-authored questions with optional hints
   - Automated answer generation using:
     - Claude Agent Skills for multi-hop reasoning
     - LLM-as-Retriever for wide-coverage questions
4. **Postprocessing**: Format standardization and quality validation

For more details on the generation pipeline, see the [full documentation](https://datapizza.tech/it/blog/0gtzt/).

### Annotations

- **Easy Tier**: Machine-generated and human-reviewed
- **Medium Tier**: Questions are human-authored; answers are machine-generated with automated retrieval and synthesis

## Use Cases

This dataset is designed for evaluating and benchmarking RAG systems across multiple dimensions:

1. **Retrieval Quality**: Test the ability to find relevant passages from source documents
2. **Answer Quality**: Evaluate the correctness and completeness of generated answers
3. **Multi-hop Reasoning**: Assess systems' ability to synthesize information from multiple sources (Medium tier)
4. **Citation Accuracy**: Verify that systems correctly cite their sources
5. **Domain-Specific Understanding**: Evaluate performance on complex domain knowledge (TTRPG rules)

## Considerations for Using the Data

### Limitations

- **Domain-Specific**: The dataset focuses on D&D 5e rules and mechanics, which may not generalize to other domains
- **Limited Size**: With 56 questions total, the dataset is best suited for qualitative evaluation rather than large-scale quantitative benchmarking
- **Machine-Generated Answers**: While carefully validated, some answers may contain errors or inconsistencies
- **English Only**: All content is in English

### Ethical Considerations

- The source material (D&D 5e SRD) is publicly available under the CC-BY-4.0 license
- No personal or sensitive information is included in the dataset

## Additional Information

### Dataset Curators

This dataset was created as part of the RAG Evaluation research project. For more information, see the blog post and the [GitHub repository](https://github.com/datapizza-labs/rag-dataset-builder).

### Citation Information

```bibtex
@misc{datapizza_dnd_5_2_1_qa_dataset,
  author = {Singh, Raul and Chen, Ling Xuan Emma and Foresi, Francesco},
  title = {D\&D 5e SRD QA RAG Evaluation Dataset},
  year = {2025},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/datasets/datapizza-ai-lab/dnd5e-srd-qa}},
  note = {A high-quality Question-Answering dataset built from the D\&D 5th Edition System Reference Document for evaluating RAG systems}
}
```

### Acknowledgments

- Built with [`datapizza-ai`](https://github.com/datapizza-labs/datapizza-ai)
- Powered by Google Gemini and Anthropic Claude
- This work includes material from the System Reference Document 5.2.1 ("SRD 5.2.1") by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2.1 is licensed under the Creative Commons Attribution 4.0 International License, available at https://creativecommons.org/licenses/by/4.0/legalcode.