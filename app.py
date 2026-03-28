
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import httpx
import time

app = FastAPI(
    title="Free Text Corrector (14 chars max)",
    description="Correct short text (max 14 chars) in any language using LanguageTool public API",
    version="1.2"
)

RATE_LIMIT = 5          # max requests per window
WINDOW_SECONDS = 60     # 60-second fixed window
rate_data: dict[str, tuple[float, int]] = {}

def is_rate_limited(ip: str) -> bool:
    now = time.time()

    if ip not in rate_data:
        # First request for this IP
        rate_data[ip] = (now, 1)
        return False

    window_start, count = rate_data[ip]

    if now - window_start < WINDOW_SECONDS:
        # Still in the same window
        if count >= RATE_LIMIT:
            return True
        # Increment count
        rate_data[ip] = (window_start, count + 1)
        return False
    else:
        # New window starts now
        rate_data[ip] = (now, 1)
        return False

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Free Text Corrector</title>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
            textarea { width: 100%; height: 120px; padding: 12px; font-size: 16px; margin: 10px 0; border: 1px solid #ccc; border-radius: 8px; }
            button { padding: 12px 24px; font-size: 16px; background: #0066ff; color: white; border: none; border-radius: 8px; cursor: pointer; }
            button:hover { background: #0055cc; }
            .result { margin-top: 20px; padding: 16px; background: #f0f8ff; border-radius: 8px; white-space: pre-wrap; }
            .error { color: red; font-weight: bold; }
            .info { color: #666; font-size: 0.9em; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Free Text Corrector</h1>
        <p class="info">Max <strong>14 characters</strong> • 5 checks per minute • Any language supported</p>

        <textarea id="inputText" maxlength="14" placeholder="Enter up to 14 chars..."></textarea>
        <div class="info">Characters: <span id="charCount">0</span>/14</div>
        <br>
        <button onclick="correctText()">Correct Text</button>

        <div id="result"></div>

        <script>
            const textarea = document.getElementById('inputText');
            const charCount = document.getElementById('charCount');

            textarea.addEventListener('input', () => {
                charCount.textContent = textarea.value.length;
            });

            async function correctText() {
                const text = textarea.value.trim();
                const resultDiv = document.getElementById('result');

                if (!text) {
                    resultDiv.innerHTML = '<p class="error">Please enter some text.</p>';
                    return;
                }
                if (text.length > 14) {
                    resultDiv.innerHTML = '<p class="error">Text too long! Max 14 characters.</p>';
                    return;
                }

                resultDiv.innerHTML = '<p>Checking...</p>';

                try {
                    const response = await fetch('/api/correct', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text })
                    });

                    if (response.status === 429) {
                        resultDiv.innerHTML = '<p class="error">Too many requests! Wait a minute and try again.</p>';
                        return;
                    }

                    const data = await response.json();

                    if (data.corrected === text) {
                        resultDiv.innerHTML = `<p><strong>No errors found!</strong></p><div class="result">${text}</div>`;
                    } else {
                        resultDiv.innerHTML = `
                            <p><strong>Corrected:</strong></p>
                            <div class="result">${data.corrected}</div>
                        `;
                    }
                } catch (err) {
                    resultDiv.innerHTML = '<p class="error">Service unavailable. Try again later.</p>';
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/correct")
async def correct_text(request: Request, payload: dict):
    client_ip = request.client.host

    if is_rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute.")

    text = payload.get("text", "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    if len(text) > 14:
        raise HTTPException(status_code=400, detail="Text too long. Maximum 14 characters allowed.")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api.languagetool.org/v2/check",
                data={"text": text, "language": "auto"},
                timeout=15.0
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            raise HTTPException(status_code=502, detail="Correction service temporarily unavailable")

    # Apply corrections (first suggestion only, from end to start to preserve offsets)
    corrected = text
    offset_shift = 0
    matches = sorted(data.get("matches", []), key=lambda m: m["offset"], reverse=True)

    for match in matches:
        start = match["offset"] + offset_shift
        end = start + match["length"]
        if match.get("replacements"):
            replacement = match["replacements"][0]["value"]
            corrected = corrected[:start] + replacement + corrected[end:]
            offset_shift += len(replacement) - match["length"]

    return {
        "original": text,
        "corrected": corrected if matches else text,
        "matches": data.get("matches", [])
    }

# Run with: uvicorn app:app --reload
