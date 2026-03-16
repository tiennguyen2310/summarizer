import gradio as gr
from fetchers import EmailFetcher, YouTubeFetcher, DemoLinkedInFetcher
from summarizer import LLMSummarizer
import os
import html

# true on server; false locally
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "True") == "True"
print("Initializing AI")
summarizer = LLMSummarizer(use_mock=USE_MOCK_LLM)

def process_content(source, limit, query):
    if source == "YouTube Search":
        fetcher = YouTubeFetcher()
        items = fetcher.fetch_videos(query=query, limit=int(limit))
    elif source == "Emails (Requires Auth Setup)":
        fetcher = EmailFetcher()
        items = fetcher.fetch_recent_emails(limit=int(limit))
    elif source == "LinkedIn (Demo)":
        fetcher = DemoLinkedInFetcher()
        items = fetcher.fetch_recent_posts(limit=int(limit))
    else:
        items = [{"subject": "Error", "body": "Unknown source"}]

    html_output = "<div style='display: flex; flex-direction: column; gap: 20px;'>"
    yield html_output + "<p style='color: gray; font-style: italic;'>Fetching data and warming up AI...</p></div>"
    
    for item in items:
        # if OAuth missing, bypass the AI and show the error message
        if "Authentication Required" in item['subject'] or "Error" in item['subject'] or "No Results" in item['subject']:
            html_output += f"<h3 style='color: #ef4444; padding: 20px; border: 1px solid #f87171; border-radius: 8px;'>⚠️ {item['subject']}: {item['body']}</h3>"
            yield html_output + "</div>"
            continue
            
        summary = summarizer.summarize(item['body'])
        
        safe_subject = html.escape(item['subject'])
        safe_body = html.escape(item['body'])
        safe_summary = html.escape(summary)
        
        card = f"""
        <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top: 0; margin-bottom: 15px; color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 10px;">
                {safe_subject}
            </h3>
            <div style="display: flex; flex-direction: row; gap: 20px;">
                <div style="flex: 1; padding: 15px; background: #f9fafb; border-radius: 8px; max-height: 250px; overflow-y: auto;">
                    <h4 style="margin-top: 0; color: #4b5563; font-size: 14px; text-transform: uppercase;">Original Text</h4>
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

with gr.Blocks(theme=gr.themes.Base()) as interface:
    gr.Markdown("# 🌐 AI Summarizer")
    gr.Markdown("Instantly catch up on YouTube topics or your Inbox using completely local AI. *(Email integration requires local OAuth setup).*")
    
    with gr.Row():
        source_dropdown = gr.Dropdown(
            choices=["YouTube Search", "Emails (Requires Auth Setup)", "LinkedIn (Demo)"], 
            value="YouTube Search", 
            label="Select Source", 
            scale=1
        )
        search_box = gr.Textbox(
            value="Global News", label="YouTube Search Topic", 
            placeholder="e.g., Tech Reviews, Python Tutorials...",
            scale=2, visible=True
        )
        limit_slider = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="Items to fetch", scale=1)
        fetch_btn = gr.Button("Fetch & Summarize", variant="primary", scale=1)
    
    output_area = gr.HTML(label="Your Summaries")
    
    def update_ui(source):
        if source == "YouTube Search":
            return gr.update(visible=True)
        return gr.update(visible=False)

    source_dropdown.change(fn=update_ui, inputs=source_dropdown, outputs=search_box)
    fetch_btn.click(fn=process_content, inputs=[source_dropdown, limit_slider, search_box], outputs=output_area)

if __name__ == "__main__":
    interface.launch(share=True)