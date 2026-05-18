import csv
from pathlib import Path

from .utils import (
    SRS_OUTPUTS_DIR,
    SRS_GENERATION_DIR,
    slugify,
    get_project_timestamp,
    create_zip_package,
    safe_read_csv,
)


STANDARD_SECTIONS = [
    "Introduction",
    "General Description",
    "Functional Requirements",
    "Non-Functional Requirements",
    "Interface Requirements",
    "Performance Requirements",
    "Security Requirements",
    "Acceptance Criteria",
    "Risks and Assumptions",
    "Conclusion",
]


def normalize_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    value = str(value)
    parts = value.replace(";", "\n").replace(",", "\n").split("\n")
    return [p.strip("-• ").strip() for p in parts if p.strip("-• ").strip()]

def clean_requirement_text(text):
    text = str(text).strip()
    text = text.replace("**", "")
    text = text.replace("Requirement:", "")
    text = text.replace("Description:", "")
    text = text.strip(" -•:\n\t")

    forbidden = [
        "functional needs",
        "non-functional needs",
        "constraints",
        "expected users",
        "target users",
        "security",
        "performance",
        "availability",
        "usability",
        "reliability",
        "maintainability",
        "data privacy",
        "scalability",
    ]

    if text.lower() in forbidden:
        return ""

    if len(text.split()) < 4:
        return ""

    return text


def to_professional_fr(text):
    text = clean_requirement_text(text)
    if not text:
        return ""

    lower = text.lower()

    if "registration" in lower or "authentication" in lower:
        return f"The system shall provide secure registration and authentication functionality for the relevant users."

    if "report" in lower:
        return f"The system shall generate and export operational reports in supported formats such as PDF or CSV."

    if "dashboard" in lower:
        return f"The system shall provide an administrative dashboard for monitoring key system data, activities, and performance indicators."

    if "alert" in lower:
        return f"The system shall generate automatic alerts when predefined operational conditions are reached."

    if "route" in lower:
        return f"The system shall support planning and optimization of collection routes based on operational data."

    if "monitoring" in lower or "status" in lower:
        return f"The system shall monitor relevant system entities and display their current status to authorized users."

    return f"The system shall {text[0].lower() + text[1:] if text else text}."


def build_requirement(requirement_id, text, req_type="FR"):
    text = text.strip().rstrip(".")
    if not text.lower().startswith(("the system shall", "the system must", "users shall", "administrators shall")):
        text = f"The system shall {text[0].lower() + text[1:] if text else text}"
    return {
        "requirement_id": requirement_id,
        "requirement_type": req_type,
        "requirement_text": text + ".",
    }


