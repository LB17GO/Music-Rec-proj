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

// Middleware
app.use(express.static('public'));
app.use(cors());
app.use(cookieParser());
client_id = process.env.SPOTIFY_CLIENT_ID;
client_secret = process.env.SPOTIFY_CLIENT_SECRET;

// Helper function to refresh access token
async function refreshSpotifyToken(refresh_token) {
  const tokenEndpoint = 'https://accounts.spotify.com/api/token';

  const data = querystring.stringify({
    grant_type: 'refresh_token',
    refresh_token: refresh_token,
  });

  const authHeader = Buffer.from(`${client_id}:${client_secret}`).toString('base64');

  try {
    const response = await axios.post(tokenEndpoint, data, {
      headers: {
        'Authorization': `Basic ${authHeader}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const accessToken = response.data.access_token;
    console.log('✅ Refreshed Access Token:', accessToken);
    return accessToken;
  } catch (error) {
    console.error('❌ Error refreshing token:', error.response?.data || error.message);
    throw error;
  }
}

// Middleware to validate and refresh token if needed
async function validateToken(req, res, next) {
  const accessToken = req.cookies.spotify_access_token;
  const refreshToken = req.cookies.spotify_refresh_token;

  if (!accessToken) {
    return res.redirect('/login');
  }

  try {
    await axios.get('https://api.spotify.com/v1/me', {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    });
    return next();
  } catch (error) {
    if (error.response?.status === 401 && refreshToken) {
      const newToken = await refreshAccessToken(refreshToken);
      if (newToken) {
        res.cookie('spotify_access_token', newToken, { httpOnly: true });
        req.cookies.spotify_access_token = newToken;
        return next();
      }
    }
    res.clearCookie('spotify_access_token');
    res.clearCookie('spotify_refresh_token');
    return res.redirect('/login');
  }
}

// Routes
app.get('/login', (req, res) => {
  const scope = [
    'user-library-read',
    'user-top-read',
    'user-read-private',
    'user-read-email',
    'user-read-recently-played',
    'user-read-playback-state'
  ].join(' ');

  res.redirect(`${SPOTIFY_AUTH_URL}?${querystring.stringify({
    response_type: 'code',
    client_id: process.env.SPOTIFY_CLIENT_ID,
    scope: scope,
    redirect_uri: process.env.SPOTIFY_REDIRECT_URI,
    show_dialog: true
  })}`);
});

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

    res.cookie('spotify_access_token', data.access_token, { httpOnly: true, maxAge: 3600000 });
    res.cookie('spotify_refresh_token', data.refresh_token, { httpOnly: true });

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
    const newToken = await refreshSpotifyToken(refreshToken);
    if (newToken) {
      accessToken = newToken;
      res.cookie('spotify_access_token', newToken, { httpOnly: true });
      console.log('🔁 Refreshed access token:');
    } else {
      throw new Error('Failed to refresh access token.');
    }

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
    }));

    // Assemble final track data
    const finalTracks = allTracks.map(t => ({
      id: t.id,
      name: t.name,
    }));

    // Save to a fixed file: "web_top_songs.csv"
    try {
      const dataDir = path.join(__dirname, 'data');
      if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

      const csvFilename = path.join(dataDir, 'web_top_songs.csv');
      const parser = new Parser({ fields: Object.keys(finalTracks[0]) });
      const csv = parser.parse(finalTracks);

      fs.writeFileSync(csvFilename, csv);
      console.log(`✅ CSV saved to: ${csvFilename}`);

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

const { execFile } = require('child_process'); 
app.get('/run-algorithm', async (req, res) => {
  console.log("✅ /run-algorithm called");
  refreshToken = req.cookies.spotify_refresh_token;

  try {
    const dataDir = path.join(__dirname, 'data');
    const modelPath = path.join(__dirname, 'model.pkl');
    const accessToken = await refreshSpotifyToken(refreshToken);

    // Find latest CSV file
    const files = fs.readdirSync(dataDir)
      .filter(f => f.endsWith('.csv'))
      .map(f => ({ name: f, time: fs.statSync(path.join(dataDir, f)).mtime.getTime() }))
      .sort((a, b) => b.time - a.time);

    if (!files.length) {
      return res.status(404).send('No CSV file found');
    }

    const latestCsv = path.join(dataDir, files[0].name);
    console.log

    // Run the Python script
    execFile('/usr/bin/python3', [path.join(__dirname, '..', 'code', 'hybrid_filtering.py')], async (error, stdout, stderr) => {
      console.log(latestCsv);
      if (error) {
        console.error('Python error:', error, stderr);
        return res.status(500).send('Failed to run algorithm.');
      }

      try {
        const songIds = JSON.parse(stdout); // list of Spotify song IDs
        
        if (!songIds.length) {
          return res.status(404).send('No songs returned from model.');
        }

        // Batch fetch track info from Spotify
        const batches = [];
        const batchSize = 50; // Spotify API limit is 50 IDs at once

        for (let i = 0; i < songIds.length; i += batchSize) {
          batches.push(songIds.slice(i, i + batchSize));
        }

        let allTracks = [];

        for (const batch of batches) {
          const { data } = await axios.get(
            `https://api.spotify.com/v1/tracks?ids=${batch.join(',')}`,
            { headers: { Authorization: `Bearer ${accessToken}` } }
          );

          allTracks = allTracks.concat(data.tracks.map(track => ({
            id: track.id,
            name: track.name,
            artist: track.artists.map(a => a.name).join(', '),
            albumImage: track.album.images[0]?.url || null
          })));
        }

        res.json({ recommendedTracks: allTracks });

      } catch (parseError) {
        console.error('Failed to parse Python output:', parseError);
        res.status(500).send('Algorithm ran but output was invalid.');
      }
    });

  } catch (err) {
    console.error('Run algorithm error:', err.message);
    res.status(500).send('Internal server error');
  }
});


// Start server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
