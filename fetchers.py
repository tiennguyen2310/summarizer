import base64
import os.path
from urllib.parse import quote_plus

import feedparser
import yt_dlp
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except Exception:  # pragma: no cover - optional dependency
    YouTubeTranscriptApi = None


class YouTubeFetcher:
    def fetch_videos(self, query="latest global news", limit=5):
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
        }
        search_query = f"ytsearch{limit}:{query}"
        extracted_videos = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if "entries" not in info or not info["entries"]:
                    return [{"subject": "No Results", "body": "YouTube returned no videos."}]
                for entry in info["entries"]:
                    title = entry.get("title", "No Title")
                    channel = entry.get("channel", "Unknown Channel")
                    description = entry.get("description", "No description provided.")
                    video_id = entry.get("id")
                    transcript_text, transcript_note = self._get_transcript_text(video_id)
                    clean_desc = self._clean_text(description)
                    body_text = transcript_text or clean_desc
                    if transcript_note:
                        body_text = body_text + chr(10) + chr(10) + f"[{transcript_note}]"
                    extracted_videos.append({
                        "subject": f"📺 {title}",
                        "body": f"""Channel: {channel}
Title: {title}
Transcript/Text: {body_text[:7000]}""",
                        "content_type": "video",
                        "source": "youtube",
                    })
            return extracted_videos
        except Exception as e:
            return [{"subject": "Error", "body": f"Failed to scrape YouTube: {str(e)}"}]

    def _get_transcript_text(self, video_id):
        if not video_id or YouTubeTranscriptApi is None:
            return "", "Transcript unavailable; using description only"

        try:
            segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        except Exception:
            try:
                api = YouTubeTranscriptApi()
                transcript = api.fetch(video_id, languages=["en"])
                segments = transcript.to_raw_data() if hasattr(transcript, "to_raw_data") else transcript
            except Exception:
                return "", "Transcript unavailable; using description only"

        lines = []
        for segment in segments or []:
            text = segment.get("text", "").strip()
            if text:
                lines.append(text)

        if not lines:
            return "", "Transcript unavailable; using description only"

        transcript_text = self._clean_text(" ".join(lines))
        return transcript_text[:7000], "Transcript sourced from YouTube captions"

    def _clean_text(self, text):
        text = text or ""
        text = text.replace("http://", "")
        text = text.replace("https://", "")
        return " ".join(text.split())


class NewsFetcher:
    def fetch_news(self, query="latest global news", limit=5):
        rss_url = (
            "https://news.google.com/rss/search?q="
            f"{quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        )
        feed = feedparser.parse(rss_url)
        entries = feed.entries or []
        if not entries:
            return [{"subject": "No Results", "body": "No news items were found."}]

        extracted_news = []
        for entry in entries[:limit]:
            title = entry.get("title", "No Title")
            source = entry.get("source", {})
            source_name = source.get("title", "Google News") if hasattr(source, "get") else "Google News"
            summary = entry.get("summary", "") or entry.get("description", "")
            summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ", strip=True)
            summary = self._clean_text(summary)
            link = entry.get("link", "")
            extracted_news.append({
                "subject": f"📰 {title}",
                "body": f"""Source: {source_name}
Title: {title}
Summary: {summary}
Link: {link}""",
                "content_type": "text",
                "source": "news",
            })
        return extracted_news

    def _clean_text(self, text):
        text = text or ""
        text = text.replace("http://", "")
        text = text.replace("https://", "")
        return " ".join(text.split())


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class EmailFetcher:
    def __init__(self):
        self.creds = None
        self.auth_error = None

        if not os.path.exists("token.json") and not os.path.exists("credentials.json"):
            self.auth_error = "Missing OAuth credentials. Please see the GitHub README to set up the Gmail API."
            return

        try:
            if os.path.exists("token.json"):
                self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                    self.creds = flow.run_local_server(port=0)
                with open("token.json", "w") as token:
                    token.write(self.creds.to_json())
            self.service = build("gmail", "v1", credentials=self.creds)
        except Exception as e:
            self.auth_error = f"Authentication Failed: {str(e)}"

    def _get_email_body(self, payload):
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    return base64.urlsafe_b64decode(part["body"].get("data", "")).decode("utf-8")
                if "parts" in part:
                    return self._get_email_body(part)
        elif payload.get("mimeType") in ["text/plain", "text/html"]:
            data = payload["body"].get("data", "")
            text = base64.urlsafe_b64decode(data).decode("utf-8")
            if payload.get("mimeType") == "text/html":
                return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)
            return text
        return ""

    def fetch_recent_emails(self, limit=5):
        if self.auth_error:
            return [{"subject": "Authentication Required", "body": self.auth_error}]

        try:
            results = self.service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=limit).execute()
            messages = results.get("messages", [])
            if not messages:
                return [{"subject": "No Emails", "body": "No new messages found."}]

            extracted_emails = []
            for msg in messages:
                msg_data = self.service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
                payload = msg_data["payload"]
                subject = next((header["value"] for header in payload.get("headers", []) if header["name"] == "Subject"), "No Subject")

                body = self._get_email_body(payload)
                clean_body = BeautifulSoup(body, "html.parser").get_text(separator=" ", strip=True)
                clean_body = self._clean_text(clean_body)

                extracted_emails.append({
                    "subject": f"📧 {subject}",
                    "body": clean_body[:5000],
                    "content_type": "text",
                    "source": "email",
                })
            return extracted_emails
        except Exception as e:
            return [{"subject": "API Error", "body": str(e)}]

    def _clean_text(self, text):
        text = text or ""
        text = text.replace("http://", "")
        text = text.replace("https://", "")
        return " ".join(text.split())


class DemoLinkedInFetcher:
    def fetch_recent_posts(self, limit=5):
        mock_posts = [
            {
                "subject": "💼 John Doe (Software Engineer)",
                "body": "I am thrilled to announce I am joining this company! #career",
                "content_type": "text",
                "source": "linkedin",
            },
            {
                "subject": "💼 TechStartup",
                "body": "We announce a massive API pricing update lowering costs by 50%.",
                "content_type": "text",
                "source": "linkedin",
            },
        ]
        return mock_posts[:limit]