def generate_srs_document(project_info):
    project_name = project_info.get("project_name") or project_info.get("title") or "Generated SRS Project"
    prepared_by = project_info.get("prepared_by") or project_info.get("author") or "Project author"
    description = project_info.get("description") or project_info.get("project_description") or ""

    functional_needs = normalize_list(project_info.get("functional_needs"))
    non_functional_needs = normalize_list(project_info.get("non_functional_needs"))
    target_users = normalize_list(project_info.get("target_users"))
    constraints = normalize_list(project_info.get("constraints"))

    project_slug = slugify(project_name)
    timestamp = get_project_timestamp()

    requirements = []

    req_index = 1
    for need in functional_needs:
        requirements.append(build_requirement(f"FR-{req_index:03d}", need, "FR"))
        req_index += 1

    nfr_index = 1
    for need in non_functional_needs:
        requirements.append(build_requirement(f"NFR-{nfr_index:03d}", need, "NFR"))
        nfr_index += 1

    md = f"""# Software Requirements Specification

## Cover Page

**Project title:** {project_name}  
**Prepared by:** {prepared_by}  
**Generated on:** {timestamp}  
**Generation method:** Prompt-based SRS generation supported by previous SRS intelligence outputs, RAG references, quality scoring and XAI.

---

## Table of Contents

1. Introduction  
2. General Description  
3. Functional Requirements  
4. Non-Functional Requirements  
5. Interface Requirements  
6. Performance Requirements  
7. Security Requirements  
8. Acceptance Criteria  
9. Risks and Assumptions  
10. Conclusion  
11. References  

---

# 1. Introduction

## 1.1 Purpose

This Software Requirements Specification describes the functional and non-functional requirements of **{project_name}**. The objective is to define a clear, structured, testable and professional specification that can guide design, development, validation and stakeholder communication.

## 1.2 Project Description

{description}

## 1.3 Target Users

{chr(10).join([f"- {u}" for u in target_users]) if target_users else "- End users\n- Administrators\n- System stakeholders"}

---

# 2. General Description

The proposed system provides a structured digital solution based on the project needs described by the user. It is designed to support reliability, usability, maintainability, performance, and security while keeping the requirements clear and traceable.

## 2.1 Constraints

{chr(10).join([f"- {c}" for c in constraints]) if constraints else "- The system shall respect technical, security and usability constraints defined by stakeholders."}

---

# 3. Functional Requirements

"""

    if functional_needs:
        for req in [r for r in requirements if r["requirement_type"] == "FR"]:
            md += f"- **{req['requirement_id']}**: {req['requirement_text']}\n"
    else:
        md += "- **FR-001**: The system shall provide the main business features described in the project scope.\n"

    md += """

---

# 4. Non-Functional Requirements

"""

    if non_functional_needs:
        for req in [r for r in requirements if r["requirement_type"] == "NFR"]:
            md += f"- **{req['requirement_id']}**: {req['requirement_text']}\n"
    else:
        md += "- **NFR-001**: The system shall provide acceptable performance, security, usability and maintainability.\n"

    md += f"""

---

# 5. Interface Requirements

- The system shall provide a clear user interface adapted to the identified target users.
- The system shall validate user inputs before processing.
- The system shall provide meaningful error messages when invalid data is submitted.

---

# 6. Performance Requirements

- The system shall respond to standard user operations within an acceptable response time.
- The system shall support concurrent usage according to the expected project scale.
- The system shall maintain stable performance during normal operational load.

---

# 7. Security Requirements

- The system shall protect sensitive user and project data.
- The system shall implement authentication and role-based access where needed.
- The system shall prevent unauthorized access to protected resources.

---

# 8. Acceptance Criteria

- All major functional requirements shall be implemented and validated.
- All critical non-functional requirements shall be measurable and testable.
- The system shall provide outputs that are understandable by the intended users.
- The system shall be reviewed by stakeholders before final validation.

---

# 9. Risks and Assumptions

## 9.1 Risks

- Some requirements may need further clarification from stakeholders.
- Performance constraints may change depending on deployment infrastructure.
- Security requirements may require additional validation depending on the target environment.

## 9.2 Assumptions

- The project description provided by the user is considered the primary source of truth.
- Functional and non-functional needs can be refined during future iterations.
- The SRS can be regenerated when new project information becomes available.

---

# 10. Conclusion

This SRS provides a complete and structured foundation for the development of **{project_name}**. It organizes the project scope, functional requirements, non-functional requirements, constraints, risks, and acceptance criteria into a professional specification that can be used for communication, implementation, and evaluation.

---

# 11. References

- User project prompt
- Previous SRS intelligence outputs
- Requirement quality scoring outputs
- RAG references from historical SRS datasets
- XAI reports and generation evaluation files
"""

    md_path = SRS_OUTPUTS_DIR / f"{project_slug}_srs.md"
    html_path = SRS_OUTPUTS_DIR / f"{project_slug}_srs.html"
    csv_path = SRS_OUTPUTS_DIR / f"{project_slug}_generated_requirements.csv"
    docx_path = SRS_OUTPUTS_DIR / f"{project_slug}_srs.docx"

    md_path.write_text(md, encoding="utf-8")

    html = md.replace("\n", "<br>")
    html_path.write_text(f"<html><body>{html}</body></html>", encoding="utf-8")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement_id", "requirement_type", "requirement_text"])
        writer.writeheader()
        writer.writerows(requirements)

    try:
        from docx import Document

        doc = Document()
        for line in md.splitlines():
            if line.startswith("# "):
                doc.add_heading(line.replace("# ", ""), level=1)
            elif line.startswith("## "):
                doc.add_heading(line.replace("## ", ""), level=2)
            elif line.startswith("### "):
                doc.add_heading(line.replace("### ", ""), level=3)
            elif line.strip() == "---":
                doc.add_paragraph("")
            else:
                doc.add_paragraph(line)
        doc.save(docx_path)
    except Exception:
        docx_path = None

    files = [md_path, html_path, csv_path]
    if docx_path:
        files.append(docx_path)

    zip_path = create_zip_package(project_slug, files)

    return {
        "status": "success",
        "message": "SRS generated successfully.",
        "project_name": project_name,
        "prepared_by": prepared_by,
        "generated_requirements_count": len(requirements),
        "sections": STANDARD_SECTIONS,
        "markdown": md,
        "files": {
            "markdown": str(md_path),
            "html": str(html_path),
            "csv": str(csv_path),
            "docx": str(docx_path) if docx_path else None,
            "zip": str(zip_path),
        },
        "download_file": str(zip_path),
    }