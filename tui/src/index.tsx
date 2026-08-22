import React from 'react';

import { render } from 'ink';

import { App } from './App.js';

try {
  render(<App />);
} catch (error) {
  console.error('Failed to start Nomad Lakehouse TUI:', error);
  process.exit(1);
}
