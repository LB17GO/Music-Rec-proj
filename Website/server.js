const express = require('express');
const app = express();
const port = 3000;
const redirect_uri = 'http://localhost:3000/callback';
const axios = require('axios');
const cors = require('cors');
const querystring = require('querystring');

const SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize';
const SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token';


// Serve static files (HTML, CSS, images)

app.use(express.static('public'));
app.use(cors());

app.get('/login', (req, res) => {
  console.log("Login route hit");
  const scope = 'user-top-read user-read-private user-read-email';
  res.redirect(`${SPOTIFY_AUTH_URL}?${querystring.stringify({
    response_type: 'code',
    client_id: process.env.CLIENT_ID,
    scope: scope,
    redirect_uri: process.env.REDIRECT_URI,
  })}`);
});

app.get('/callback', async (req, res) => {
  const { code } = req.query;
  
  try {
    // Exchange code for access token
    const { data } = await axios.post(SPOTIFY_TOKEN_URL, querystring.stringify({
      grant_type: 'authorization_code',
      code,
      redirect_uri: process.env.REDIRECT_URI,
      client_id: process.env.CLIENT_ID,
      client_secret: process.env.CLIENT_SECRET,
    }), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    const { access_token, refresh_token } = data;
    
    // Now you can use the access_token to make API calls
    res.redirect(`/?access_token=${access_token}`);
  } catch (error) {
    res.send('Error getting access token');
  }
});

const fs = require('fs');
const path = require('path');

app.get('/save-liked-songs', async (req, res) => {
  try {
    const { access_token } = req.query;
    const allTracks = [];
    let nextUrl = 'https://api.spotify.com/v1/me/tracks?limit=50'; // Max 50 per request

    // Keep fetching until no more pages
    while (nextUrl) {
      const response = await axios.get(nextUrl, {
        headers: {
          'Authorization': `Bearer ${access_token}`
        }
      });

      // Extract relevant track data
      const tracks = response.data.items.map(item => ({
        id: item.track.id,
        name: item.track.name,
        artists: item.track.artists.map(artist => ({
          id: artist.id,
          name: artist.name
        })),
        album: {
          id: item.track.album.id,
          name: item.track.album.name,
          release_date: item.track.album.release_date
        },
        duration_ms: item.track.duration_ms,
        popularity: item.track.popularity,
        added_at: item.added_at
      }));

      allTracks.push(...tracks);
      nextUrl = response.data.next; // Spotify provides pagination URL
    }

    // Create data directory if it doesn't exist
    const dir = path.join(__dirname, 'data');
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir);
    }

    // Save to file with timestamp
    const filename = path.join(dir, `liked_songs_${Date.now()}.json`);
    fs.writeFileSync(filename, JSON.stringify(allTracks, null, 2));

    res.json({
      success: true,
      message: `Saved ${allTracks.length} liked songs to ${filename}`,
      count: allTracks.length
    });

  } catch (error) {
    console.error('Error saving liked songs:', error.message);
    res.status(500).json({ 
      success: false,
      error: error.message 
    });
  }
});



app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
  });