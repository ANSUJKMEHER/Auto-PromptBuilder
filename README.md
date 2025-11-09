# 🧠 Auto Prompt Builder
*A Dynamic Prompt Generation and Tuning System for Industry Use*

## 📄 Overview
Auto Prompt Builder is an intelligent web-based platform designed to simplify prompt engineering for generative AI systems. It allows users to **create, chain, test, and evaluate** prompts through a visual and interactive interface — without requiring any coding expertise.

Built with **Python**, **Streamlit**, **Firebase**, and the **Cohere API**, the platform serves professionals across industries such as HR, education, healthcare, and legal services who want to build efficient and reusable prompt workflows.

---

## 🚀 Features
- 🔐 **User Authentication** – Secure login/signup using Firebase  
- 🧩 **Prompt Template Library** – Domain-specific templates (HR, Legal, Education, etc.)  
- 🔗 **Prompt Chaining** – Connect multiple prompts to automate workflows  
- ⚙ **Parameter Tuning** – Adjust creativity (temperature), token length, etc.  
- ⭐ **Evaluation System** – Rate and give feedback on AI-generated responses  
- 💾 **Export Options** – Save prompts/responses as `.txt` or `.json`  
- 🔄 **Real-Time Updates** – Live preview of AI responses with adjustable settings  

---

## 🧱 Tech Stack
| Layer | Technology |
|-------|-------------|
| Frontend | Streamlit |
| Backend | Python |
| Database | Firebase Firestore |
| AI Integration | Cohere API |
| Authentication | Firebase Auth |


---

## ⚙ Installation & Setup
### Prerequisites
- Python 3.10+
- Firebase project with Authentication & Realtime Database enabled
- Cohere API key
- Streamlit installed (`pip install streamlit`)

### Steps
```bash
# Clone this repository
git clone https://github.com/ANSUJKMEHER/Auto-PromptBuilder.git
cd Auto-PromptBuilder

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# (You can use a .env file for API keys)
COHERE_API_KEY=your-cohere-api-key
FIREBASE_CONFIG=your-firebase-config

# Run the app
streamlit run app.py
