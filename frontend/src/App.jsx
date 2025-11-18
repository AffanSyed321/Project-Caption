import { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8000/api/v1';

function App() {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [goal, setGoal] = useState('');
  const [address, setAddress] = useState('');
  const [platform, setPlatform] = useState('Facebook');
  const [loading, setLoading] = useState(false);
  const [generatedCaption, setGeneratedCaption] = useState('');
  const [editedCaption, setEditedCaption] = useState('');
  const [locationInfo, setLocationInfo] = useState(null);
  const [error, setError] = useState('');
  const [saveMessage, setSaveMessage] = useState('');

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerate = async () => {
    if (!image || !goal || !address) {
      setError('Please fill in all fields and upload an image');
      return;
    }

    setLoading(true);
    setError('');
    setSaveMessage('');

    const formData = new FormData();
    formData.append('image', image);
    formData.append('goal', goal);
    formData.append('address', address);
    formData.append('platform', platform);

    try {
      const response = await axios.post(`${API_URL}/generate-caption`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setGeneratedCaption(response.data.caption);
      setEditedCaption(response.data.caption);
      setLocationInfo(response.data.location_info);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error generating caption. Make sure backend is running and API key is configured.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!image || !goal || !address) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');
    setSaveMessage('');

    const formData = new FormData();
    formData.append('image', image);
    formData.append('goal', goal);
    formData.append('address', address);
    formData.append('platform', platform);
    formData.append('previous_caption', generatedCaption);

    try {
      const response = await axios.post(`${API_URL}/regenerate-caption`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setGeneratedCaption(response.data.caption);
      setEditedCaption(response.data.caption);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error regenerating caption');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editedCaption || !goal) {
      setError('No caption to save');
      return;
    }

    setSaveMessage('');
    const formData = new FormData();
    formData.append('goal', goal);
    formData.append('caption', editedCaption);

    try {
      await axios.post(`${API_URL}/save-caption`, formData);
      setSaveMessage('Caption saved successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error saving caption');
      console.error(err);
    }
  };

  const handleReset = () => {
    setImage(null);
    setImagePreview(null);
    setGoal('');
    setAddress('');
    setPlatform('Facebook');
    setGeneratedCaption('');
    setEditedCaption('');
    setLocationInfo(null);
    setError('');
    setSaveMessage('');
  };

  return (
    <div className="container">
      <header>
        <h1>🎈 Urban Air Caption Generator</h1>
        <p>Create localized, authentic captions for your Urban Air locations</p>
      </header>

      <div className="main-content">
        {/* Left Panel - Input Form */}
        <div className="input-panel">
          <h2>Create Caption</h2>

          <div className="form-group">
            <label>Upload Image</label>
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="file-input"
            />
            {imagePreview && (
              <div className="image-preview">
                <img src={imagePreview} alt="Preview" />
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Post Goal</label>
            <input
              type="text"
              placeholder="e.g., Promote birthday parties, announce summer hours"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="text-input"
            />
          </div>

          <div className="form-group">
            <label>Urban Air Location Address</label>
            <input
              type="text"
              placeholder="e.g., 2051 Skibo Rd, Fayetteville, NC 28314"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="text-input"
            />
          </div>

          <div className="form-group">
            <label>Platform</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="select-input"
            >
              <option value="Facebook">Facebook</option>
              <option value="Instagram">Instagram</option>
            </select>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !image || !goal || !address}
            className="btn btn-primary"
          >
            {loading ? 'Generating...' : 'Generate Caption'}
          </button>

          {generatedCaption && (
            <button
              onClick={handleReset}
              className="btn btn-secondary"
              style={{ marginTop: '10px' }}
            >
              Start New Caption
            </button>
          )}
        </div>

        {/* Right Panel - Generated Caption */}
        <div className="output-panel">
          <h2>Generated Caption</h2>

          {locationInfo && (
            <div className="location-info">
              <strong>Location:</strong> {locationInfo.city}, {locationInfo.state}
              {locationInfo.is_rural && <span className="badge">Rural Area</span>}
            </div>
          )}

          {generatedCaption ? (
            <div className="caption-display">
              <textarea
                value={editedCaption}
                onChange={(e) => setEditedCaption(e.target.value)}
                className="caption-textarea"
                rows="12"
                placeholder="Your caption will appear here..."
              />

              <div className="action-buttons">
                <button
                  onClick={handleRegenerate}
                  disabled={loading}
                  className="btn btn-secondary"
                >
                  {loading ? 'Regenerating...' : '🔄 Regenerate'}
                </button>

                <button
                  onClick={handleSave}
                  className="btn btn-success"
                >
                  💾 Save Caption
                </button>
              </div>

              {saveMessage && <div className="success-message">{saveMessage}</div>}
            </div>
          ) : (
            <div className="empty-state">
              <p>👈 Fill out the form and click "Generate Caption" to get started</p>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}
        </div>
      </div>
    </div>
  );
}

export default App;
