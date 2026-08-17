import React, { useEffect, useRef, useState } from 'react';
import { useKeyboard } from '@opentui/react';
import { TextAttributes } from '@opentui/core';
import type { InputRenderable } from '@opentui/core';

type Step = 'welcome' | 'fields' | 'options' | 'summary';

const FIELD_SPECS = [
  { label: 'MinIO root user', key: 'MINIO_ROOT_USER', secure: false },
  { label: 'MinIO root password', key: 'MINIO_ROOT_PASSWORD', secure: true },
  { label: 'MinIO API port', key: 'MINIO_API_PORT', secure: false },
  { label: 'MinIO console port', key: 'MINIO_CONSOLE_PORT', secure: false },
  { label: 'Warehouse bucket', key: 'WAREHOUSE_BUCKET', secure: false },
  { label: 'Postgres DB', key: 'POSTGRES_DB', secure: false },
  { label: 'Postgres user', key: 'POSTGRES_USER', secure: false },
  { label: 'Postgres password', key: 'POSTGRES_PASSWORD', secure: true },
  { label: 'Postgres port', key: 'POSTGRES_PORT', secure: false },
  { label: 'AWS region', key: 'AWS_REGION', secure: false },
  { label: 'Dashboard domain', key: 'DASHBOARD_DOMAIN', secure: false },
  { label: 'Dashboard auth user', key: 'DASHBOARD_AUTH_USER', secure: false },
  { label: 'Dashboard auth password', key: 'DASHBOARD_AUTH_PASSWORD', secure: true },
  { label: 'Dashboard upstream', key: 'DASHBOARD_UPSTREAM', secure: false },
  { label: 'Dashboard allowed CIDRs', key: 'DASHBOARD_ALLOWED_CIDRS', secure: false },
] as const;

export const App = () => {
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [step, setStep] = useState<Step>('welcome');
  const inputRef = useRef<InputRenderable | null>(null);

  const currentField = FIELD_SPECS[currentIndex];

  const saveCurrentFieldValue = () => {
    if (!inputRef.current) return;
    const actualValue = inputRef.current.value ?? '';
    setFormData((prev) => ({
      ...prev,
      [currentField.key]: actualValue,
    }));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => {
      if (prev < FIELD_SPECS.length - 1) {
        return prev + 1;
      }
      setStep('options');
      return prev;
    });
  };

  const handlePrev = () => {
    setCurrentIndex((prev) => {
      if (prev > 0) {
        return prev - 1;
      }
      setStep('welcome');
      return prev;
    });
  };

  const handleFieldSubmit = () => {
    saveCurrentFieldValue();
    handleNext();
  };

  const handleSave = () => {
    saveCurrentFieldValue();

    const envContent = Object.entries(formData)
      .map(([k, v]) => `${k}=${v}`)
      .join('\n');

    console.log('\nSaving .env content:\n');
    console.log(envContent);
    console.log('\nConfiguration complete.\n');

    setStep('summary');
  };

  useKeyboard((event) => {
    console.log('KEY EVENT:', JSON.stringify(event));

    const keyName = event?.name?.toLowerCase?.() ?? '';

    if (keyName === 'q') {
      process.exit(0);
    }

    if (keyName === 'enter' || keyName === 'return') {
      if (step === 'welcome') {
        setStep('fields');
        return;
      }

      if (step === 'fields') {
        handleFieldSubmit();
        return;
      }

      if (step === 'options') {
        handleSave();
        return;
      }

      return;
    }

    if (keyName === 'backspace' && step === 'fields') {
      saveCurrentFieldValue();
      handlePrev();
    }
  });

  useEffect(() => {
    if (step === 'fields' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [step, currentIndex]);

  const currentValue = formData[currentField.key] || '';
  const displayValue = currentField.secure ? '*'.repeat(currentValue.length) : currentValue;

  return (
    <box gap={1} border borderStyle="single" borderColor="blue">
      <text fg="cyan" attributes={TextAttributes.BOLD}>
        Nomad Lakehouse Setup Wizard
      </text>

      {step === 'welcome' && (
        <box gap={1}>
          <text>Welcome to the Nomad Lakehouse setup!</text>
          <text>This wizard will help you configure your environment variables.</text>
          <text fg="yellow">Press [Enter] to start, or [q] to quit.</text>
        </box>
      )}

      {step === 'fields' && (
        <box gap={1}>
          <text fg="green">
            Field {currentIndex + 1} of {FIELD_SPECS.length}
          </text>

          <text>{currentField.label}</text>

          <box gap={1}>
            <text>{currentField.label}: </text>
            <input
              ref={inputRef}
              value={displayValue}
              placeholder={currentField.secure ? 'Enter password' : 'Enter value'}
            />
          </box>

          <text fg="gray">[Enter] Next | [Backspace] Prev | [q] Quit</text>
        </box>
      )}

      {step === 'options' && (
        <box gap={1}>
          <text fg="green">Configuration Complete!</text>
          <text>Ready to write .env and start the stack?</text>
          <text fg="yellow">Press [Enter] to save and finish, or [q] to quit.</text>
        </box>
      )}

      {step === 'summary' && (
        <box gap={1}>
          <text fg="green">Configuration saved successfully!</text>
          <text>Your values were collected by the wizard.</text>
          <text fg="yellow">Press [q] to quit.</text>
        </box>
      )}
    </box>
  );
};
