# 📧 AI Daily Summarizer

A local AI tool that extracts and summarizes data from multiple platforms. It securely connects to a user's Gmail via OAuth, natively scrapes YouTube search results, and generates concise summaries through llama.cpp using a local GGUF model.

## 🚀 Live Demonstration
The project now targets local llama.cpp inference instead of a cloud GPU notebook.


## 🛠️ Features
- **Secure OAuth 2.0 Login:** Does not use app passwords; uses official Google APIs.
- **Keyless YouTube Extraction:** Integrates `yt-dlp` to natively query and scrape YouTube video metadata and descriptions without requiring API keys or triggering rate limits.
- **Real-Time UI Yielding:** Built with Gradio to stream summaries live as they generate.
- **llama.cpp Inference:** Runs local GGUF models through `llama-cli`, with CPU mode as the default.
- **Dynamic Model Hot-Swapping:** Allows users to switch between GGUF model files live in the UI without restarting the application backend.

## 💻 How to run locally
1. Make sure llama.cpp is built and `../llama.cpp/build/bin/llama-cli` exists.
2. Put a GGUF model somewhere local. By default this app uses `../ChatBot/Llama-3.2-1B-Instruct-Q4_K_M.gguf`.
3. `pip install -r requirements.txt`
4. Optional email setup: download your `credentials.json` from Google Cloud Console, then run `python get_token.py` to authenticate.
5. Run `USE_MOCK_LLM=False LLAMA_MODEL=../ChatBot/Llama-3.2-1B-Instruct-Q4_K_M.gguf python app.py`

Useful environment variables:
- `LLAMA_MODEL`: path to the GGUF model.
- `LLAMA_CPP_CLI`: path to `llama-cli`; defaults to `../llama.cpp/build/bin/llama-cli`.
- `LLAMA_GPU_LAYERS`: layers to offload to GPU; defaults to `0` for CPU-only.
- `LLAMA_CTX_SIZE`: context window; defaults to `4096`.
- `LLAMA_MAX_TOKENS`: max summary tokens; defaults to `160`.

## Future Developments
- Prompt tuning for higher-quality summaries
- Better model-template presets for common GGUF families
- Multi-email batch summarization
- Daily digest email delivery
- Official API integrations for LinkedIn and Twitter feeds
