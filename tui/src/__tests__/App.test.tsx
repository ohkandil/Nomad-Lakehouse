import { test, expect } from "bun:test";
import { createTestRenderer } from "@opentui/core/testing";
import { App } from "../App";
import { createRoot } from "@opentui/react";
import React from "react";

async function setupApp() {
  const testSetup = await createTestRenderer({
    width: 80,
    height: 24,
  });
  const root = createRoot(testSetup.renderer);
  root.render(<App />);
  // Use flush to allow React to reconcile
  await testSetup.flush();
  return testSetup;
}

test("renders welcome screen", async () => {
  const testSetup = await setupApp();
  const frame = testSetup.captureCharFrame();
  expect(frame).toContain("Nomad Lakehouse Setup Wizard");
});
