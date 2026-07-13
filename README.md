# Lifehack Motivation → Telegram → 3,000-byte TTS chunks

This project has two connected parts:

1. **GitHub Actions** sends one randomly selected link from your manually curated Lifehack Motivation list every day.
2. A **Telegram webhook bot**, deployed from the same GitHub repository to Render, splits
   text that you paste or upload into natural TTS chunks of at most **3,000 UTF-8 bytes**.

## Why it does not automatically extract Lifehack articles

Lifehack's Terms of Service say users must not access the site through automated or
non-human means such as a bot or script. This project therefore does not scrape or
download the article. It sends a Motivation link; you open the page normally and supply
the text to your private bot for personal study.

Motivation section:

```text
https://www.lifehack.org/communication/motivation
```

Terms:

```text
https://www.lifehack.org/terms-of-service
```

## Daily workflow

```text
GitHub Actions sends a Motivation link
             ↓
You open and read it normally
             ↓
You paste text into Telegram or upload a UTF-8 .txt file
             ↓
The bot returns Part 1, Part 2, Part 3...
Each text part is ≤ 3,000 UTF-8 bytes
             ↓
You put each part into your TTS tool
             ↓
You summarize it in your own words and practise speaking
```

## Files

```text
.
├── .github/
│   └── workflows/
│       ├── daily.yml
│       ├── set-webhook.yml
│       └── tests.yml
├── tests/
│   └── test_splitter.py
├── app.py
├── articles.json
├── render.yaml
├── requirements.txt
├── send_daily.py
├── set_webhook.py
├── split_text.py
└── telegram_api.py
```

# Setup

## 1. Create the Telegram bot

1. Open the verified **@BotFather** account in Telegram.
2. Send `/newbot`.
3. Choose a display name.
4. Choose a username ending in `bot`.
5. Copy the token. It resembles:

```text
123456789:AAExampleToken...
```

Keep it private.

## 2. Find your Telegram chat ID

1. Open your new bot.
2. Press **Start** and send `hello`.
3. In a browser, replace `<TOKEN>` below with your token:

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

4. Find:

```json
"chat": {
  "id": 123456789
}
```

That number is your chat ID.

If `"result":[]` appears, send another message to the bot and refresh the browser page.

## 3. Put this project in GitHub

1. Create a new private GitHub repository.
2. Upload all files and folders from this template.
3. Confirm that the workflow files are under:

```text
.github/workflows/
```

## 4. Deploy the webhook bot to Render

GitHub stores the code, but an interactive Telegram bot needs an HTTPS server that can
receive messages. Render provides that server.

1. Create a Render account.
2. Choose **New → Blueprint**.
3. Connect the GitHub repository.
4. Render reads `render.yaml`.
5. Enter these environment variables when requested:

```text
TELEGRAM_BOT_TOKEN = token from BotFather
TELEGRAM_CHAT_ID    = your numeric Telegram chat ID
WEBHOOK_SECRET      = a random 32+ character value
```

A valid example format for `WEBHOOK_SECRET` is:

```text
mY_private_webhook_2026_A7f9K2x8
```

Use your own value, not the example.

6. Deploy.
7. Copy the public Render URL. It resembles:

```text
https://lifehack-motivation-tts-bot.onrender.com
```

The health page should return:

```json
{"status":"ok"}
```

## 5. Add GitHub Actions secrets

Open your GitHub repository:

```text
Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

Create four secrets:

```text
TELEGRAM_BOT_TOKEN = token from BotFather
TELEGRAM_CHAT_ID    = numeric chat ID
PUBLIC_BASE_URL     = your Render URL, without a trailing slash
WEBHOOK_SECRET      = exactly the same value used in Render
```

Secret names must match exactly.

## 6. Register the Telegram webhook

In GitHub:

```text
Actions
→ Set Telegram Webhook
→ Run workflow
```

The workflow should turn green.

Now send `/start` to the bot.

## 7. Test the TTS splitter

Send a normal text message. The bot replies:

```text
Prepared 2 TTS part(s)...
Part 1/2 · 2,981 bytes
[text]
Part 2/2 · 1,274 bytes
[text]
```

Copy only each text message into the TTS service.

For a long article, create a UTF-8 `.txt` file and upload it to the bot. The template
accepts `.txt` and `.md` files up to 250 KB.

## 8. Test the daily Motivation message

In GitHub:

```text
Actions
→ Daily Motivation Article
→ Run workflow
```

The template schedules delivery at **05:00 Europe/Berlin** every day.

# Editing the Motivation reading list

Open `articles.json`:

```json
[
  {
    "title": "Article title",
    "url": "https://www.lifehack.org/example"
  }
]
```

Add links manually while browsing the Lifehack Motivation section normally.

JSON rules:

- Keep the surrounding `[` and `]`.
- Put a comma between entries.
- Do not put a comma after the final entry.
- Use full Lifehack HTTPS links.

# How the 3,000-byte splitter works

The splitter:

1. Normalizes whitespace.
2. Prefers sentence boundaries.
3. Uses word boundaries when a sentence is too large.
4. Uses safe Unicode-character boundaries only as a last resort.
5. Verifies every chunk after UTF-8 encoding.

Bytes are not the same as characters:

- Most English letters use 1 UTF-8 byte.
- Korean characters commonly use 3 UTF-8 bytes.
- Many emoji use 4 or more bytes as displayed sequences.

That is why the code measures encoded bytes rather than using `len(text)`.

# Commands

```text
/start   Show instructions
/help    Show instructions
/limit   Explain the 3,000-byte setting
/split   Split text written after the command
```

Ordinary pasted text is split automatically.

# Important limitations

- The bot does not scrape Lifehack; it selects from links that you added to `articles.json`.
- A URL alone is not extracted.
- The bot currently returns text chunks; it does not generate audio by itself.
- Render's free web service can sleep when idle, so the first reply after a long idle
  period may be delayed.
- Do not publish your Telegram token or webhook secret.


# One-click ad-free browser extraction

The `browser_extension` folder contains a Chrome/Edge extension. After you open a
Lifehack article normally, clicking the extension icon:

- finds the likely article body in the already loaded page;
- removes navigation, ads, social/share areas, subscriptions and recommendations;
- sends the cleaned text to this private Render service;
- splits it into Telegram TTS parts of at most 3,000 UTF-8 bytes.

Add this environment variable to Render:

```text
SUBMIT_SECRET
```

Then load the `browser_extension` folder as an unpacked extension and save:

```text
PUBLIC_BASE_URL = your Render URL
SUBMIT_SECRET   = the same secret stored in Render
```

See `ONE_CLICK_GUIDE_KO.md` for Korean setup steps.
