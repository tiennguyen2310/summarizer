import os
import re
import shutil
import subprocess
from pathlib import Path


class LLMSummarizer:
    def __init__(
        self,
        model_path="../ChatBot/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        use_mock=False,
        llama_cli="../llama.cpp/build/bin/llama-cli",
        max_tokens=160,
        ctx_size=4096,
        gpu_layers=0,
        timeout=180,
    ):
        self.use_mock = use_mock
        self.llama_cli = self._resolve_path(os.getenv("LLAMA_CPP_CLI", llama_cli))
        self.current_model_path = None
        self.max_tokens = int(os.getenv("LLAMA_MAX_TOKENS", max_tokens))
        self.ctx_size = int(os.getenv("LLAMA_CTX_SIZE", ctx_size))
        self.gpu_layers = os.getenv("LLAMA_GPU_LAYERS", str(gpu_layers))
        self.timeout = int(os.getenv("LLAMA_TIMEOUT", timeout))

        if not self.use_mock:
            self.load_model(os.getenv("LLAMA_MODEL", model_path))

    def _resolve_path(self, value):
        if not value:
            return None

        expanded = os.path.expanduser(value)
        if os.path.isabs(expanded):
            return expanded

        project_root = Path(__file__).resolve().parent
        return str((project_root / expanded).resolve())

    def load_model(self, model_path):
        resolved_model = self._resolve_path(model_path)

        if not resolved_model or not os.path.exists(resolved_model):
            return f"Error loading model: GGUF file not found: {resolved_model or model_path}"

        if not os.path.exists(self.llama_cli) and shutil.which(self.llama_cli) is None:
            return f"Error loading model: llama-cli not found: {self.llama_cli}"

        self.current_model_path = resolved_model
        print(f"Using llama.cpp model: {resolved_model}")
        return f"Using GGUF model: {resolved_model}"

    def summarize(self, text):
        if self.use_mock:
            return f"[FAKE SUMMARY] This is a fake summary for local testing of: {text[:30]}..."

        if not self.current_model_path:
            raise RuntimeError("No llama.cpp GGUF model is loaded.")

        system_prompt = (
            "You are a concise summarizer. Return exactly two clear, complete "
            "sentences and no preamble."
        )
        prompt = (
            "Summarize the following content in exactly two clear, complete "
            f"sentences.\n\nText:\n{text}\n\nSummary:"
        )

        cmd = [
            self.llama_cli,
            "-m",
            self.current_model_path,
            "-n",
            str(self.max_tokens),
            "-c",
            str(self.ctx_size),
            "-ngl",
            str(self.gpu_layers),
            "--temp",
            "0.2",
            "--top-p",
            "0.9",
            "--no-display-prompt",
            "--no-show-timings",
            "--log-disable",
            "--simple-io",
            "-st",
            "-sys",
            system_prompt,
            "-p",
            prompt,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return "Summary generation timed out. Try a smaller input or increase LLAMA_TIMEOUT."

        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")

        if result.returncode != 0:
            error = (stderr or stdout).strip()
            return f"llama.cpp failed: {error}"

        raw_summary = self._extract_summary(stdout)

        # Find the last punctuation mark, and cut everything after it.
        match = re.search(r".*[.!?]", raw_summary, flags=re.DOTALL)
        if match:
            clean_summary = match.group(0)
        else:
            clean_summary = raw_summary + "."

        return clean_summary

    def _extract_summary(self, output):
        summary = output
        prompt_marker = "\n> "
        if prompt_marker in summary:
            summary = summary.rsplit(prompt_marker, 1)[-1]
            if "\n\n" in summary:
                summary = summary.split("\n\n", 1)[-1]

        if "Summary:" in summary:
            summary = summary.rsplit("Summary:", 1)[-1]

        summary = re.sub(r"\s*Exiting\.*\s*$", "", summary).strip()
        summary = re.sub(r"^Loading model\.\.\..*?\n\n", "", summary, flags=re.DOTALL).strip()

        lines = []
        ignored_prefixes = (
            "warning:",
            "build",
            "model",
            "modalities",
            "available commands:",
            "/",
        )
        for line in summary.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(ignored_prefixes):
                continue
            if stripped.startswith(">"):
                continue
            lines.append(stripped)

        return " ".join(lines).strip()
