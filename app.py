import html
import os

import gradio as gr

from fetchers import DemoLinkedInFetcher, EmailFetcher, NewsFetcher, YouTubeFetcher
from summarizer import LLMSummarizer

# true on server; false locally
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "False") == "True"
print("Initializing AI")
summarizer = LLMSummarizer(use_mock=USE_MOCK_LLM)


def fetch_items(source, limit, query):
    limit = int(limit)
    query = (query or "").strip() or "latest global news"

    if source == "YouTube Search (video transcripts)":
        fetcher = YouTubeFetcher()
        return fetcher.fetch_videos(query=query, limit=limit)
    if source == "News Search (text)":
        fetcher = NewsFetcher()
        return fetcher.fetch_news(query=query, limit=limit)
    if source == "Cross-media: News + YouTube":
        news_limit = max(1, limit)
        video_limit = max(1, limit)
        news_items = NewsFetcher().fetch_news(query=query, limit=news_limit)
        video_items = YouTubeFetcher().fetch_videos(query=query, limit=video_limit)
        for item in news_items + video_items:
            item.setdefault("cross_media", True)
        return news_items + video_items
    if source == "Emails (Requires Auth Setup)":
        fetcher = EmailFetcher()
        return fetcher.fetch_recent_emails(limit=limit)
    if source == "LinkedIn (Demo)":
        fetcher = DemoLinkedInFetcher()
        return fetcher.fetch_recent_posts(limit=limit)
    return [{"subject": "Error", "body": "Unknown source"}]


def process_content(source, limit, query):
    items = fetch_items(source, limit, query)

    html_output = "<div style='display: flex; flex-direction: column; gap: 20px;'>"
    yield html_output + "<p style='color: gray; font-style: italic;'>Fetching data and warming up AI...</p></div>"

    if not items:
        yield html_output + "<p>No items found.</p></div>"
        return

    error_subjects = {"Authentication Required", "Error", "No Results", "API Error", "No Emails"}
    valid_items = []
    for item in items:
        if any(marker in item.get('subject', '') for marker in error_subjects):
            html_output += f"<h3 style='color: #ef4444; padding: 20px; border: 1px solid #f87171; border-radius: 8px;'>⚠️ {html.escape(item['subject'])}: {html.escape(item['body'])}</h3>"
            yield html_output + "</div>"
            continue
        valid_items.append(item)

    if not valid_items:
        return

    top_items = valid_items[:5]
    aggregate_summary = summarizer.summarize_collection(
        top_items,
        topic=query,
        cross_media=(source == "Cross-media: News + YouTube"),
    )

    aggregate_card = f"""
    <div style="border: 1px solid #d1d5db; border-radius: 12px; padding: 20px; background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); box-shadow: 0 6px 18px rgba(0,0,0,0.06);">
        <h3 style="margin-top: 0; margin-bottom: 10px; color: #111827;">Top-{len(top_items)} Aggregate Summary</h3>
        <p style="margin: 0; color: #1f2937; line-height: 1.7; font-size: 15px;">{html.escape(aggregate_summary)}</p>
    </div>
    """
    html_output += aggregate_card
    yield html_output + "</div>"

    for item in valid_items:
        summary = summarizer.summarize(item['body'], topic=query)

        safe_subject = html.escape(item['subject'])
        safe_body = html.escape(item['body'])
        safe_summary = html.escape(summary)
        safe_source = html.escape(item.get('source', 'text'))
        safe_type = html.escape(item.get('content_type', 'text'))

        card = f"""
        <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top: 0; margin-bottom: 8px; color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 10px;">
                {safe_subject}
            </h3>
            <p style="margin-top: 0; margin-bottom: 15px; color: #6b7280; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em;">
                Source: {safe_source} · Type: {safe_type}
            </p>
            <div style="display: flex; flex-direction: row; gap: 20px;">
                <div style="flex: 1; padding: 15px; background: #f9fafb; border-radius: 8px; max-height: 250px; overflow-y: auto;">
                    <h4 style="margin-top: 0; color: #4b5563; font-size: 14px; text-transform: uppercase;">Original Text / Transcript</h4>
                    <p style="font-size: 13px; color: #6b7280; line-height: 1.5; white-space: pre-wrap;">{safe_body}</p>
                </div>
                <div style="flex: 1; padding: 15px; background: #eff6ff; border-radius: 8px; border: 1px solid #bfdbfe;">
                    <h4 style="margin-top: 0; color: #1d4ed8; font-size: 14px; text-transform: uppercase;">✨ AI Summary</h4>
                    <p style="font-size: 15px; color: #1e3a8a; line-height: 1.6; font-weight: 500;">{safe_summary}</p>
                </div>
            </div>
        </div>
        """
        html_output += card
        yield html_output + "</div>"


def change_model_logic(new_model_path):
    if USE_MOCK_LLM:
        return "Using Mock LLM - No reload needed."
    result = summarizer.load_model(new_model_path)
    return result


with gr.Blocks(theme=gr.themes.Base()) as interface:
    gr.Markdown("# 🌐 AI Summarizer")
    gr.Markdown(
        "Pull together text sources and video transcripts, then generate an item-level summary plus a top-5 aggregate summary. "
        "Use OpenRouter for API-backed model calls; email integration still requires local OAuth setup."
    )

    with gr.Accordion("⚙️ Model Settings", open=False):
        with gr.Row():
            model_input = gr.Textbox(
                value=os.getenv("OPENROUTER_MODEL", "~openai/gpt-latest"),
                label="OpenRouter Model Slug",
                placeholder="e.g., openai/gpt-oss-20b:free",
            )
            load_btn = gr.Button("Use This Model", variant="secondary")
        status_msg = gr.Markdown("*Current OpenRouter model slug is ready.*")

    with gr.Row():
        source_dropdown = gr.Dropdown(
            choices=[
                "YouTube Search (video transcripts)",
                "News Search (text)",
                "Cross-media: News + YouTube",
                "Emails (Requires Auth Setup)",
                "LinkedIn (Demo)",
            ],
            value="Cross-media: News + YouTube",
            label="Select Source",
            scale=1,
        )
        search_box = gr.Textbox(
            value="transit strike today",
            label="Search / topic",
            placeholder="e.g., transit strike today, AI layoffs, election debate...",
            scale=2,
            visible=True,
        )
        limit_slider = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="Items per source", scale=1)
        fetch_btn = gr.Button("Fetch & Summarize", variant="primary", scale=1)

    output_area = gr.HTML(label="Your Summaries")

    fetch_btn.click(fn=process_content, inputs=[source_dropdown, limit_slider, search_box], outputs=output_area)
    load_btn.click(fn=change_model_logic, inputs=model_input, outputs=status_msg)

if __name__ == "__main__":
    interface.launch(share=os.getenv("GRADIO_SHARE", "False") == "True")

