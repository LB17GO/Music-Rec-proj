const express = require('express');
const app = express();
const port = 3000;
const redirect_uri = 'http://localhost:3000/callback';
const axios = require('axios');
const cors = require('cors');
const querystring = require('querystring');
require('dotenv').config(); // At the top of your server file (e.g., app.js)

const cookieParser = require('cookie-parser');

app.use(cookieParser()); // For reading cookies

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
    client_id: process.env.SPOTIFY_CLIENT_ID,
    scope: scope,
    redirect_uri: process.env.SPOTIFY_REDIRECT_URI,
  })}`);
});

app.get('/callback', async (req, res) => {
  const { code, error } = req.query;

  console.log('Exchange attempt with:', {
    code: code,
    redirect_uri: process.env.SPOTIFY_REDIRECT_URI,
    client_id: process.env.SPOTIFY_CLIENT_ID?.substring(0, 5) + '...' // Log partial ID
  });
  

  if (error) {
    console.error('Spotify auth error:', error);
    return res.redirect('/?error=' + encodeURIComponent(error));
  }

  try {
    const { data } = await axios.post(
      'https://accounts.spotify.com/api/token',
      new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: process.env.SPOTIFY_REDIRECT_URI, // Fixed this line
        client_id: process.env.SPOTIFY_CLIENT_ID,
        client_secret: process.env.SPOTIFY_CLIENT_SECRET,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );

    // Better security: Use HTTP-only cookies or sessions
    res.cookie('spotify_access_token', data.access_token, { httpOnly: true });
    res.cookie('spotify_refresh_token', data.refresh_token, { httpOnly: true });
    
    res.redirect('/dashboard'); // Redirect to a protected route

  } catch (error) {
    console.error('Token exchange error:', error.response?.data || error.message);
    res.redirect('/?error=auth_failed');
  }
});

app.get('/dashboard', async (req, res) => {
  const accessToken = req.cookies.spotify_access_token;

  if (!accessToken) {
    return res.redirect('/login');
  }

  try {
    const allTracks = [];
    let nextUrl = 'https://api.spotify.com/v1/me/tracks?limit=50';

    while (nextUrl) {
      const response = await axios.get(nextUrl, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      const tracks = response.data.items.map(item => ({
        id: item.track.id,
        name: item.track.name,
        genre: item.track.artist.genre,
        artists: item.track.artists.map(artist => ({
          id: artist.id,
          name: artist.name
        })),
        album: {
          id: item.track.album.id,
          name: item.track.album.name,
        },
        audiofeatures: {
          duration_ms: item.track.duration_ms,
          popularity: item.track.popularity,
          danceability: item.track.danceability,
          energy: item.track.energy,
          loudness: item.track.loudness,
          speechiness: item.track.speechiness,
          liveness: item.track.liveness,
          valence: item.track.valence,
          tempo: item.track.tempo,
        },
      }));

      allTracks.push(...tracks);
      nextUrl = response.data.next;
    }

    const dir = path.join(__dirname, 'data');
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir);
    }

    const filename = path.join(dir, `liked_songs_${Date.now()}.json`);
    fs.writeFileSync(filename, JSON.stringify(allTracks, null, 2));

    console.log(`Saved ${allTracks.length} liked songs to ${filename}`);

    // Send dashboard page after saving
    res.sendFile(path.join(__dirname, 'public', 'dashboard.html'));

  } catch (error) {
    console.error('Error saving liked songs:', error.message);
    res.status(500).send('Failed to fetch liked songs');
  }
});

app.get('/display-recs', async (req, res) => {

});



app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
  });