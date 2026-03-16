# 📧 AI Daily Email Summarizer

An open-source, locally run (or cloud GPU) AI tool that securely connects to the user's Gmail, extracts your daily newsletters/emails, and generates real-time concise summaries using **Qwen3-4B-Instruct**.

## 🚀 Live Demonstration
I have deployed the AI inference engine on a Kaggle T4 GPU. 
👉 **[View the Kaggle Notebook Demo Here](https://www.kaggle.com/code/tien23/summarizer)**

*(Note: For security reasons, the underlying OAuth tokens are kept in a private Kaggle dataset. You can view the code, but you must clone the repo and supply your own `credentials.json` to run it yourself).*

## 🛠️ Features
- **Secure OAuth 2.0 Login:** Does not use app passwords; uses official Google APIs.
- **Real-Time UI Yielding:** Built with Gradio to stream summaries live as they generate.
- **Smart Text Cleaning:** Uses Regex to strip out messy HTML, image links, and tracking URLs to save LLM context space.
- **Incomplete Sentence Heuristic:** Post-processes the LLM output to guarantee grammatically complete sentences.

## 💻 How to run locally
1. `git clone https://github.com/tiennguyen2310/summarizer`
2. `pip install -r requirements.txt`
3. Download your `credentials.json` from Google Cloud Console.
4. Run `python get_token.py` to authenticate.
5. Run `python app.py`

## Future Developments
- Prompt tuning for higher-quality summaries
- Support for additional open-source models (Mistral, Llama, etc.)
- Multi-email batch summarization
- Daily digest email delivery
- Different sources ofsummarization (news, YouTube, etc.)