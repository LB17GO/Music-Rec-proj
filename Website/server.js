const express = require('express');
const app = express();
const port = 3000;

// Serve static files (HTML, CSS, images)
app.use(express.static('public'));




app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
  });