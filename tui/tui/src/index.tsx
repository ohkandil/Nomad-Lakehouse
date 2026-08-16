import { createCliRenderer } from '@opentui/core';
import { createRoot } from '@opentui/react';
import React from 'react';
import { App } from './App';

async function start() {
  try {
    const renderer = await createCliRenderer();
    const root = createRoot(renderer);
    root.render(<App />);
  } catch (error) {
    console.error("Failed to start OpenTUI wizard:", error);
    process.exit(1);
  }
}

start();