async function fetchAndDisplayRecommendations(accessToken = null) {
  const container = document.getElementById('recommendations');
  const button = document.getElementById('reveal') || document.getElementById('login-btn');
  if (button) button.remove(); // Remove button after starting

  let tracksData;

  if (accessToken) {
    // If we have access token from URL (old flow)
    const topTracksRes = await fetch(`/top-tracks?access_token=${accessToken}`);
    const topTracks = await topTracksRes.json();
    const seedTracks = topTracks.slice(0, 5).map(t => t.id).join(',');
    
    const recRes = await fetch(`/recommendations?access_token=${accessToken}&seed_tracks=${seedTracks}`);
    tracksData = await recRes.json();
    // Map the API data to look like { id, name, artist, albumImage }
    tracksData = tracksData.map(track => ({
      id: track.id,
      name: track.name,
      artist: track.artists[0].name,
      albumImage: track.album.images[0]?.url || ''
    }));

  } else {
    // If using your new server-side auth flow
    const res = await fetch('/run-algorithm');
    const data = await res.json();
    tracksData = data.recommendedTracks;
  }

  tracksData.forEach(track => {
    const trackDiv = document.createElement('div');
    trackDiv.className = 'track';

    trackDiv.innerHTML = `
      <img src="${track.albumImage}" alt="Album Cover">
      <div class="track-name">${track.name}</div>
      <div class="artist-name">${track.artist}</div>
    `;

    container.appendChild(trackDiv);
  });
}

// Button clicks
document.getElementById('login-btn')?.addEventListener('click', () => {
  window.location.href = 'http://localhost:3000/login';
});

document.getElementById('reveal')?.addEventListener('click', async () => {
  await fetchAndDisplayRecommendations();
});

// Auto-trigger if coming back from Spotify login
if (window.location.hash.includes('access_token')) {
  const access_token = new URLSearchParams(window.location.hash.substring(1)).get('access_token');
  fetchAndDisplayRecommendations(access_token);
}