import streamlit as st
import time
import json
import os
from datetime import datetime
from template_manager import load_templates
from prompt_engine import generate_prompt
from chaining import run_chaining
from firebase_auth import signup, login, log_prompt_to_firebase, db

st.set_page_config(page_title="AutoPrompt Builder")
st.title("🧠 AutoPrompt Builder")

# 🔐 Login Section
REMEMBER_FILE = "remembered_user.txt"

# Auto-login if remembered email exists
if "user" not in st.session_state:
    st.session_state.user = None
    if os.path.exists(REMEMBER_FILE):
        with open(REMEMBER_FILE, "r") as f:
            remembered_email = f.read().strip()
            if remembered_email:
                st.session_state.user = {"email": remembered_email}

# If still not logged in, show login form
if st.session_state.user is None:
    st.title("🔐 AutoPrompt Builder Login")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        remember = st.checkbox("Remember Me (for this device only)")

        if st.button("Login"):
            if not email or not password:
                st.warning("⚠️ Please enter both email and password.")
            else:
                try:
                    user = login(email, password)
                    st.session_state.user = user
                    st.success("✅ Logged in successfully!")

                    if remember:
                        with open(REMEMBER_FILE, "w") as f:
                            f.write(email)

                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")

    with tab2:
        email_signup = st.text_input("New Email")
        pass_signup = st.text_input("New Password", type="password")

        if st.button("Sign Up"):
            if not email_signup or not pass_signup:
                st.warning("⚠️ Please enter both email and password to sign up.")
            else:
                try:
                    signup(email_signup, pass_signup)
                    st.success("✅ Account created. You can now log in.")
                except Exception as e:
                    st.error(f"Signup failed: {e}")

    st.stop()


# 🚪 Logout button (after successful login)
st.sidebar.markdown("### 👤 Logged in as:")
st.sidebar.code(st.session_state.user["email"])
if st.sidebar.button("🚪 Logout"):
    st.session_state.user = None
    if os.path.exists("remembered_user.txt"):
        os.remove("remembered_user.txt")
    st.rerun()

# ✅ Setup clear_prompt flag for reset logic
if "clear_chaining" not in st.session_state:
    st.session_state.clear_chaining = False
if "clear_prompt" not in st.session_state:
    st.session_state.clear_prompt = False


# Initialize session state
if "last_response" not in st.session_state:
    st.session_state["last_response"] = ""
if "full_prompt" not in st.session_state:
    st.session_state["full_prompt"] = ""
