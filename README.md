# Captionator

A web platform that generates localized, audience-specific social media captions for Urban Air Adventure Park locations. The system uses AI to research local demographics, culture, and community characteristics, then creates captions that resonate with each location's unique audience.

## Features

- **Image Analysis**: Upload promotional graphics and AI analyzes the visual content
- **Local Research**: Automatically researches chamber of commerce and government websites to understand local culture
- **Smart Caption Generation**: Creates authentic, localized captions (not generic templates)
- **Platform Optimization**: Optimized for Facebook or Instagram
- **Edit & Regenerate**: Edit captions manually or generate new variations
- **Population Awareness**: Adjusts search radius for rural vs urban areas
- **Caption History**: Save and retrieve past captions

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI
- SQLite
- OpenAI GPT-4o + Vision API
- BeautifulSoup4 (web scraping)

**Frontend:**
- React (Vite)
- Axios
- Modern CSS

**Deployment:**
- Railway

## Local Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API Key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
```

6. Run the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

API docs at `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Using the Application

1. **Upload an Image**: Choose a promotional graphic for your post
2. **Enter Goal**: Describe what the post should achieve (e.g., "Promote birthday parties")
3. **Enter Address**: Provide the full Urban Air location address (e.g., "123 Main St, Springfield, IL 62701")
4. **Select Platform**: Choose Facebook or Instagram
5. **Generate**: Click "Generate Caption" and wait for AI processing
6. **Edit**: Modify the caption as needed in the text area
7. **Regenerate**: Click regenerate for a different version if desired
8. **Save**: Save your final caption to the database

## How It Works

### Workflow

1. **Image Analysis**
   - OpenAI Vision API analyzes the uploaded image
   - Identifies activities, mood, promotions, and target demographic

2. **Local Research**
   - Extracts city and state from address
   - Searches chamber of commerce websites
   - Searches official government/city websites
   - Analyzes population density (rural vs urban)

3. **Caption Generation**
   - GPT-4o combines:
     - Image analysis
     - Local research findings
     - Post goal
     - Platform requirements
   - Generates authentic, localized caption
   - Avoids generic templates

4. **Iteration**
   - User can edit caption manually
   - Regenerate for new variations
   - Save final version to database

## Deployment to Railway

### Backend Deployment

1. Create a new Railway project
2. Connect your GitHub repository
3. Select the `backend` folder as the root directory
4. Add environment variables in Railway dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `PORT`: Auto-configured by Railway

5. Railway will auto-detect Python and deploy using the `railway.json` configuration

### Frontend Deployment

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Deploy the `dist` folder to a static hosting service (Railway, Vercel, Netlify)
3. Update the `API_URL` in `frontend/src/App.jsx` to point to your Railway backend URL

**OR** serve frontend from backend:
- Copy `frontend/dist` contents to `backend/static`
- Update FastAPI to serve static files

## Environment Variables

**Backend (.env):**
```
OPENAI_API_KEY=your_openai_api_key_here
API_V1_STR=/api/v1
PROJECT_NAME=Urban Air Caption Generator
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://your-frontend-url.com
```

## API Endpoints

- `POST /api/v1/generate-caption` - Generate new caption
- `POST /api/v1/regenerate-caption` - Regenerate different version
- `POST /api/v1/save-caption` - Save caption to database
- `GET /api/v1/captions` - Retrieve saved captions
- `GET /api/v1/health` - Health check

## Project Structure

```
urban-air-caption-generator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # API endpoints
│   │   ├── core/
│   │   │   ├── config.py          # Configuration
│   │   │   └── database.py        # Database setup
│   │   ├── models/
│   │   │   └── caption.py         # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── local_research.py  # Web scraping service
│   │   │   └── openai_service.py  # OpenAI integration
│   │   └── main.py                # FastAPI app
│   ├── requirements.txt
│   ├── railway.json
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main React component
│   │   └── App.css                # Styling
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Future Enhancements

- [ ] Integration with Census API for accurate population data
- [ ] More sophisticated web scraping with multiple sources
- [ ] Caption analytics and performance tracking
- [ ] Multi-user support with authentication
- [ ] Direct social media posting
- [ ] Caption templates library
- [ ] A/B testing for captions
- [ ] Hashtag research and optimization

## Troubleshooting

**Backend won't start:**
- Check Python version (3.10+)
- Verify OpenAI API key is set in `.env`
- Check all dependencies are installed

**Frontend can't connect to backend:**
- Verify backend is running on port 8000
- Check CORS settings in `backend/app/core/config.py`
- Update `API_URL` in `frontend/src/App.jsx` if needed

**Caption generation fails:**
- Verify OpenAI API key is valid
- Check API usage limits
- Ensure image file is valid format
- Check backend logs for errors

**Web scraping doesn't work:**
- Many government/chamber sites may block scrapers
- Consider using official APIs where available
- Implement retry logic and fallbacks

## License

Proprietary - Urban Air Adventure Park

## Support

For issues or questions, contact the development team.
# Force Railway rebuild - Wed Nov 19 20:49:11 CST 2025
# Updated Wed Nov 19 20:57:05 CST 2025
