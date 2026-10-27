"""
X Post Generator — generate 3 tweet variants on any topic with AI.
Run: streamlit run app.py
"""

import json
import os
import re

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MAX_LEN = 280
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")

LANGUAGES = {"English": "English", "Українська": "Ukrainian", "Polski": "Polish"}
TONES = ["Informative", "Funny", "Provocative", "Motivational", "Storytelling"]


def build_prompt(topic: str, language: str, tone: str, hashtags: bool, emojis: bool) -> str:
    return f"""Write 3 different posts for X (Twitter) about this topic: "{topic}".

Rules:
- Language: {language}
- Tone: {tone}
- Each post MUST be under {MAX_LEN} characters
- Each post should use a different angle or hook
- Hashtags: {"add 1-2 relevant hashtags" if hashtags else "no hashtags"}
- Emojis: {"a few emojis are fine" if emojis else "no emojis"}

Return ONLY a JSON array of 3 strings, nothing else.
Example: ["post one", "post two", "post three"]"""


def parse_posts(text: str) -> list[str]:
    """Extract the JSON array from the model reply, even if extra text slipped in."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError("Model did not return a JSON array.")
    posts = json.loads(match.group(0))
    return [str(p).strip() for p in posts if str(p).strip()][:3]


def generate_posts(api_key: str, topic: str, language: str, tone: str,
                   hashtags: bool, emojis: bool) -> list[str]:
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": build_prompt(topic, language, tone, hashtags, emojis)}],
    )
    return parse_posts(response.content[0].text)


# ---------------- UI ----------------
st.set_page_config(page_title="X Post Generator", page_icon="✍️")
st.title("✍️ X Post Generator")
st.caption("Enter a topic and get 3 ready-to-post tweet variants.")

with st.sidebar:
    st.header("Settings")
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.text_input("Anthropic API key", type="password")
    language = st.selectbox("Language", list(LANGUAGES))
    tone = st.selectbox("Tone", TONES)
    hashtags = st.toggle("Hashtags", value=True)
    emojis = st.toggle("Emojis", value=False)

topic = st.text_area("Topic", placeholder="e.g. how AI helps freelancers save time")

if st.button("Generate", type="primary", use_container_width=True):
    if not api_key:
        st.error("Add your API key in the sidebar or in the .env file.")
    elif not topic.strip():
        st.warning("Enter a topic first.")
    else:
        with st.spinner("Writing posts..."):
            try:
                st.session_state.posts = generate_posts(
                    api_key, topic.strip(), LANGUAGES[language], tone, hashtags, emojis
                )
            except Exception as e:
                st.error(f"Something went wrong: {e}")

for i, post in enumerate(st.session_state.get("posts", []), start=1):
    length = len(post)
    status = "✅" if length <= MAX_LEN else "⚠️ too long"
    st.subheader(f"Variant {i}")
    st.code(post, language=None, wrap_lines=True)  # code block has a built-in copy button
    st.caption(f"{length}/{MAX_LEN} characters {status}")
