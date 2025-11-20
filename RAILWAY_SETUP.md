# Railway Deployment Setup Guide

## 🚨 Quick Fix for 502 Errors

The 502 errors were caused by **gunicorn timeout issues**. The fix has been pushed to GitHub.

### Steps to Fix:

1. **Redeploy on Railway** (it will pull the latest code with timeout fix)
2. **Verify Environment Variables** (see below)

---

## Required Environment Variables

Set these in your Railway project settings:

### 1. OPENAI_API_KEY (Required)
```
OPENAI_API_KEY=sk-proj-your-key-here
```
**Where to find it:** https://platform.openai.com/api-keys

**⚠️ Important:** Make sure there are no extra spaces or quotes around the key!

---

## Railway Configuration

### Port Configuration
Railway automatically detects the port from your app. The Dockerfile is configured to use port 8000.

**No action needed** - Railway will handle this automatically.

### Build Configuration
Railway will automatically:
1. Detect the Dockerfile
2. Build both frontend and backend
3. Serve the frontend from the backend

**No action needed** - Dockerfile handles everything.

---

## What the Fix Does

### Before (Causing 502 Errors):
- Gunicorn timeout: 30 seconds (default)
- Caption generation with GPT-5.1 reasoning: 30-90 seconds
- **Result:** Worker killed → 502 error

### After (Fixed):
- Gunicorn timeout: **180 seconds** (3 minutes)
- Graceful timeout: **200 seconds**
- Workers: **2** (optimized for Railway memory)
- **Result:** Requests complete successfully ✅

---

## How to Redeploy on Railway

### Option 1: Automatic (Recommended)
If you have GitHub integration enabled:
1. Railway will automatically detect the new commit
2. It will redeploy automatically
3. Wait for deployment to complete (~5-10 minutes)

### Option 2: Manual
1. Go to Railway dashboard
2. Click on your project
3. Click "Deploy" or "Redeploy"
4. Wait for deployment to complete

---

## Verifying Deployment

### 1. Check Deployment Logs
In Railway dashboard:
1. Go to "Deployments" tab
2. Click on latest deployment
3. Check logs for:
   ```
   Database initialized
   OpenAI API configured: True  ← Should be True!
   ```

### 2. Test the Application
1. Open your Railway app URL
2. Try generating a caption
3. Watch the debug console at the bottom
4. If it works: ✅ You're good!
5. If error: Copy logs and paste to Claude

---

## Common Issues

### Issue: Still getting 502 errors
**Causes:**
1. OPENAI_API_KEY not set → Set it in Railway env vars
2. Old deployment still running → Redeploy with latest code
3. Railway timeout (100s limit) → Already handled, but very complex requests might still timeout

**Solution:**
- Verify environment variable is set (no typos!)
- Redeploy with latest code
- Check Railway logs for actual error

### Issue: "OpenAI API configured: False" in logs
**Cause:** OPENAI_API_KEY environment variable not set

**Solution:**
1. Go to Railway project settings
2. Click "Variables" tab
3. Add: `OPENAI_API_KEY` = `your-key-here`
4. Redeploy

### Issue: Build fails
**Causes:**
- Node.js or Python version issues
- Dependency installation failures

**Solution:**
- Check Railway build logs
- Share error with Claude for help

---

## Performance Notes

### Expected Response Times:
- **Image upload:** 1-2 seconds
- **Image analysis (GPT-4o Vision):** 10-20 seconds
- **Local research (web scraping):** 5-15 seconds
- **Caption generation (GPT-5.1):** 30-90 seconds
- **Total:** 45-120 seconds (1-2 minutes)

This is normal! The debug console will show progress.

### Why so long?
- GPT-5.1 uses "reasoning" which takes time for better quality
- Web scraping for local research can be slow
- Vision API needs to process images/videos

### Can it be faster?
Yes, but with quality tradeoffs:
- Use GPT-4o instead of GPT-5.1 (faster, less reasoning)
- Reduce reasoning effort to "low" or "none"
- Skip local research (not recommended)

---

## Cost Estimates

### Per Caption:
- Image analysis (GPT-4o Vision): ~$0.01-0.02
- Caption generation (GPT-5.1, medium reasoning): ~$0.05-0.10
- **Total: ~$0.06-0.12 per caption**

### Monthly Estimates:
- 50 captions: $3-6/month
- 100 captions: $6-12/month
- 500 captions: $30-60/month

**Note:** Railway hosting is separate (~$5-10/month)

---

## Support

### Getting Help:
1. Check Railway deployment logs first
2. Use the debug console in the app (bottom of page)
3. Click "Copy Logs" and share with Claude
4. Include the error message from Railway logs

### Useful Links:
- OpenAI API Keys: https://platform.openai.com/api-keys
- Railway Dashboard: https://railway.app/dashboard
- GitHub Repo: https://github.com/AffanSyed321/Project-Caption

---

## Next Steps After Deployment

1. ✅ Verify environment variables are set
2. ✅ Redeploy with latest code
3. ✅ Test caption generation
4. ✅ Check debug logs
5. ✅ Start using Captionator!

---

**Last Updated:** 2025-11-20
**Fix Version:** Includes gunicorn timeout fix for 502 errors
