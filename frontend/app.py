"""
Chat UI.  Start the API first (uvicorn app.api.main:app --port 8000), then:

    streamlit run frontend/app.py
"""
import os
import re

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

SAMPLE_QUESTIONS = [
    "How much parental leave do I get?",
    "What is the anti-harassment policy?",
    "What is the salary band for a Senior Software Engineer L5?",
    "How many performance improvement plans ended in separation?",
    "How many critical vulnerabilities are open?",
]

DEMO_USERS = [
    {"Username": "alice_employee", "Role": "employee"},
    {"Username": "gina_manager", "Role": "manager"},
    {"Username": "carol_engineer", "Role": "engineer"},
    {"Username": "bob_hr", "Role": "hr"},
    {"Username": "dave_finance", "Role": "finance"},
    {"Username": "erin_security", "Role": "security"},
    {"Username": "frank_admin", "Role": "admin"},
]

ROLE_COLORS = {"employee": "gray", "manager": "blue", "engineer": "green", "hr": "orange",
               "finance": "violet", "security": "red", "admin": "rainbow"}
DEPT_COLORS = {"general": "gray", "hr": "orange", "engineering": "green",
               "security": "red", "finance": "violet"}

st.set_page_config(page_title="Enterprise Knowledge Assistant", page_icon="🔐")

for key, default in {"token": None, "username": None, "role": None,
                     "departments": [], "messages": []}.items():
    st.session_state.setdefault(key, default)


# ---------------- helpers ----------------

def clean(text: str) -> str:
    """Make model output safe and tidy for display."""
    # some models write citations as 【3†L1-L4】 or 【3】: normalise to [3]
    text = re.sub(r"【(\d+)(?:†[^】]*)?】", r"[\1]", text)
    # Streamlit treats $...$ as math, which garbles prices like $124,000 - $162,000
    return text.replace("$", r"\$")


def logout():
    for key in ("token", "username", "role"):
        st.session_state[key] = None
    st.session_state.departments = []
    st.session_state.messages = []


def login(username: str, password: str):
    try:
        r = requests.post(f"{API_URL}/auth/login",
                          json={"username": username, "password": password}, timeout=20)
    except requests.RequestException:
        st.error("Cannot reach the API. Is `uvicorn` running?")
        return
    if r.status_code != 200:
        st.error("Invalid username or password.")
        return
    data = r.json()
    departments = []
    try:   # which document areas this role can read (shown in the sidebar)
        me = requests.get(f"{API_URL}/me",
                          headers={"Authorization": f"Bearer {data['access_token']}"}, timeout=10)
        if me.status_code == 200:
            departments = me.json().get("departments", [])
    except requests.RequestException:
        pass
    st.session_state.update(token=data["access_token"], username=data["username"],
                            role=data["role"], departments=departments, messages=[])
    st.rerun()


def ask(question: str):
    """Call the API. The server decides what this user may see from the token."""
    fail = {"found": False, "sources": [], "latency_ms": 0}
    try:
        r = requests.post(f"{API_URL}/chat", json={"question": question},
                          headers={"Authorization": f"Bearer {st.session_state.token}"},
                          timeout=120)
    except requests.RequestException:
        return {**fail, "answer": "Cannot reach the API. Is `uvicorn` running?"}
    if r.status_code == 401:
        logout()
        st.warning("Your session expired. Please log in again.")
        st.rerun()
    if r.status_code == 422:
        return {**fail, "answer": "Please type a longer question (3 to 1000 characters)."}
    if r.status_code != 200:
        return {**fail, "answer": f"Server error ({r.status_code}). Please try again."}
    return r.json()


def render_message(msg):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and not msg.get("found", True):
            st.info(clean(msg["content"]), icon="🔍")
        else:
            st.markdown(clean(msg["content"]))
        if msg.get("sources"):
            with st.expander(f"Sources ({len(msg['sources'])})"):
                for s in msg["sources"]:
                    color = DEPT_COLORS.get(s["department"], "gray")
                    st.markdown(f"**[{s['n']}]** {clean(s['title'])} › {clean(s['section'])}  \n"
                                f":{color}-badge[{s['department']}] `{s['file']}`")
        if msg.get("latency_ms"):
            st.caption(f"Answered in {msg['latency_ms'] / 1000:.1f} s")


# ---------------- logged-out view ----------------

if st.session_state.token is None:
    st.title("🔐 Enterprise Knowledge Assistant")
    st.markdown(
        "Ask questions about company policies, benefits, engineering and security. "
        "Answers come **only from documents your role is allowed to read**, with sources.")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary")
    if submitted and u and p:
        login(u, p)
    with st.expander("Demo accounts"):
        st.table(DEMO_USERS)
        st.caption("Password: the DEMO_PASSWORD value from your .env file (default Demo@12345).")
    st.stop()

# ---------------- sidebar (logged in) ----------------

with st.sidebar:
    st.header("Account")
    color = ROLE_COLORS.get(st.session_state.role, "gray")
    st.markdown(f"**{st.session_state.username}**  \nRole: :{color}-badge[{st.session_state.role}]")
    if st.session_state.departments:
        st.markdown("**Documents you can read**")
        st.markdown(" ".join(f":{DEPT_COLORS.get(d, 'gray')}-badge[{d}]"
                             for d in st.session_state.departments))
    col1, col2 = st.columns(2)
    if col1.button("Log out", use_container_width=True):
        logout()
        st.rerun()
    if col2.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("Try a question")
    st.caption("Ask the same question as different users to see access control at work.")
    for i, q in enumerate(SAMPLE_QUESTIONS):
        if st.button(q, key=f"sample{i}", use_container_width=True):
            st.session_state.pending = q

# ---------------- main chat ----------------

st.title("🔐 Enterprise Knowledge Assistant")
st.caption("Answers come only from documents your role is allowed to read, with sources.")

if not st.session_state.messages:
    st.info("👋 Type a question below, or pick a sample question from the sidebar.")

for m in st.session_state.messages:
    render_message(m)

question = st.chat_input("Ask about company policies, benefits, engineering or security...")
question = question or st.session_state.pop("pending", None)

if question:
    user_msg = {"role": "user", "content": question}
    st.session_state.messages.append(user_msg)
    render_message(user_msg)
    with st.spinner("Searching documents..."):
        res = ask(question)
    bot_msg = {"role": "assistant", "content": res["answer"], "found": res.get("found", False),
               "sources": res.get("sources", []), "latency_ms": res.get("latency_ms", 0)}
    st.session_state.messages.append(bot_msg)
    render_message(bot_msg)