with st.expander("🧠 AutoPrompt Builder", expanded=False):
    user_id = st.session_state.user.get("uid") or st.session_state.user["email"].replace(".", "_")
    templates = load_templates(user_id)
    template_choice = st.selectbox("Choose Industry Template", list(templates.keys()))
    template = templates[template_choice]

    with st.expander("📄 View & Customize Template"):
        st.code(template.get("structure", "No structure found"), language='markdown')

        st.markdown("✍️ Customize Template")
        edited_template = st.text_area("Edit Template Format", value=template.get("structure", ""), height=120)

        new_template_name = st.text_input("📁 Save As New Template Name (without .json)")

        if st.button("💾 Save Template"):
            if new_template_name.strip() == "":
                st.warning("Please enter a name for the new template.")
            else:
                new_template_data = {"structure": edited_template}
                user_id = st.session_state.user.get("uid") or st.session_state.user["email"].replace(".", "_")
                try:
                    db.child("templates").child(user_id).child(new_template_name.strip()).set(new_template_data)
                    st.success(f"Template saved as '{new_template_name.strip()}' in Firebase.")
                except Exception as e:
                    st.error(f"Failed to save template: {e}")


    # If clear was triggered in last run, reset all prompt inputs
    if st.session_state.get("clear_prompt", False):
        st.session_state["role"] = ""
        st.session_state["audience"] = ""
        st.session_state["tone"] = "Formal"
        st.session_state["intent"] = ""
        st.session_state["last_response"] = ""
        st.session_state["full_prompt"] = ""

        # Clear few-shot examples
        for key in list(st.session_state.keys()):
            if key.startswith("ex_input_") or key.startswith("ex_output_"):
                del st.session_state[key]

        st.session_state["clear_prompt"] = False

    # Prompt Input Section
    role = st.text_input("Enter Role (e.g., HR, Lawyer)", key="role")
    audience = st.text_input("Enter Audience (e.g., Candidate, Client)", key="audience")
    tone = st.selectbox("Tone", ["Formal", "Casual", "Neutral"], key="tone")
    intent = st.text_area("Intent/Task Description", key="intent")

    # Few-Shot Examples
    st.markdown("### 🧠 Optional: Few-Shot Examples")
    example_count = st.number_input("How many examples?", min_value=0, max_value=5, value=0)

    few_shot_examples = []
    for i in range(example_count):
        input_example = st.text_area(f"Example {i+1} - Input", key=f"ex_input_{i}")
        output_example = st.text_area(f"Example {i+1} - Expected Output", key=f"ex_output_{i}")
        if input_example and output_example:
            few_shot_examples.append((input_example, output_example))

    # Parameter Tuning
    st.markdown("### ⚙️ Parameter Tuning")
    temperature = st.slider("Temperature (Controls creativity)", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
    max_tokens = st.number_input("Max Tokens (Controls output length)", min_value=10, max_value=1000, value=300)

    if st.button("Generate Prompt"):
        if not role or not audience or not intent:
            st.warning("⚠️ Please fill in all fields: Role, Audience, and Intent are required.")
        else:
            base_prompt = edited_template.format(role=role, audience=audience, tone=tone, intent=intent)

            few_shot_prompt = ""
            for idx, (ex_input, ex_output) in enumerate(few_shot_examples):
                few_shot_prompt += f"Example {idx+1}:\nInput: {ex_input}\nOutput: {ex_output}\n\n"

            full_prompt = few_shot_prompt + "Now complete the task:\n" + base_prompt

            result = generate_prompt(full_prompt, temperature=temperature, max_tokens=max_tokens)

            # Save to session
            st.session_state["full_prompt"] = full_prompt
            st.session_state["last_response"] = result

            # Log to Firebase
            log_prompt_to_firebase(
                email=st.session_state.user["email"],
                prompt=full_prompt,
                response=result,
                meta={
                    "role": role,
                    "audience": audience,
                    "tone": tone,
                    "intent": intent,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "rating": None,
                    "feedback": None,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                uid = st.session_state.user["email"].replace(".", "_")

            )
            

    # Show AI Response
    if st.session_state.get("last_response"):
        st.subheader("🧠 AI Response:")
        st.write(st.session_state["last_response"])

        st.markdown("### 📌 Generated Prompt Sent to AI:")
        st.code(st.session_state["full_prompt"], language='markdown')

        # Export Options
        st.markdown("### 📤 Export Prompt & Response")
        export_format = st.radio("Choose export format:", ["TXT", "JSON"], horizontal=True)

        export_data = {
            "role": role,
            "audience": audience,
            "tone": tone,
            "intent": intent,
            "prompt": st.session_state["full_prompt"],
            "response": st.session_state["last_response"]
        }

        if export_format == "TXT":
            txt_content = f"""Role: {role}
Audience: {audience}
Tone: {tone}
Intent: {intent}

--- Prompt Sent to AI ---
{st.session_state["full_prompt"]}

--- AI Response ---
{st.session_state["last_response"]}
"""
            st.download_button("⬇️ Download .txt file", data=txt_content, file_name="prompt_output.txt", mime="text/plain")

        elif export_format == "JSON":
            json_content = json.dumps(export_data, indent=2)
            st.download_button("⬇️ Download .json file", data=json_content, file_name="prompt_output.json", mime="application/json")

        # Rating & Feedback
        st.markdown("### 📊 Rate the Response")
        rating = st.slider("⭐ Rate this response (1 = poor, 5 = excellent)", 1, 5, value=3, key="rating_slider")
        feedback = st.text_area("💬 Optional: What did you like or dislike?", key="feedback_text")

        if st.button("Submit Rating", key="submit_rating_btn"):
            st.success(f"✅ Thank you! You rated this response {rating} star(s).")
            if feedback:
                st.markdown("📝 Your feedback:")
                st.write(feedback)

    # Clear Inputs
    if st.button("🧹 Clear Prompt Input & Output"):
        st.session_state.clear_prompt = True
        st.rerun()
# 🔗 Prompt chaining section


st.markdown("---")
st.title("🔗 Prompt Chaining")

with st.expander("🔗 Prompt Chaining", expanded=False):
    # ✅ Clear Chaining
    if st.session_state.get("clear_chaining", False):
        for i in range(len(st.session_state.get("chaining_steps", []))):
            step_key = f"chaining_step_{i}"
            if step_key in st.session_state:
                st.session_state[step_key] = ""
        st.session_state.chaining_steps = [""]
        st.session_state["initial_input"] = ""
        st.session_state["chain_outputs"] = []
        st.session_state["chain_rating"] = 3
        st.session_state["chain_feedback"] = ""
        st.session_state["chaining_feedback_submitted"] = False
        st.session_state.clear_chaining = False

    # Initialize chaining steps
    if "chaining_steps" not in st.session_state or not st.session_state.chaining_steps:
        st.session_state.chaining_steps = [""]

    # 🧩 Build Prompt Chain
    st.subheader("🧩 Build Your Prompt Chain")
    st.markdown("Define a sequence of prompts. Each step will take the output of the previous step as input.")

    for i in range(len(st.session_state.chaining_steps)):
        key = f"chaining_step_{i}"
        default_value = st.session_state.get(key, "")
        st.session_state.chaining_steps[i] = st.text_area(
            f"Step {i+1} Prompt",
            value=default_value,
            key=key,
            height=100
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Step", key=f"add_step_button_{len(st.session_state.chaining_steps)}"):
            st.session_state.chaining_steps.append("")
            st.rerun()
    with col2:
        if len(st.session_state.chaining_steps) > 1:
            if st.button("➖ Remove Last Step", key=f"remove_step_button_{len(st.session_state.chaining_steps)}"):
                st.session_state.chaining_steps.pop()
                st.rerun()

    # 📝 Initial input
    initial_input = st.text_area(
        "📝 Initial Input",
        value=st.session_state.get("initial_input", ""),
        key="initial_input",
        height=100
    )

    # ⚙️ Parameters
    st.markdown("### ⚙️ Generation Parameters")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, step=0.05, key="chaining_temp")
    max_tokens = st.number_input("Max Tokens", 10, 1000, 300, key="chaining_tokens")

    # ▶️ Run chaining
    if st.button("▶️ Run Chaining", key="run_chain_button"):
        steps = st.session_state.chaining_steps

        if not initial_input.strip() or any(not step.strip() for step in steps):
            st.warning("⚠️ Please fill in the initial input and all chaining steps before running.")
        else:
            all_outputs = run_chaining(steps, initial_input, temperature, max_tokens)
            st.session_state["chain_outputs"] = all_outputs
            st.session_state["chaining_feedback_submitted"] = False

            # ✅ Build chain_steps
            chain_steps = []
            for idx, (step, prompt, result) in enumerate(all_outputs):
                chain_steps.append({
        "step": step or f"Step {idx+1}",
        "prompt": prompt or "",
        "response": result or ""
    })


            # ✅ Log immediately to Firebase
            log_prompt_to_firebase(
                email=st.session_state.user["email"],
                prompt=initial_input,
                response=all_outputs[-1][2],
                meta={
                    "role": role,
                    "audience": audience,
                    "tone": tone,
                    "intent": intent,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timestamp":datetime.now().isoformat()
                },
                chain_steps=chain_steps,
                uid=st.session_state.user["email"].replace(".", "_")
            )

    # ✅ Show Chained Output
    if st.session_state.get("chain_outputs"):
        all_outputs = st.session_state["chain_outputs"]

        st.subheader("🔗 Chained Output")
        for idx, (step, prompt, result) in enumerate(all_outputs):
            with st.expander(f"🔹 Step {idx+1}: {step}", expanded=False):
                st.markdown("🧾 Prompt:")
                st.code(prompt, language="markdown")
                st.markdown("🧠 Output:")
                st.write(result)

        # 📤 Export
        st.markdown("### 📤 Export Chaining Result")
        export_chain_format = st.radio("Choose export format:", ["TXT", "JSON"], horizontal=True, key="chain_export_format")

        chain_steps = [
            {"step": step, "prompt": prompt, "response": result}
            for step, prompt, result in all_outputs
        ]

        chain_export = {
            "initial_input": initial_input,
            "steps": chain_steps
        }

        if export_chain_format == "TXT":
            txt_export = f"Initial Input:\n{initial_input}\n\n"
            for idx, step_data in enumerate(chain_steps):
                txt_export += f"Step {idx+1}: {step_data['step']}\nPrompt:\n{step_data['prompt']}\nResponse:\n{step_data['response']}\n\n"
            st.download_button("⬇️ Download .txt file", data=txt_export, file_name="chained_output.txt", mime="text/plain")
        elif export_chain_format == "JSON":
            json_export = json.dumps(chain_export, indent=2)
            st.download_button("⬇️ Download .json file", data=json_export, file_name="chained_output.json", mime="application/json")

        # 📊 Feedback
        st.markdown("### 📊 Rate the Chaining Response")
        rating = st.slider("⭐ Rate this output", 1, 5, value=st.session_state.get("chain_rating", 3), key="chain_rating")
        feedback = st.text_area("💬 Feedback on chaining output", value=st.session_state.get("chain_feedback", ""), key="chain_feedback")

        if st.session_state.get("chaining_feedback_submitted"):
            st.success("✅ Thank you! Your feedback has been submitted.")

        if st.button("✅ Submit Chaining Feedback"):
            from firebase_auth import update_feedback_in_firebase

            user_id = st.session_state.user.get("uid") or st.session_state.user["email"].replace(".", "_")
            timestamp_to_match = st.session_state["chain_outputs"][0][-1]  # Last entry's timestamp
            log_key = st.session_state.chain_keys.get(timestamp_to_match)
            if log_key:
                update_feedback_in_firebase(user_id, log_key, rating=rating, feedback=feedback)
                st.success("✅ Feedback submitted.")
            else:
                st.error("Could not find matching chaining log to update.")
                st.session_state.chaining_feedback_submitted = True
                time.sleep(1.5)
                st.rerun()

    # 🧹 Clear Button
    if st.button("🧹 Clear Chaining"):
        st.session_state.clear_chaining = True
        st.rerun()


#view prompt history 
st.markdown("---")
st.subheader("📚 View Your Prompt History")

# --- 🔐 Safety check for user ---
if "user" not in st.session_state or "email" not in st.session_state.user:
    st.warning("User not authenticated. Please log in to view history.")
    st.stop()

# --- 🧠 Initialize session state keys ---
defaults = {
    "show_history": False,
    "load_history_now": False,
    "prompt_logs": [],
    "chain_logs": [],
    "prompt_keys": {},
    "chain_keys": {},
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 📌 Toggle button with load trigger ---
toggle_label = "📖 Load History ▾" if not st.session_state.show_history else "📕 Hide History ▴"
if st.button(toggle_label, key="toggle_history"):
    st.session_state.show_history = not st.session_state.show_history
    if st.session_state.show_history:
        st.session_state.load_history_now = True
    st.rerun()

# --- 📦 Load and Show History ---
if st.session_state.show_history:
    st.info(f"📌 Currently logged in as: {st.session_state.user['email']}")
    user_id = st.session_state.user.get("uid") or st.session_state.user["email"].replace(".", "_")
    if st.session_state.load_history_now:
        st.session_state.load_history_now = False
        try:
            logs = db.child("logs").child(user_id).get()
            st.session_state.prompt_logs = []
            st.session_state.chain_logs = []
            st.session_state.prompt_keys = {}
            st.session_state.chain_keys = {}

            if logs.each():
                for item in logs.each():
                    entry = item.val()
                    key = item.key()
                    if entry.get("chain"):
                        st.session_state.chain_logs.append(entry)
                        st.session_state.chain_keys[entry["timestamp"]] = key
                    else:
                        st.session_state.prompt_logs.append(entry)
                        st.session_state.prompt_keys[entry["timestamp"]] = key
        except Exception as e:
            st.error(f"Failed to load history: {e}")

    # 🔗 Chaining History
    if st.session_state.chain_logs:
        st.markdown("## 🔗 Chaining History")
        for entry in st.session_state.chain_logs:
            raw_time = entry.get("timestamp", "Unknown Time")
            try:
                readable_date = datetime.fromisoformat(raw_time).strftime("%d %b %Y")
            except:
                readable_date = raw_time

            with st.expander(f"🕒 {readable_date} — Initial Input: {entry.get('prompt', '')[:50]}..."):
                st.markdown("🔗 Chaining Workflow:")
                for c in entry["chain"]:
                    st.markdown(f"- 🔹 {c['step']} Prompt:")
                    st.code(c["prompt"], language="markdown")
                    st.markdown("🧠 Response:")
                    st.write(c["response"])

                delete_key = st.session_state.chain_keys.get(entry["timestamp"])
                if st.button("🗑️ Delete This Entry", key=f"delete_chain_{delete_key}"):
                    try:
                        db.child("logs").child(user_id).child(delete_key).remove()
                        st.success("Deleted successfully. Reloading...")
                        st.session_state.load_history_now = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")

    # 🧠 Single Prompt History
    if st.session_state.prompt_logs:
        st.markdown("## 🧠 Single Prompt History")
        for entry in st.session_state.prompt_logs:
            raw_time = entry.get("timestamp", "Unknown Time")
            try:
                readable_date = datetime.fromisoformat(raw_time).strftime("%d %b %Y")
            except:
                readable_date = raw_time

            with st.expander(f"🕒 {readable_date} — Prompt: {entry.get('prompt', '')[:50]}..."):
                st.code(entry.get("prompt", ""), language="markdown")
                st.markdown("🧠 AI Response:")
                st.write(entry.get("response", "No response"))

                delete_key = st.session_state.prompt_keys.get(entry["timestamp"])
                if st.button("🗑️ Delete This Entry", key=f"delete_prompt_{delete_key}"):
                    try:
                        db.child("logs").child(user_id).child(delete_key).remove()
                        st.success("Deleted successfully. Reloading...")
                        st.session_state.load_history_now = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")

    # 🔍 No History Case
    if not st.session_state.prompt_logs and not st.session_state.chain_logs:
        st.info("No history found.")




