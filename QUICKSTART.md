# Quick Start Guide

## Get Running in 5 Minutes

### Step 1: Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (you'll need it in Step 3)

### Step 2: Set Up Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure API Key

```bash
# Create .env file from example
cp .env.example .env

# Edit .env and add your OpenAI API key
# Replace 'your_openai_api_key_here' with your actual key
```

Or do it in one command:
```bash
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
```

### Step 4: Start Backend

```bash
# Make sure you're in the backend directory
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
Database initialized
OpenAI API configured: True
```

**Keep this terminal running!**

### Step 5: Start Frontend (New Terminal)

```bash
# Open a new terminal
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### Step 6: Use the App

1. Open http://localhost:5173 in your browser
2. Upload an image
3. Enter goal (e.g., "Promote birthday parties")
4. Enter address (e.g., "2051 Skibo Rd, Fayetteville, NC 28314")
5. Select platform (Facebook or Instagram)
6. Click "Generate Caption"
7. Wait for AI magic!
8. Edit, regenerate, or save

## Testing It Out

### Example Test Data:

**Goal:** "Promote birthday party packages with $99 discount"

**Address:** "2051 Skibo Rd, Fayetteville, NC 28314"

**Platform:** Facebook

**Image:** Any Urban Air promotional image from the `Urban Air Caption example` folder

## Troubleshooting

**"OpenAI API configured: False"**
- You didn't set your API key in the .env file
- Make sure there are no quotes around the key
- Format: `OPENAI_API_KEY=sk-proj-abc123...`

**"Error generating caption"**
- Backend not running? Check terminal
- CORS error? Restart backend
- Check browser console (F12) for errors

**Frontend won't connect**
- Make sure backend is running on port 8000
- Check that frontend shows http://localhost:5173
- Try refreshing the page

**Port already in use**
- Backend: Change port in command: `uvicorn app.main:app --reload --port 8001`
- Frontend: Press `Ctrl+C` and run `npm run dev` again

## What Happens Under the Hood

1. **Upload Image** → Sent to backend
2. **Backend receives** → OpenAI Vision analyzes image
3. **Extract location** → Parse city/state from address
4. **Web research** → Scrape chamber/gov websites (may timeout - that's okay)
5. **GPT-4o generates** → Creates localized caption
6. **Return to frontend** → Display for editing
7. **Save** → Store in SQLite database

## Next Steps

Once you've tested locally and it works:

1. **Deploy Backend to Railway:**
   - Push code to GitHub
   - Connect Railway to your repo
   - Set `OPENAI_API_KEY` environment variable in Railway
   - Deploy!

2. **Deploy Frontend:**
   - Build: `npm run build`
   - Deploy `dist` folder to Vercel/Netlify
   - Update `API_URL` in App.jsx to Railway backend URL

3. **Improve Prompts:**
   - Edit `backend/app/services/openai_service.py`
   - Tweak the prompts to match Urban Air's brand voice
   - Test with real locations

## Need Help?

Check the full README.md for detailed documentation!
