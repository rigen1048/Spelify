# Spelify

Free Text Corrector (14 chars max)
**Super lightweight grammar & spelling checker** for very short text (≤ 14 characters)
Powered by the free **LanguageTool public API** — works in **many languages**.

## Features

- Max **14 characters** per request
- **5 checks per minute** per IP (fixed-window rate limiting)
- Supports **auto language detection**
- Returns only the **first suggested correction** per match
- Clean, mobile-friendly single-page UI
- Shows character counter in real-time
- Proper **429 Too Many Requests** handling
- Built with **FastAPI** + **HTTpx** + vanilla JS

## Video Demo

https://github.com/user-attachments/assets/96223d79-0316-4ac4-a4ed-68e45993b2f8




## How to Run Locally

#### 1. Build and run the image
git clone https://github.com/yourusername/free-text-corrector.git
cd free-text-corrector
docker build -t free-text-corrector .
docker run -p 8010:8010 free-text-corrector

#### 2. Use it
go to browser and search `http://127.0.0.1:8010`

#### 3. Clean UP
docker images
docker rmi -f [Image name / id]
docker image prune # run this specific command at your own risk if you have projects with docker
