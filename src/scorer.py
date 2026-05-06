import streamlit as st
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def calculate_similarity(jd_text, resume_text):
    model = load_model()
    jd_embedding = model.encode([jd_text])
    resume_embedding = model.encode([resume_text])
    score = cosine_similarity(jd_embedding, resume_embedding)[0][0]
    return round(score * 100, 2)


def calculate_skill_match(jd_skills, resume_skills):
    if not jd_skills:
        return 0, []
    matched = set(jd_skills).intersection(set(resume_skills))
    score = (len(matched) / len(jd_skills)) * 100
    return round(score, 2), list(matched)
