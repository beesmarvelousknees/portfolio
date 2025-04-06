const express = require('express');
const fs = require('fs');
const app = express();
const PORT = 3007;

app.use(express.json());

const filePath = './portfolio.json';

// Get current portfolio data
app.get('/portfolio', (req, res) => {
  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      return res.status(500).send('Error reading data');
    }
    res.send(JSON.parse(data));
  });
});

// Update portfolio data
app.post('/portfolio', (req, res) => {
  const newData = req.body;
  fs.writeFile(filePath, JSON.stringify(newData, null, 2), 'utf8', (err) => {
    if (err) {
      return res.status(500).send('Error writing data');
    }
    res.send('Data updated successfully');
  });
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
