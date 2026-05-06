import os
import pandas as pd

from src.parser import extract_text
from src.skills import extract_skills
from src.experience import extract_experience
from src.scorer import (
    calculate_similarity,
    calculate_skill_match
)


RESUME_FOLDER = "resumes"
JD_FOLDER = "jds"
OUTPUT_FOLDER = "output"

OUTPUT_FILE = (
    "resume_screening_results.xlsx"
)


def load_files(folder):
    data = {}

    for file_name in os.listdir(folder):
        file_path = os.path.join(
            folder,
            file_name
        )

        if os.path.isfile(file_path):
            text = extract_text(file_path)

            if text.strip():
                data[file_name] = text

    return data


def main():
    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    resumes = load_files(
        RESUME_FOLDER
    )

    job_descriptions = load_files(
        JD_FOLDER
    )

    results = []

    for jd_name, jd_text in (
        job_descriptions.items()
    ):
        jd_skills = extract_skills(
            jd_text
        )

        for (
            resume_name,
            resume_text
        ) in resumes.items():

            resume_skills = (
                extract_skills(
                    resume_text
                )
            )

            years_of_experience = (
                extract_experience(
                    resume_text
                )
            )

            semantic_score = (
                calculate_similarity(
                    jd_text,
                    resume_text
                )
            )

            (
                skill_score,
                matched_skills
            ) = calculate_skill_match(
                jd_skills,
                resume_skills
            )

            final_score = round(
                semantic_score * 0.75
                + skill_score * 0.25,
                2
            )

            results.append({
                "Job Description":
                    jd_name,

                "Resume":
                    resume_name,

                "Semantic Score (%)":
                    semantic_score,

                "Skill Match Score (%)":
                    skill_score,

                "Final Score (%)":
                    final_score,

                "JD Skills":
                    ", ".join(jd_skills),

                "Resume Skills":
                    ", ".join(
                        resume_skills
                    ),

                "Matched Skills":
                    ", ".join(
                        matched_skills
                    ),

                "Years of Experience":
                    years_of_experience
            })

    df = pd.DataFrame(results)

    df = df.sort_values(
        by=[
            "Job Description",
            "Final Score (%)"
        ],
        ascending=[True, False]
    )

    output_path = os.path.join(
        OUTPUT_FOLDER,
        OUTPUT_FILE
    )

    df.to_excel(
        output_path,
        index=False
    )

    print(
        f"Results saved to: "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()