const express = require('express');
const app = express();
const port = 3000;
const axios = require('axios');
const cors = require('cors');
const querystring = require('querystring');
const path = require('path');
const fs = require('fs');
const cookieParser = require('cookie-parser');
const { Parser } = require('json2csv');
require('dotenv').config();

// Constants
const SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize';
const SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token';
const SPOTIFY_CLIENT_CREDENTIALS_TOKEN_URL = 'https://accounts.spotify.com/api/token';

// Middleware
app.use(express.static('public'));
app.use(cors());
app.use(cookieParser());

// Helper function to refresh access token
async function refreshAccessToken(refreshToken) {
  try {
    const { data } = await axios.post(
      SPOTIFY_TOKEN_URL,
      new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: refreshToken,
        client_id: process.env.SPOTIFY_CLIENT_ID,
        client_secret: process.env.SPOTIFY_CLIENT_SECRET,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );
    return data.access_token;
  } catch (error) {
    console.error('Token refresh failed:', error.response?.data || error.message);
    return null;
  }
}
app.get('/me', validateToken, async (req, res) => {
  const accessToken = req.cookies.spotify_access_token;

  try {
    const response = await axios.get('https://api.spotify.com/v1/me', {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });

    res.json(response.data);  // shows user info + scopes in terminal

  } catch (error) {
    console.error('Token check failed:', error.response?.data || error.message);
    res.status(401).send('Invalid or expired token — please re-authenticate.');
  }
});
// Middleware to validate and refresh token if needed
async function validateToken(req, res, next) {
  const accessToken = req.cookies.spotify_access_token;
  const refreshToken = req.cookies.spotify_refresh_token;

  if (!accessToken) {
    return res.redirect('/login');
  }

  try {
    // Test the token with a simple request
    await axios.get('https://api.spotify.com/v1/me', {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    return next();
  } catch (error) {
    if (error.response?.status === 401 && refreshToken) {
      // Token expired - try to refresh it
      const newToken = await refreshAccessToken(refreshToken);
      if (newToken) {
        res.cookie('spotify_access_token', newToken, { httpOnly: true });
        req.cookies.spotify_access_token = newToken;
        return next();
      }
    }
    // If we get here, authentication failed
    res.clearCookie('spotify_access_token');
    res.clearCookie('spotify_refresh_token');
    return res.redirect('/login');
  }
}

async function getClientCredentialsToken() {
  try {
    const { data } = await axios.post(
      SPOTIFY_CLIENT_CREDENTIALS_TOKEN_URL,
      new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: process.env.SPOTIFY_CLIENT_ID,
        client_secret: process.env.SPOTIFY_CLIENT_SECRET
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );
    return data.access_token;
  } catch (error) {
    console.error('Client credentials token error:', error.response?.data || error.message);
    return null;
  }
}

// Routes
app.get('/login', (req, res) => {
  const scope = [
    'user-library-read',       // To read saved tracks
    'user-top-read',           // To read top tracks/artists
    'user-read-private',       // To read user details
    'user-read-email',         // To read user email
    'user-read-recently-played', // To read recently played tracks
    'user-read-playback-state'
  ].join(' ');

  res.redirect(`${SPOTIFY_AUTH_URL}?${querystring.stringify({
    response_type: 'code',
    client_id: process.env.SPOTIFY_CLIENT_ID,
    scope: scope,
    redirect_uri: process.env.SPOTIFY_REDIRECT_URI,
    show_dialog: true // This forces the approval dialog to show every time
  })}`);
});

async function getAudioFeaturesWithFallback(trackIds, userToken) {
  const audioFeatures = {};
  const batchSize = 50; // Conservative batch size
  
  // First try with user token
  let token = userToken;
  let tokenType = 'user';
  
  for (let i = 0; i < trackIds.length; i += batchSize) {
    const batch = trackIds.slice(i, i + batchSize);
    try {
      const { data } = await axios.get(
        `https://api.spotify.com/v1/audio-features?ids=${batch.join(',')}`,
        {
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json'
          },
          timeout: 10000
        }
      );

      (data.audio_features || []).forEach(feature => {
        if (feature) audioFeatures[feature.id] = feature;
      });
      
    } catch (error) {
      console.error(`Batch ${i}-${i+batchSize} failed with ${tokenType} token:`, error.message);
      
      // If first failure, try switching to client credentials
      if (tokenType === 'user') {
        token = await getClientCredentialsToken();
        tokenType = 'client';
        if (!token) break; // No fallback token available
        
        // Retry the same batch with client token
        i -= batchSize; // Reset the loop counter to retry this batch
        continue;
      }
      
      // If already using client credentials and still failing, try individual requests
      for (const trackId of batch) {
        try {
          const { data } = await axios.get(
            `https://api.spotify.com/v1/audio-features/${trackId}`,
            { headers: { 'Authorization': `Bearer ${token}` } }
          );
          audioFeatures[trackId] = data;
        } catch (err) {
          console.error(`Failed for single track ${trackId}:`, err.message);
        }
      }
    }
    
    // Small delay between batches
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  
  return audioFeatures;
}

app.get('/callback', async (req, res) => {
  const { code, error } = req.query;

  if (error) {
    console.error('Spotify auth error:', error);
    return res.redirect('/?error=' + encodeURIComponent(error));
  }

  try {
    const { data } = await axios.post(
      SPOTIFY_TOKEN_URL,
      new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: process.env.SPOTIFY_REDIRECT_URI,
        client_id: process.env.SPOTIFY_CLIENT_ID,
        client_secret: process.env.SPOTIFY_CLIENT_SECRET,
      }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );

    // Log granted scopes for debugging purposes
    console.log("Granted scopes:", data.scope);

    // Set cookies
    res.cookie('spotify_access_token', data.access_token, { httpOnly: true, maxAge: 3600000 });  // 1 hour
    res.cookie('spotify_refresh_token', data.refresh_token, { httpOnly: true });

    // Redirect to dashboard or wherever needed
    res.redirect('/dashboard');

  } catch (error) {
    console.error('Token error:', error.response?.data || error.message);
    res.redirect('/?error=auth_failed');
  }
});

app.get('/dashboard', async (req, res) => {
  let accessToken = req.cookies.spotify_access_token;
  const refreshToken = req.cookies.spotify_refresh_token;

  try {
    // Force a refresh of the token in case the cookie one is stale
    const newToken = await refreshAccessToken(refreshToken);
    if (newToken) {
      accessToken = newToken;
      res.cookie('spotify_access_token', newToken, { httpOnly: true });
      console.log('🔁 Refreshed access token:', newToken);
    } else {
      throw new Error('Failed to refresh access token.');
    }

    // Get user's top tracks
    const { data: topTracksData } = await axios.get(
      'https://api.spotify.com/v1/me/top/tracks?limit=50&time_range=short_term',
      {
        headers: { Authorization: `Bearer ${accessToken}` },
        timeout: 10000
      }
    );

    if (!topTracksData.items?.length) {
      throw new Error('No top tracks returned from Spotify');
    }

    const allTracks = topTracksData.items.map(item => ({
      id: item.id,
      name: item.name,
      artistIds: item.artists.map(a => a.id),
      artists: item.artists.map(a => ({ id: a.id, name: a.name })),
      album: { id: item.album.id, name: item.album.name },
      duration_ms: item.duration_ms,
      popularity: item.popularity
    }));

    const trackIds = [...new Set(allTracks.map(t => t.id))];
    const artistIds = [...new Set(allTracks.flatMap(t => t.artistIds))];

    console.log('Attempting audio features with token:', accessToken.substring(0, 10) + '...');

    // Test audio features for a known track
    try {
      const testTrackId = '3n3Ppam7vgaVa1iaRUc9Lp';
      const { data } = await axios.get(
        `https://api.spotify.com/v1/audio-features?ids=${testTrackId}`,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
          timeout: 10000
        }
      );
      console.log('✅ Test audio features OK:', data);
    } catch (e) {
      console.error('❌ Audio feature test failed (403?):', e.response?.status, e.response?.data || e.message);
    }

    // Fetch audio features
    // const audioFeatures = {};
    // for (let i = 0; i < trackIds.length; i += 100) {
    //   const batch = trackIds.slice(i, i + 100);
    //   try {
    //     const { data } = await axios.get(
    //       `https://api.spotify.com/v1/audio-features?ids=${batch.join(',')}`,
    //       {
    //         headers: { Authorization: `Bearer ${accessToken}` },
    //         timeout: 10000
    //       }
    //     );
    //     (data.audio_features || []).forEach(f => {
    //       if (f) {
    //         const { key, mode, ...rest } = f;
    //         audioFeatures[f.id] = rest;
    //       }
    //     });
    //   } catch (err) {
    //     console.error('❌ Failed to fetch batch audio features:', err.response?.status, err.response?.data || err.message);
    //   }
    // }

    const audioFeatures = await getAudioFeaturesWithFallback(trackIds, req.cookies.spotify_access_token);
  
  if (Object.keys(audioFeatures).length === 0) {
    console.error('No audio features could be retrieved');
    return res.status(500).send('Failed to retrieve audio features');
  }

    // Fetch genres for artists
    const artistGenres = {};
    for (let i = 0; i < artistIds.length; i += 50) {
      const batch = artistIds.slice(i, i + 50);
      try {
        const { data } = await axios.get(
          `https://api.spotify.com/v1/artists?ids=${batch.join(',')}`,
          {
            headers: { Authorization: `Bearer ${accessToken}` },
            timeout: 10000
          }
        );
        data.artists.forEach(a => {
          artistGenres[a.id] = a.genres || [];
        });
      } catch (err) {
        console.error('❌ Failed to fetch genres:', err.response?.status, err.response?.data || err.message);
      }
    }

    // Assemble final track data
    const finalTracks = allTracks.map(t => ({
      id: t.id,
      name: t.name,
      artists: t.artists.map(a => a.name).join(', '),
      album: t.album.name,
      popularity: t.popularity,
      genres: t.artists.flatMap(a => artistGenres[a.id] || []).join(', '),
      duration_ms: t.duration_ms,
      ...(audioFeatures[t.id] || {})
    }));

    // Save to CSV
    try {
      const dataDir = path.join(__dirname, 'data');
      if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

      const timestamp = Date.now();
      const csvFilename = path.join(dataDir, `top_tracks_${timestamp}.csv`);
      const parser = new Parser({ fields: Object.keys(finalTracks[0]) });
      const csv = parser.parse(finalTracks);

      fs.writeFileSync(csvFilename, csv);
      console.log(`✅ CSV saved: ${csvFilename}`);

      return res.redirect('/dashboard.html');
    } catch (fileError) {
      console.error('❌ Failed to save file:', fileError.message);
      return res.status(500).send('Data processed but file saving failed');
    }

  } catch (err) {
    console.error('❌ Dashboard error:', err.response?.data || err.message);
    res.status(500).send('Dashboard failed: ' + err.message);
  }
});


app.get('/test-client-auth', async (req, res) => {
  try {
    const token = await getClientCredentialsToken();
    if (!token) {
      return res.status(500).json({ error: 'Failed to get client token' });
    }

    const testTrackId = '11dFghVXANMlKmJXsNCbNl'; // Coldplay - Fix You
    const { data } = await axios.get(
      `https://api.spotify.com/v1/audio-features/${testTrackId}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    res.json({
      success: true,
      tokenType: 'client_credentials',
      features: data
    });
  } catch (error) {
    res.status(500).json({
      error: error.message,
      details: error.response?.data
    });
  }
});

// Start server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
