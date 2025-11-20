import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Use relative path in production (works with any domain), localhost in development
const API_URL = import.meta.env.DEV
  ? 'http://localhost:8000/api/v1'
  : '/api/v1';

function App() {
  const [media, setMedia] = useState(null);
  const [mediaPreview, setMediaPreview] = useState(null);
  const [mediaType, setMediaType] = useState('image');
  const [goal, setGoal] = useState('');
  const [address, setAddress] = useState('');
  const [platform, setPlatform] = useState('Facebook');
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [generatedCaption, setGeneratedCaption] = useState('');
  const [editedCaption, setEditedCaption] = useState('');
  const [locationInfo, setLocationInfo] = useState(null);
  const [reasoning, setReasoning] = useState(null);
  const [qualityScores, setQualityScores] = useState(null);
  const [fullMediaAnalysis, setFullMediaAnalysis] = useState('');
  const [fullLocalResearch, setFullLocalResearch] = useState('');
  const [expandedSections, setExpandedSections] = useState({
    media: false,
    research: false,
    strategy: false
  });
  const [savedLocations, setSavedLocations] = useState([]);
  const [selectedLocationId, setSelectedLocationId] = useState('');
  const [error, setError] = useState('');
  const [saveMessage, setSaveMessage] = useState('');
  const [showChatEditor, setShowChatEditor] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // DEBUG LOGGING SYSTEM
  const [debugLogs, setDebugLogs] = useState([]);
  const [showDebugPanel, setShowDebugPanel] = useState(false);

  // Helper function to add debug logs
  const addLog = (type, message, data = null) => {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      type, // 'info', 'error', 'request', 'response'
      message,
      data: data ? JSON.stringify(data, null, 2) : null
    };

    console.log(`[${type.toUpperCase()}] ${message}`, data || '');

    setDebugLogs(prev => [...prev, logEntry]);
  };

  // Copy logs to clipboard
  const copyLogsToClipboard = () => {
    const logText = debugLogs.map(log =>
      `[${log.timestamp}] [${log.type.toUpperCase()}] ${log.message}${log.data ? '\n' + log.data : ''}`
    ).join('\n\n---\n\n');

    const fullLog = `=== CAPTIONATOR DEBUG LOG ===
Environment: ${import.meta.env.DEV ? 'DEVELOPMENT' : 'PRODUCTION'}
API URL: ${API_URL}
User Agent: ${navigator.userAgent}
Timestamp: ${new Date().toISOString()}

=== LOGS ===
${logText}`;

    navigator.clipboard.writeText(fullLog).then(() => {
      alert('Logs copied to clipboard!');
    }).catch(err => {
      alert('Failed to copy logs: ' + err.message);
    });
  };

  // Clear logs
  const clearLogs = () => {
    setDebugLogs([]);
  };

  useEffect(() => {
    // Log initialization
    addLog('info', 'App initialized', {
      environment: import.meta.env.DEV ? 'DEVELOPMENT' : 'PRODUCTION',
      apiUrl: API_URL,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    });

    // Load saved locations on mount
    loadLocations();
  }, []);

  const loadLocations = async () => {
    try {
      addLog('request', 'Loading saved locations', { url: `${API_URL}/locations` });

      const response = await axios.get(`${API_URL}/locations`);

      addLog('response', 'Locations loaded successfully', {
        status: response.status,
        locationCount: response.data.locations.length,
        locations: response.data.locations
      });

      setSavedLocations(response.data.locations);

      // If no saved locations and no location selected, default to "new" to show address input
      if (response.data.locations.length === 0 && !selectedLocationId) {
        setSelectedLocationId('new');
      }
    } catch (err) {
      addLog('error', 'Failed to load locations', {
        message: err.message,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        url: err.config?.url,
        stack: err.stack
      });
      console.error('Error loading locations:', err);
    }
  };

  const handleLocationSelect = (e) => {
    const value = e.target.value;
    setSelectedLocationId(value);

    if (value === 'new') {
      // User selected "Enter New Address" - clear address for manual entry
      setAddress('');
    } else if (value) {
      // User selected an existing location - fill in the address
      const location = savedLocations.find(loc => loc.id === parseInt(value));
      if (location) {
        setAddress(location.address);
      }
    } else {
      // User selected empty option - clear address
      setAddress('');
    }
  };

  const isVideo = (filename) => {
    const videoExtensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v'];
    return videoExtensions.some(ext => filename.toLowerCase().endsWith(ext));
  };

  const handleMediaChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setMedia(file);
      const type = isVideo(file.name) ? 'video' : 'image';
      setMediaType(type);

      const reader = new FileReader();
      reader.onloadend = () => {
        setMediaPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();

    addLog('info', 'Generate button clicked', {
      hasMedia: !!media,
      mediaType,
      mediaName: media?.name,
      mediaSize: media?.size,
      goal,
      address,
      platform
    });

    if (!media || !goal || !address) {
      const errorMsg = 'Please fill in all fields and upload an image or video';
      addLog('error', 'Validation failed', {
        hasMedia: !!media,
        hasGoal: !!goal,
        hasAddress: !!address
      });
      setError(errorMsg);
      return;
    }

    setLoading(true);
    setError('');
    setSaveMessage('');
    setReasoning(null);
    setQualityScores(null);

    const formData = new FormData();
    formData.append('media', media);
    formData.append('goal', goal);
    formData.append('address', address);
    formData.append('platform', platform);

    addLog('info', 'FormData prepared', {
      mediaFile: media.name,
      mediaSize: media.size,
      mediaType: media.type,
      goal,
      address,
      platform
    });

    try {
      // Show progress stages
      setLoadingStage(`Analyzing ${mediaType}...`);
      await new Promise(resolve => setTimeout(resolve, 500));

      setLoadingStage('Researching local area...');
      await new Promise(resolve => setTimeout(resolve, 500));

      setLoadingStage('Generating localized caption...');

      const requestUrl = `${API_URL}/generate-caption`;
      addLog('request', 'Sending generate caption request', {
        url: requestUrl,
        method: 'POST',
        contentType: 'multipart/form-data',
        fields: {
          mediaName: media.name,
          mediaType: media.type,
          mediaSize: media.size,
          goal,
          address,
          platform
        }
      });

      const response = await axios.post(requestUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      addLog('response', 'Caption generated successfully', {
        status: response.status,
        statusText: response.statusText,
        hasCaption: !!response.data.caption,
        captionLength: response.data.caption?.length,
        hasLocationInfo: !!response.data.location_info,
        hasReasoning: !!response.data.reasoning,
        hasQualityScores: !!response.data.quality_scores,
        responseData: response.data
      });

      setGeneratedCaption(response.data.caption);
      setEditedCaption(response.data.caption);
      setLocationInfo(response.data.location_info);
      setReasoning(response.data.reasoning);
      setQualityScores(response.data.quality_scores);
      setFullMediaAnalysis(response.data.media_analysis || '');
      setFullLocalResearch(response.data.location_info?.full_research || '');
      setError('');
      setLoadingStage('');

      // Reload locations in case a new one was saved
      loadLocations();
    } catch (err) {
      const errorDetail = err.response?.data?.detail || 'Error generating caption. Make sure backend is running and API key is configured.';

      addLog('error', 'Caption generation failed', {
        message: err.message,
        status: err.response?.status,
        statusText: err.response?.statusText,
        responseData: err.response?.data,
        requestUrl: err.config?.url,
        requestMethod: err.config?.method,
        headers: err.config?.headers,
        networkError: !err.response,
        errorStack: err.stack
      });

      setError(errorDetail);
      console.error('Caption generation error:', err);
      setLoadingStage('');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!media || !goal || !address) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');
    setSaveMessage('');

    const formData = new FormData();
    formData.append('media', media);
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
      setQualityScores(response.data.quality_scores);
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

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleReResearch = async () => {
    if (!address) {
      setError('Address is required to re-research');
      return;
    }

    setLoadingStage('Re-researching location...');

    try {
      const response = await axios.post(`${API_URL}/research-location`, {
        address: address
      });

      setFullLocalResearch(response.data.full_research || '');
      setLocationInfo(response.data.location_info);

      // Update reasoning with new research
      if (reasoning) {
        setReasoning({
          ...reasoning,
          local_research_summary: `✓ Re-researched ${response.data.location_info.city}, ${response.data.location_info.state}: ${response.data.full_research?.substring(0, 300)}...`
        });
      }

      setLoadingStage('');
      setSaveMessage('Location re-researched successfully! You may want to regenerate the caption.');
      setTimeout(() => setSaveMessage(''), 5000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error re-researching location');
      setLoadingStage('');
    }
  };

  const handleDeleteLocation = async () => {
    if (!selectedLocationId || selectedLocationId === 'new') return;

    if (window.confirm('Are you sure you want to delete this location?')) {
      try {
        await axios.delete(`${API_URL}/locations/${selectedLocationId}`);

        // Remove from saved locations
        setSavedLocations(prev => prev.filter(loc => loc.id !== parseInt(selectedLocationId)));

        // Reset selection
        setSelectedLocationId('');
        setAddress('');
        setSaveMessage('Location deleted successfully');
        setTimeout(() => setSaveMessage(''), 3000);
      } catch (err) {
        console.error('Error deleting location:', err);
        setError('Failed to delete location');
      }
    }
  };

  const handleChatEdit = async () => {
    if (!chatInput.trim()) return;

    setChatLoading(true);

    try {
      const formData = new FormData();
      formData.append('current_caption', editedCaption);
      formData.append('user_instruction', chatInput);
      formData.append('chat_history', JSON.stringify(chatHistory));
      formData.append('city', locationInfo.city);
      formData.append('state', locationInfo.state);
      formData.append('goal', goal);
      formData.append('platform', platform);

      const response = await axios.post(`${API_URL}/chat-edit-caption`, formData);

      // Update caption with AI response
      setEditedCaption(response.data.edited_caption);

      // Add to chat history
      const newHistory = [
        ...chatHistory,
        { role: 'user', content: chatInput },
        { role: 'assistant', content: response.data.edited_caption }
      ];
      setChatHistory(newHistory);
      setChatInput('');
    } catch (err) {
      console.error('Error editing caption:', err);
      setError('Failed to edit caption');
    } finally {
      setChatLoading(false);
    }
  };

  const handleReset = () => {
    setMedia(null);
    setMediaPreview(null);
    setMediaType('image');
    setGoal('');
    setAddress('');
    setSelectedLocationId('');
    setPlatform('Facebook');
    setGeneratedCaption('');
    setEditedCaption('');
    setLocationInfo(null);
    setReasoning(null);
    setQualityScores(null);
    setFullMediaAnalysis('');
    setFullLocalResearch('');
    setExpandedSections({ media: false, research: false, strategy: false });
    setError('');
    setSaveMessage('');
    setLoadingStage('');
  };

  return (
    <div className="container">
      <header>
        <h1>🎈 Captionator</h1>
        <p>Create localized, authentic captions for your Urban Air locations</p>
      </header>

      <div className="main-content">
        {/* Left Panel - Input Form */}
        <div className="input-panel">
          <h2>Create Caption</h2>

          <div className="form-group">
            <label>Upload Image or Video</label>
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleMediaChange}
              className="file-input"
            />
            {mediaPreview && (
              <div className="image-preview">
                {mediaType === 'video' ? (
                  <video src={mediaPreview} controls style={{ width: '100%', maxHeight: '300px' }} />
                ) : (
                  <img src={mediaPreview} alt="Preview" />
                )}
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
            <label>Urban Air Location</label>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <select
                value={selectedLocationId}
                onChange={handleLocationSelect}
                className="select-input"
                style={{ flex: 1 }}
              >
                <option value="">-- Select a location --</option>
                {savedLocations.map(loc => (
                  <option key={loc.id} value={loc.id}>
                    {loc.display}
                  </option>
                ))}
                <option value="new">+ Enter New Location</option>
              </select>

              {selectedLocationId && selectedLocationId !== 'new' && (
                <button
                  onClick={handleDeleteLocation}
                  className="btn-delete-icon"
                  title="Delete this location"
                  style={{
                    marginLeft: '10px',
                    background: '#ff4444',
                    color: 'white',
                    border: '2px solid #000',
                    borderRadius: '4px',
                    padding: '10px 15px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    boxShadow: '2px 2px 0px #000',
                    height: '46px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px'
                  }}
                >
                  🗑️
                </button>
              )}
            </div>
          </div>

          {selectedLocationId === 'new' && (
            <div className="form-group">
              <label>Enter New Address</label>
              <input
                type="text"
                placeholder="e.g., 2051 Skibo Rd, Fayetteville, NC 28314"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="text-input"
              />
            </div>
          )}

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
            disabled={loading || !media || !goal || !address}
            className="btn btn-primary"
          >
            {loading ? (loadingStage || 'Generating...') : 'Generate Caption'}
          </button>

          {loading && (
            <div style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
              <div>⏱️ Estimated time: 30-45 seconds</div>
              <div style={{ marginTop: '5px' }}>{loadingStage}</div>
            </div>
          )}

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
                  onClick={() => setShowChatEditor(!showChatEditor)}
                  className="btn btn-secondary"
                  style={{ background: showChatEditor ? '#ff6b35' : '#00d9ff' }}
                >
                  {showChatEditor ? '❌ Close Chat' : '💬 Edit with AI'}
                </button>

                <button
                  onClick={handleSave}
                  className="btn btn-success"
                >
                  💾 Save Caption
                </button>
              </div>

              {showChatEditor && (
                <div className="chat-editor" style={{
                  marginTop: '20px',
                  padding: '20px',
                  background: '#f0f8ff',
                  border: '4px solid #000',
                  borderRadius: '8px',
                  boxShadow: '6px 6px 0px #000'
                }}>
                  <h3 style={{ marginTop: 0, fontSize: '18px', fontWeight: 'bold' }}>
                    ✨ AI Caption Editor
                  </h3>
                  <p style={{ fontSize: '14px', color: '#666', marginBottom: '15px' }}>
                    Tell the AI how you'd like to change the caption. Examples: "make it shorter", "add more emojis", "make it more professional"
                  </p>

                  {chatHistory.length > 0 && (
                    <div style={{
                      maxHeight: '200px',
                      overflowY: 'auto',
                      marginBottom: '15px',
                      padding: '10px',
                      background: 'white',
                      border: '2px solid #000',
                      borderRadius: '4px'
                    }}>
                      {chatHistory.map((msg, idx) => (
                        <div key={idx} style={{
                          marginBottom: '10px',
                          padding: '8px',
                          background: msg.role === 'user' ? '#e3f2fd' : '#e8f5e9',
                          borderRadius: '4px',
                          fontSize: '13px'
                        }}>
                          <strong>{msg.role === 'user' ? '👤 You:' : '🤖 AI:'}</strong> {msg.content}
                        </div>
                      ))}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input
                      type="text"
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleChatEdit()}
                      placeholder="Type your instruction..."
                      disabled={chatLoading}
                      style={{
                        flex: 1,
                        padding: '12px',
                        border: '2px solid #000',
                        borderRadius: '4px',
                        fontSize: '14px'
                      }}
                    />
                    <button
                      onClick={handleChatEdit}
                      disabled={chatLoading || !chatInput.trim()}
                      className="btn btn-primary"
                      style={{ minWidth: '100px' }}
                    >
                      {chatLoading ? '✨...' : '✨ Apply'}
                    </button>
                  </div>
                </div>
              )}

              {saveMessage && <div className="success-message">{saveMessage}</div>}

              {qualityScores && (
                <div className="quality-scores-section" style={{
                  marginTop: '20px',
                  padding: '20px',
                  background: qualityScores.quality_tier === 'Excellent' ? '#e8f5e9' :
                    qualityScores.quality_tier === 'Good' ? '#e3f2fd' :
                      qualityScores.quality_tier === 'Fair' ? '#fff3e0' : '#ffebee',
                  borderRadius: '8px',
                  border: '2px solid ' + (qualityScores.quality_tier === 'Excellent' ? '#4caf50' :
                    qualityScores.quality_tier === 'Good' ? '#2196f3' :
                      qualityScores.quality_tier === 'Fair' ? '#ff9800' : '#f44336')
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <h3 style={{ fontSize: '18px', margin: 0, color: '#333' }}>
                      ⭐ Quality Analysis
                    </h3>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                      <span style={{
                        padding: '6px 12px',
                        borderRadius: '20px',
                        fontSize: '14px',
                        fontWeight: 'bold',
                        background: qualityScores.quality_tier === 'Excellent' ? '#4caf50' :
                          qualityScores.quality_tier === 'Good' ? '#2196f3' :
                            qualityScores.quality_tier === 'Fair' ? '#ff9800' : '#f44336',
                        color: 'white'
                      }}>
                        {qualityScores.quality_tier}
                      </span>
                      <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#333' }}>
                        {qualityScores.overall_score}/100
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
                    {[
                      { label: 'Brand Consistency', score: qualityScores.brand_consistency },
                      { label: 'Local Relevance', score: qualityScores.local_relevance },
                      { label: 'Goal Alignment', score: qualityScores.goal_alignment },
                      { label: 'Overall Quality', score: qualityScores.overall_quality }
                    ].map(item => (
                      <div key={item.label}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', fontSize: '13px' }}>
                          <span style={{ fontWeight: '500', color: '#555' }}>{item.label}</span>
                          <span style={{ fontWeight: 'bold', color: '#333' }}>{item.score}/100</span>
                        </div>
                        <div style={{
                          width: '100%',
                          height: '8px',
                          background: '#e0e0e0',
                          borderRadius: '4px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${item.score}%`,
                            height: '100%',
                            background: item.score >= 90 ? '#4caf50' :
                              item.score >= 80 ? '#2196f3' :
                                item.score >= 70 ? '#ff9800' : '#f44336',
                            transition: 'width 0.3s ease'
                          }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  {qualityScores.strengths && qualityScores.strengths.length > 0 && (
                    <div style={{ marginBottom: '10px' }}>
                      <strong style={{ color: '#2e7d32', fontSize: '14px' }}>✓ Strengths:</strong>
                      <ul style={{ margin: '5px 0', paddingLeft: '20px', fontSize: '13px', color: '#555' }}>
                        {qualityScores.strengths.map((strength, idx) => (
                          <li key={idx} style={{ marginBottom: '3px' }}>{strength}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {qualityScores.issues && qualityScores.issues.length > 0 && qualityScores.issues[0] !== "Could not analyze automatically" && (
                    <div style={{ marginBottom: '10px' }}>
                      <strong style={{ color: '#c62828', fontSize: '14px' }}>⚠ Issues:</strong>
                      <ul style={{ margin: '5px 0', paddingLeft: '20px', fontSize: '13px', color: '#555' }}>
                        {qualityScores.issues.map((issue, idx) => (
                          <li key={idx} style={{ marginBottom: '3px' }}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {qualityScores.recommendation && (
                    <div style={{
                      marginTop: '10px',
                      padding: '10px',
                      background: 'rgba(255,255,255,0.5)',
                      borderRadius: '6px',
                      fontSize: '13px',
                      fontWeight: '500',
                      color: '#333'
                    }}>
                      <strong>Recommendation:</strong> {qualityScores.recommendation}
                    </div>
                  )}
                </div>
              )}

              {reasoning && (
                <div className="reasoning-section" style={{
                  marginTop: '20px',
                  padding: '15px',
                  background: '#f8f9fa',
                  borderRadius: '8px',
                  fontSize: '14px',
                  lineHeight: '1.6'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <h3 style={{ fontSize: '16px', margin: 0, color: '#333' }}>
                      📊 Caption Generation Process
                    </h3>
                    <button
                      onClick={handleReResearch}
                      disabled={loadingStage === 'Re-researching location...'}
                      className="btn btn-secondary"
                      style={{
                        padding: '6px 12px',
                        fontSize: '13px',
                        background: '#6c757d',
                        border: 'none',
                        borderRadius: '4px',
                        color: 'white',
                        cursor: 'pointer'
                      }}
                    >
                      {loadingStage === 'Re-researching location...' ? '🔄 Researching...' : '🔄 Re-research Location'}
                    </button>
                  </div>

                  {/* Media Analysis Section */}
                  <div style={{ marginBottom: '15px', padding: '12px', background: 'white', borderRadius: '6px', border: '1px solid #e0e0e0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <strong style={{ color: '#333' }}>Media Analysis:</strong>
                      <button
                        onClick={() => toggleSection('media')}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#2196f3',
                          cursor: 'pointer',
                          fontSize: '13px',
                          fontWeight: '500'
                        }}
                      >
                        {expandedSections.media ? '▼ Show Less' : '▶ Show Full Analysis'}
                      </button>
                    </div>
                    <div style={{ color: '#555' }}>
                      {expandedSections.media ? (
                        <div style={{ whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto', padding: '8px', background: '#fafafa', borderRadius: '4px' }}>
                          {fullMediaAnalysis || reasoning.media_confirmation}
                        </div>
                      ) : (
                        <div>{reasoning.media_confirmation}</div>
                      )}
                    </div>
                  </div>

                  {/* Local Research Section */}
                  <div style={{ marginBottom: '15px', padding: '12px', background: 'white', borderRadius: '6px', border: '1px solid #e0e0e0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <strong style={{ color: '#333' }}>Local Research:</strong>
                      <button
                        onClick={() => toggleSection('research')}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#2196f3',
                          cursor: 'pointer',
                          fontSize: '13px',
                          fontWeight: '500'
                        }}
                      >
                        {expandedSections.research ? '▼ Show Less' : '▶ Show Full Research'}
                      </button>
                    </div>
                    <div style={{ color: '#555' }}>
                      {expandedSections.research ? (
                        <div style={{ whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto', padding: '8px', background: '#fafafa', borderRadius: '4px' }}>
                          {fullLocalResearch || reasoning.local_research_summary}
                        </div>
                      ) : (
                        <div>{reasoning.local_research_summary}</div>
                      )}
                    </div>
                  </div>

                  {/* Caption Strategy Section */}
                  <div style={{ padding: '12px', background: 'white', borderRadius: '6px', border: '1px solid #e0e0e0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <strong style={{ color: '#333' }}>Caption Strategy:</strong>
                      <button
                        onClick={() => toggleSection('strategy')}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#2196f3',
                          cursor: 'pointer',
                          fontSize: '13px',
                          fontWeight: '500'
                        }}
                      >
                        {expandedSections.strategy ? '▼ Show Less' : '▶ Show More'}
                      </button>
                    </div>
                    <div style={{ color: '#555' }}>
                      {expandedSections.strategy ? (
                        <div style={{ whiteSpace: 'pre-wrap', padding: '8px', background: '#fafafa', borderRadius: '4px' }}>
                          {reasoning.caption_strategy}

                          {locationInfo && (
                            <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #e0e0e0' }}>
                              <strong>Location Details:</strong>
                              <ul style={{ marginTop: '5px', paddingLeft: '20px' }}>
                                <li>City: {locationInfo.city}</li>
                                <li>State: {locationInfo.state}</li>
                                <li>Area Type: {locationInfo.is_rural ? 'Rural' : 'Urban/Suburban'}</li>
                              </ul>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div>{reasoning.caption_strategy}</div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <p>👈 Fill out the form and click "Generate Caption" to get started</p>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}
        </div>
      </div>

      {/* DEBUG PANEL */}
      <div style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        background: '#1e1e1e',
        color: '#d4d4d4',
        borderTop: '2px solid #007acc',
        zIndex: 9999,
        maxHeight: showDebugPanel ? '400px' : '40px',
        transition: 'max-height 0.3s ease',
        overflow: 'hidden',
        fontFamily: 'monospace',
        fontSize: '12px'
      }}>
        {/* Debug Panel Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 16px',
          background: '#252526',
          borderBottom: showDebugPanel ? '1px solid #3e3e42' : 'none',
          cursor: 'pointer'
        }} onClick={() => setShowDebugPanel(!showDebugPanel)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '16px' }}>{showDebugPanel ? '▼' : '▶'}</span>
            <strong style={{ color: '#4ec9b0' }}>🐛 Debug Console</strong>
            <span style={{
              background: debugLogs.length > 0 ? '#007acc' : '#666',
              padding: '2px 8px',
              borderRadius: '10px',
              fontSize: '11px',
              color: 'white'
            }}>
              {debugLogs.length} logs
            </span>
            {debugLogs.some(log => log.type === 'error') && (
              <span style={{
                background: '#d32f2f',
                padding: '2px 8px',
                borderRadius: '10px',
                fontSize: '11px',
                color: 'white'
              }}>
                {debugLogs.filter(log => log.type === 'error').length} errors
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                copyLogsToClipboard();
              }}
              style={{
                background: '#007acc',
                border: 'none',
                color: 'white',
                padding: '4px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: 'bold'
              }}
            >
              📋 Copy Logs
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearLogs();
              }}
              style={{
                background: '#d32f2f',
                border: 'none',
                color: 'white',
                padding: '4px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              🗑️ Clear
            </button>
          </div>
        </div>

        {/* Debug Panel Content */}
        {showDebugPanel && (
          <div style={{
            padding: '12px',
            overflowY: 'auto',
            maxHeight: '360px',
            background: '#1e1e1e'
          }}>
            {debugLogs.length === 0 ? (
              <div style={{ color: '#888', textAlign: 'center', padding: '20px' }}>
                No logs yet. Interact with the app to see debug information.
              </div>
            ) : (
              debugLogs.map((log, idx) => (
                <div key={idx} style={{
                  marginBottom: '12px',
                  padding: '10px',
                  background: '#252526',
                  borderRadius: '4px',
                  borderLeft: `3px solid ${
                    log.type === 'error' ? '#d32f2f' :
                    log.type === 'request' ? '#ff9800' :
                    log.type === 'response' ? '#4caf50' :
                    '#2196f3'
                  }`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{
                      color: log.type === 'error' ? '#f48771' :
                             log.type === 'request' ? '#ffb74d' :
                             log.type === 'response' ? '#81c784' :
                             '#64b5f6',
                      fontWeight: 'bold',
                      textTransform: 'uppercase',
                      fontSize: '10px'
                    }}>
                      {log.type}
                    </span>
                    <span style={{ color: '#858585', fontSize: '10px' }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ color: '#d4d4d4', marginBottom: '6px' }}>
                    {log.message}
                  </div>
                  {log.data && (
                    <details style={{ marginTop: '6px' }}>
                      <summary style={{ color: '#569cd6', cursor: 'pointer', fontSize: '11px' }}>
                        Show Details
                      </summary>
                      <pre style={{
                        marginTop: '6px',
                        padding: '8px',
                        background: '#1e1e1e',
                        borderRadius: '4px',
                        overflowX: 'auto',
                        fontSize: '11px',
                        color: '#ce9178'
                      }}>
                        {log.data}
                      </pre>
                    </details>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
