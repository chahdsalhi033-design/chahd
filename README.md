# My AI Text-to-Video App

This is your own text-to-video web app. It uses Runway's real AI video API.

## Run on your computer

1. Install Python 3.10+ from https://python.org
2. Open Terminal / Command Prompt in this folder.
3. Run:

```bash
pip install -r requirements.txt
copy .env.example .env
```

4. Open `.env` and paste your Runway API key:

```env
RUNWAY_API_KEY=your_real_key
```

5. Start the app:

```bash
uvicorn app:app --reload
```

6. Open: http://127.0.0.1:8000

## Put it online free

1. Create a GitHub account and upload this folder.
2. Create a free Render account: https://render.com
3. Click New + > Web Service.
4. Connect your GitHub repository.
5. Add environment variable:

```env
RUNWAY_API_KEY=your_real_key
```

6. Click Deploy.
7. Render gives you a public link like:

```text
https://your-app-name.onrender.com
```

## Important

You must add your own Runway API key. Runway charges credits for each generated video.
