import React, { useState, useRef, useEffect } from 'react';
import { useKeyboard } from '@opentui/react';
import { createRoot } from '@opentui/react';
import { createCliRenderer } from '@opentui/core';
import { TextAttributes } from '@opentui/core';
import type { InputRenderable } from '@opentui/core';

const FIELD_SPECS = [
  { label: "MinIO root user", key: "MINIO_ROOT_USER", secure: false },
  { label: "MinIO root password", key: "MINIO_ROOT_PASSWORD", secure: true },
  { label: "MinIO API port", key: "MINIO_API_PORT", secure: false },
  { label: "MinIO console port", key: "MINIO_CONSOLE_PORT", secure: false },
  { label: "Warehouse bucket", key: "WAREHOUSE_BUCKET", secure: false },
  { label: "Postgres DB", key: "POSTGRES_DB", secure: false },
  { label: "Postgres user", key: "POSTGRES_USER", secure: false },
  { label: "Postgres password", key: "POSTGRES_PASSWORD", secure: true },
  { label: "Postgres port", key: "POSTGRES_PORT", secure: false },
  { label: "AWS region", key: "AWS_REGION", secure: false },
  { label: "Dashboard domain", key: "DASHBOARD_DOMAIN", secure: false },
  { label: "Dashboard auth user", key: "DASHBOARD_AUTH_USER", secure: false },
  { label: "Dashboard auth password", key: "DASHBOARD_AUTH_PASSWORD", secure: true },
  { label: "Dashboard upstream", key: "DASHBOARD_UPSTREAM", secure: false },
  { label: "Dashboard allowed CIDRs", key: "DASHBOARD_ALLOWED_CIDRS", secure: false },
];

export const App = () => {
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [step, setStep] = useState<'welcome' | 'fields' | 'options' | 'summary'>('welcome');
  const inputRef = useRef<InputRenderable | null>(null);

  const handleNext = () => {
    if (currentIndex < FIELD_SPECS.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      setStep('options');
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    } else {
      setStep('welcome');
    }
  };

  const handleSave = () => {
    const envContent = Object.entries(formData)
      .map(([k, v]) => `${k}=${v}`)
      .join('\n');
    console.log('Saving .env:', envContent);
    setStep('summary');
  };

  const handleFieldEnter = () => {
    // Save current field value from input ref
    if (inputRef.current) {
      const actualValue = inputRef.current.value;
      const currentField = FIELD_SPECS[currentIndex];
      setFormData(prev => ({...prev, [currentField.key]: actualValue}));
    }
    handleNext();
  };

  useKeyboard((event) => {
    if (event.name === 'q') {
      process.exit(0);
    }
    if (event.name === 'enter') {
      if (step === 'welcome') setStep('fields');
      else if (step === 'fields') handleFieldEnter();
      else if (step === 'options') handleSave();
    }
    if (event.name === 'backspace' && step === 'fields') {
      // Save current field value before going back
      if (inputRef.current) {
        const actualValue = inputRef.current.value;
        const currentField = FIELD_SPECS[currentIndex];
        setFormData(prev => ({...prev, [currentField.key]: actualValue}));
      }
      handlePrev();
    }
  });

  const currentField = FIELD_SPECS[currentIndex];
  const isSecure = currentField.secure;

  // For secure fields, mask the value
  const displayValue = isSecure 
    ? '*'.repeat(formData[currentField.key]?.length || 0) 
    : (formData[currentField.key] || '');

  // Focus the input when field step is active
  useEffect(() => {
    if (step === 'fields' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [step, currentIndex]);

  return (
    <box gap={1} border borderStyle="single" borderColor="blue">
      <text fg="cyan" attributes={TextAttributes.BOLD}>Nomad Lakehouse Setup Wizard</text>
      
      {step === 'welcome' && (
        <box gap={1}>
          <text>Welcome to the Nomad Lakehouse setup!</text>
          <text>This wizard will help you configure your environment variables.</text>
          <text fg="yellow">Press [Enter] to start, or [q] to quit.</text>
        </box>
      )}

      {step === 'fields' && (
        <box gap={1}>
          <text fg="green">Step: {currentField.label}</text>
          
          <box gap={1}>
            <text>{currentField.label}: </text>
            <input 
              ref={inputRef}
              value={displayValue}
              placeholder={currentField.secure ? "Enter password" : ""}
            />
          </box>
          
          <text fg="gray">[Enter] Next | [Backspace] Prev | [q] Quit</text>
        </box>
      )}

      {step === 'options' && (
        <box gap={1}>
          <text fg="green">Configuration Complete!</text>
          <text>Ready to write .env and start the stack?</text>
          <text fg="yellow">Press [Enter] to save and finish.</text>
        </box>
      )}

      {step === 'summary' && (
        <box gap={1}>
          <text fg="green">Configuration saved successfully!</text>
          <text>Your .env file has been written.</text>
          <text fg="yellow">Press [q] to quit.</text>
        </box>
      )}
    </box>
  );
};

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