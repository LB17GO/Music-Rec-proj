document.getElementById('login-btn').addEventListener('click', () => {
    window.location.href = 'http://localhost:3000/login';
  });

  // After redirect back from Spotify with access token
  if (window.location.hash.includes('access_token')) {
    const access_token = new URLSearchParams(window.location.hash.substring(1)).get('access_token');
    
    // Fetch user data and recommendations
    fetch(`/top-tracks?access_token=${access_token}`)
      .then(response => response.json())
      .then(tracks => {
        const seedTracks = tracks.slice(0, 5).map(t => t.id).join(',');
        return fetch(`/recommendations?access_token=${access_token}&seed_tracks=${seedTracks}`);
      })
      .then(response => response.json())
      .then(recommendations => {
        document.getElementById('recommendations').innerHTML = 
          recommendations.map(track => `<div>${track.name} by ${track.artists[0].name}</div>`).join('');
      });
    }