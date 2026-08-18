import React, { useReducer, useEffect, useRef, useCallback } from 'react';
import { useKeyboard, useRenderer } from '@opentui/react';
import type { InputRenderable } from '@opentui/core';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { TextAttributes } from '@opentui/core';
import { FIELD_SPECS, wizardReducer, createInitialState, validateField, buildEnvContent } from './wizard-logic';

const STATE_FILE = join(homedir(), '.nomad-lakehouse-wizard-state.json');
const ENV_FILE = join(process.cwd(), '.env');

export function App() {
  const [state, dispatch] = useReducer(wizardReducer, createInitialState());
  const inputRef = useRef<InputRenderable | null>(null);
  const renderer = useRenderer();

  // Persist state on fields/options steps
  useEffect(() => {
    if (state.step === 'fields' || state.step === 'options') {
      try {
        writeFileSync(STATE_FILE, JSON.stringify({
          step: state.step,
          currentIndex: state.currentIndex,
          formData: state.formData,
        }), 'utf-8');
      } catch {
        // ignore persistence errors
      }
    }
  }, [state.step, state.currentIndex, state.formData]);

  // Focus input when entering fields step
  useEffect(() => {
    if (state.step === 'fields' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [state.step, state.currentIndex]);

  const currentField = FIELD_SPECS[state.currentIndex];
  const isSecure = currentField?.secure ?? false;
  const fieldValue = state.formData[currentField?.key ?? ''] ?? '';
  const displayValue = isSecure ? '*'.repeat(fieldValue.length) : fieldValue;
  const fieldError = state.errors[currentField?.key ?? ''];
  const isLastField = state.currentIndex === FIELD_SPECS.length - 1;

  const handleEnter = useCallback(() => {
    if (state.step === 'welcome') {
      dispatch({ type: 'SET_STEP', step: 'fields' });
    } else if (state.step === 'fields') {
      if (inputRef.current) {
        const actualValue = inputRef.current.value;
        const fieldKey = currentField.key;
        dispatch({ type: 'SET_FIELD_VALUE', key: fieldKey, value: actualValue });
      }
      dispatch({ type: 'NEXT_FIELD' });
    } else if (state.step === 'options') {
      const envContent = buildEnvContent(state.formData);
      try {
        writeFileSync(ENV_FILE, envContent, 'utf-8');
        dispatch({ type: 'SET_STEP', step: 'summary' });
      } catch (error) {
        console.error('Failed to write .env:', error);
      }
    } else if (state.step === 'summary' || state.step === 'quitConfirm') {
      renderer.destroy();
    }
  }, [state.step, currentField, renderer]);

  const handleBackspace = useCallback(() => {
    if (state.step === 'fields') {
      if (inputRef.current) {
        const actualValue = inputRef.current.value;
        const fieldKey = currentField.key;
        dispatch({ type: 'SET_FIELD_VALUE', key: fieldKey, value: actualValue });
      }
      dispatch({ type: 'PREV_FIELD' });
    } else if (state.step === 'options') {
      dispatch({ type: 'SET_STEP', step: 'fields' });
    } else if (state.step === 'quitConfirm') {
      dispatch({ type: 'SET_STEP', step: 'fields' });
    }
  }, [state.step, currentField]);

  const handleQuit = useCallback(() => {
    if (state.step === 'quitConfirm') {
      renderer.destroy();
    } else {
      dispatch({ type: 'SET_STEP', step: 'quitConfirm' });
    }
  }, [state.step, renderer]);

  const handleKeyboard = useCallback((event: any) => {
    if (event.name === 'q') {
      handleQuit();
    } else if (event.name === 'enter') {
      handleEnter();
    } else if (event.name === 'backspace') {
      handleBackspace();
    } else if (event.name === 'escape') {
      if (state.step === 'fields') {
        dispatch({ type: 'SET_STEP', step: 'welcome' });
      } else if (state.step === 'options') {
        dispatch({ type: 'SET_STEP', step: 'fields' });
      } else if (state.step === 'quitConfirm') {
        dispatch({ type: 'SET_STEP', step: 'fields' });
      }
    }
  }, [state.step, handleQuit, handleEnter, handleBackspace]);

  useKeyboard(handleKeyboard);

  if (state.step === 'welcome') {
    return (
      <box gap={1} border borderStyle="single" borderColor="blue" padding={2}>
        <text fg="cyan" attributes={TextAttributes.BOLD}>Nomad Lakehouse Setup Wizard</text>
        <text>Welcome to the Nomad Lakehouse setup!</text>
        <text>This wizard will help you configure your environment variables.</text>
        <text fg="yellow">Press <strong>[Enter]</strong> to start, or <strong>[q]</strong> to quit.</text>
        <text fg="gray">Existing .env values will be pre-filled if found.</text>
      </box>
    );
  }

  if (state.step === 'fields') {
    return (
      <box gap={1} border borderStyle="single" borderColor="blue" padding={2}>
        <text fg="cyan" attributes={TextAttributes.BOLD}>Nomad Lakehouse Setup Wizard</text>
        <text fg="gray">Step {state.currentIndex + 1} of {FIELD_SPECS.length}</text>
        <box gap={1}>
          <text>
            <strong>{currentField.label}:</strong>
          </text>
          <input ref={inputRef} value={displayValue} placeholder={isSecure ? 'Enter password (hidden)' : ''} />
          {fieldError ? (
            <text fg="red">
              <span>✗ </span>
              <em>{fieldError}</em>
            </text>
          ) : null}
          <box flexDirection="row" gap={2} marginTop={1}>
            <text fg="green">
              <strong>Backspace</strong> Back
            </text>
            <text fg="green">
              <strong>{isLastField ? 'Enter' : 'Enter'}</strong> {isLastField ? 'Continue' : 'Next'}
            </text>
            <text fg="yellow">[q] Quit</text>
          </box>
        </box>
      </box>
    );
  }

  if (state.step === 'options') {
    return (
      <box gap={1} border borderStyle="single" borderColor="blue" padding={2}>
        <text fg="cyan" attributes={TextAttributes.BOLD}>Nomad Lakehouse Setup Wizard</text>
        <text fg="green">Configuration Complete!</text>
        <text>Ready to write .env and start the stack?</text>
        <text fg="yellow">Press <strong>[Enter]</strong> to save, <strong>[Backspace]</strong> to go back, or <strong>[q]</strong> to quit.</text>
      </box>
    );
  }

  if (state.step === 'summary') {
    return (
      <box gap={1} border borderStyle="single" borderColor="green" padding={2}>
        <text fg="cyan" attributes={TextAttributes.BOLD}>Nomad Lakehouse Setup Wizard</text>
        <text fg="green">Configuration saved successfully!</text>
        <text>Your .env file has been written to <strong>{ENV_FILE}</strong></text>
        <text fg="yellow">Press <strong>[Enter]</strong> or <strong>[q]</strong> to exit.</text>
      </box>
    );
  }

  if (state.step === 'quitConfirm') {
    return (
      <box gap={1} border borderStyle="single" borderColor="red" padding={2}>
        <text fg="red" attributes={TextAttributes.BOLD}>
          Confirm Quit
        </text>
        <text>Are you sure you want to quit without saving?</text>
        <text fg="yellow">Press <strong>[q]</strong> again to confirm, or <strong>[Backspace]/[Escape]</strong> to cancel.</text>
      </box>
    );
  }

  return <text>Unknown step</text>;
}

export default App;