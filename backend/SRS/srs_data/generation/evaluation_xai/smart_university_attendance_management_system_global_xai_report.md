
# XAI Report — Intelligent SRS Generation

## 1. Generation Strategy

The SRS was generated using an instruction-tuned LLM supported by RAG.

The user provided:
- Project title: Smart University Attendance Management System
- Prepared by: Sarah Boussaidi
- Project description: The system helps universities manage student attendance using a web and mobile platform. Teachers can create sessions, students can check in, administrators can manage courses, and the system generates attendance reports.
- Functional needs: ['Student registration and authentication', 'Teacher authentication', 'Course and class management', 'Attendance session creation', 'Student check-in', 'Attendance report generation', 'Admin dashboard']
- Non-functional needs: ['Security', 'Performance', 'Availability', 'Usability', 'Reliability', 'Maintainability']

## 2. RAG Explanation

The RAG engine retrieved examples from previous SRS intelligence outputs:
- High-quality requirements
- Improved requirements from LLM rewriting
- Requirements scored by multimodal quality analysis

Average RAG similarity score:
0.1174

RAG quality distribution:
retrieval_quality
ACCEPTABLE_RETRIEVAL    10

## 3. Generation Evaluation

Section coverage:
100.0%

Total generated requirements:
144

Average generated requirement quality:
93.68

Generated requirement quality distribution:
generated_quality_label
STRONG_GENERATED_REQUIREMENT        124
ACCEPTABLE_GENERATED_REQUIREMENT     20

## 4. Final Generation Score

Final generation score:
81.89

Final generation label:
GOOD_GENERATION

## 5. Explainability Summary

The generated SRS is explainable through:
1. RAG evidence per section.
2. Quality explanations per generated requirement.
3. Section-level diagnostics.
4. Final generation score decomposition.

This provides transparency over why the generated SRS is considered strong, acceptable, or needing improvement.
