import React from 'react';
import './App.css';
import StramViewer from "../StramViewer"

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <div>
         Pi Stream
        </div>
        <StramViewer />
      </header>
    </div>
  );
}

export default App;
