# Voice Client Build Instructions

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Build voice client bundle
npm run build

# Run Flask app
python app.py
```

### Deployment to Render

**Build Command:**
```bash
npm install && npm run build && pip install -r requirements.txt
```

**Start Command:** (unchanged)
```bash
gunicorn app:app
```

---

## What Gets Built

**Source:** `frontend/voice-client.js`

**Output:** `static/js/voice-client.js`

**Purpose:** Bundled ElevenLabs SDK for browser

**Size:** ~100-200KB (minified)

---

## Why This Is Needed

The official `@elevenlabs/client` package cannot be loaded from CDN due to CORS/MIME type issues.

Solution: Bundle it locally with esbuild and serve from Flask.

---

## Files

- `package.json` - npm dependencies
- `frontend/voice-client.js` - SDK wrapper
- `static/js/voice-client.js` - Generated bundle (gitignored)

---

## Dependencies

**Production:**
- `@elevenlabs/client@^1.21.0` - Official ElevenLabs SDK

**Development:**
- `esbuild@^0.19.0` - Fast JavaScript bundler

---

## Troubleshooting

**Bundle not found:**
```bash
npm run build
```

**Build fails:**
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Voice not working:**
- Check browser console for `[VOICE] ElevenLabs SDK module ready`
- Verify `/static/js/voice-client.js` exists
- Check Render build logs for npm errors
