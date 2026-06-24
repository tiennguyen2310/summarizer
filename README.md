# 📧 AI Daily Summarizer

A local AI tool that extracts and summarizes data from multiple platforms. It can pull text-based sources, fetch YouTube transcripts when available, and generate concise summaries through OpenRouter API-backed models.

## 🚀 Live Demonstration
The project now targets API inference through OpenRouter instead of a local llama.cpp binary.

## 🛠️ Features
- **Secure OAuth 2.0 Login:** Does not use app passwords; uses official Google APIs.
- **Text + Video Intake:** Summarizes text sources directly, and uses `youtube-transcript-api` for YouTube transcripts when available.
- **Cross-media aggregation:** Combines news/text snippets and video transcripts into one top-level summary, while still showing item-level summaries underneath.
- **Real-Time UI Yielding:** Built with Gradio to stream summaries live as they generate.
- **OpenRouter API inference:** Runs through `/api/v1/chat/completions` with configurable model slugs.
- **Dynamic Model Hot-Swapping:** Lets you change the OpenRouter model slug in the UI without restarting.

## 💻 How to run locally
1. Install dependencies: `pip install -r requirements.txt`
2. Set `OPENROUTER_API_KEY` in your environment.
3. Optionally set `OPENROUTER_MODEL` to a free OpenRouter GPT-OSS model slug.
4. Optional email setup: download your `credentials.json` from Google Cloud Console, then run `python get_token.py` to authenticate.
5. Run `python app.py`

Useful environment variables:
- `OPENROUTER_API_KEY`: required for API-backed summaries.
- `OPENROUTER_MODEL`: model slug to send to OpenRouter, e.g. a free GPT-OSS slug.
- `OPENROUTER_SITE_URL`: optional referer header for OpenRouter.
- `OPENROUTER_APP_NAME`: optional app title header for OpenRouter.
- `OPENROUTER_TIMEOUT`: request timeout in seconds.
- `OPENROUTER_MAX_TOKENS`: max summary tokens per call.
- `USE_MOCK_LLM`: set to `True` to bypass the API for local testing.

## Notes
- News is currently implemented through Google News RSS search snippets, which is a lightweight free path.
- TikTok is still TBD. A practical next step would be a dedicated fetcher that uses a transcript-first path when captions are available, then falls back to a local speech-to-text pipeline if needed.
