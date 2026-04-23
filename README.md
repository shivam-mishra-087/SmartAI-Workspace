# 🤖 AI Assistant Pro (Groq + Streamlit)

An AI-powered chatbot application built using **Streamlit** and **Groq LLM**, capable of handling conversational queries, document processing (PDF/DOCX), voice input, and real-time web search.
## 🚀 Features
* 💬 Conversational AI chatbot using Groq LLM
* 📄 PDF & DOCX document analysis
* 🎤 Voice input support (Speech Recognition)
* 🌐 Real-time web search integration
* 🔊 Text-to-Speech output (gTTS)
* 📊 Clean and interactive UI with Streamlit

## 🛠️ Tech Stack
* Python
* Streamlit
* Groq API (LLM)
* DuckDuckGo Search
* PyPDF & python-docx
* SpeechRecognition
* gTTS

## 📂 Project Structure
LLM_project/
│── app.py
│── requirements.txt
│── README.md

## 🔐 Environment Setup
### ⚠️ Important: Do NOT hardcode API keys
### 👉 For Streamlit Cloud

Go to **App Settings → Secrets** and add:
GROQ_API_KEY = "your_api_key_here"

## ▶️ Run Locally
### 1. Clone the repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

### 2. Install dependencies
pip install -r requirements.txt

### 3. Set API Key (Temporary)
set GROQ_API_KEY=your_api_key_here   # Windows CMD

### 4. Run the app
streamlit run app.py

## ☁️ Deployment (Streamlit Cloud)
1. Push your code to GitHub
2. Go to Streamlit Cloud
3. Click **New App**
4. Select your repository
5. Add your API key in **Secrets**
6. Deploy 🚀

## 🧠 How It Works
* User input is captured via Streamlit UI
* Query is processed using Groq LLM
* Optional modules handle:

  * Document parsing (PDF/DOCX)
  * Voice recognition
  * Web search
* Response is generated and displayed in real-time

## ⚠️ Limitations
* Voice input may not work on cloud servers
* Internet required for API and search features

## 🔮 Future Improvements
* Chat history memory
* Authentication system
* Multi-language support
* Advanced UI enhancements

## 🤝 Contributing
Feel free to fork this repo and contribute!

## 📜 License
This project is open-source and available under the MIT License.

## 👨‍💻 Author

**Shivam Mishra**
Aspiring Data Scientist | AI Developer

⭐ If you like this project, give it a star on GitHub!
