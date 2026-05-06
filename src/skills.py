SKILLS_DB = [
    # Core Programming
    "python",
    "java",
    "javascript",
    "typescript",
    "sql",
    "bash",
    "linux",

    # Data Science / ML
    "machine learning",
    "deep learning",
    "nlp",
    "bert",
    "transformers",
    "hugging face",
    "langchain",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "xgboost",
    "lightgbm",
    "opencv",
    "matplotlib",
    "seaborn",
    "mlflow",

    # Data Engineering
    "pyspark",
    "hadoop",
    "airflow",

    # Databases
    "postgresql",
    "mongodb",
    "redis",

    # Cloud / DevOps
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "jenkins",
    "ci/cd",

    # Backend / APIs
    "flask",
    "fastapi",
    "django",
    "spring boot",
    "graphql",
    "rest api",
    "microservices",

    # Frontend
    "react",
    "angular",
    "vue",
    "next.js",
    "node.js",
    "html",
    "css",

    # QA / Testing
    "selenium",
    "playwright",
    "pytest",
    "junit",
    "testng",
    "postman",
    "jira",

    # BI / Reporting
    "power bi",
    "tableau",
    "excel",

    # Version Control
    "git",
    "github",

    # Visualization / Design
    "streamlit",
    "figma",

    # Methodologies
    "agile",
    "scrum",
    "microservices",
    "object oriented programming",
    "data structures",
    "algorithms",
]


def extract_skills(text):
    text = text.lower()

    matched_skills = []

    for skill in SKILLS_DB:
        if skill in text:
            matched_skills.append(skill)

    return matched_skills