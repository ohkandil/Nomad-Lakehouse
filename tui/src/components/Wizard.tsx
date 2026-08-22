import { Box, Text, useInput } from 'ink';

import TextInput from 'ink-text-input';

import React, { useEffect, useRef, useState } from 'react';

import { loadEnvFile, mergeEnv, serializeEnv, writeEnvFile } from '../lib/env.js';

export interface WizardField {
  label: string;
  key: string;
  secure: boolean;
  placeholder?: string;
}

export const WIZARD_FIELDS: WizardField[] = [
  { label: 'MinIO root user', key: 'MINIO_ROOT_USER', secure: false },
  { label: 'MinIO root password', key: 'MINIO_ROOT_PASSWORD', secure: true },
  { label: 'MinIO API port', key: 'MINIO_API_PORT', secure: false, placeholder: '9000' },
  { label: 'MinIO console port', key: 'MINIO_CONSOLE_PORT', secure: false, placeholder: '9001' },
  { label: 'Warehouse bucket', key: 'WAREHOUSE_BUCKET', secure: false, placeholder: 'warehouse' },
  { label: 'Postgres DB', key: 'POSTGRES_DB', secure: false, placeholder: 'iceberg' },
  { label: 'Postgres user', key: 'POSTGRES_USER', secure: false, placeholder: 'iceberg' },
  { label: 'Postgres password', key: 'POSTGRES_PASSWORD', secure: true },
  { label: 'Postgres port', key: 'POSTGRES_PORT', secure: false, placeholder: '5432' },
  { label: 'AWS region', key: 'AWS_REGION', secure: false, placeholder: 'us-east-1' },
  { label: 'Dashboard domain', key: 'DASHBOARD_DOMAIN', secure: false, placeholder: 'dashboard.home.arpa' },
  { label: 'Dashboard auth user', key: 'DASHBOARD_AUTH_USER', secure: false, placeholder: 'admin' },
  { label: 'Dashboard auth password', key: 'DASHBOARD_AUTH_PASSWORD', secure: true },
  { label: 'Dashboard upstream', key: 'DASHBOARD_UPSTREAM', secure: false, placeholder: '127.0.0.1:8088' },
  { label: 'Dashboard allowed CIDRs', key: 'DASHBOARD_ALLOWED_CIDRS', secure: false },
];

type Step = 'welcome' | 'fields' | 'options' | 'summary';

interface WizardProps {
  /** Called when the wizard wants the app to switch tabs (Tab/Shift+Tab still work globally). */
  onEditingChange?: (editing: boolean) => void;
}

export const Wizard = ({ onEditingChange }: WizardProps) => {
  const [step, setStep] = useState<Step>('welcome');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [formData, setFormData] = useState<Record<string, string>>(() => ({}));
  const [draftValue, setDraftValue] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const inputFocusedRef = useRef(false);

  const field = WIZARD_FIELDS[currentIndex];
  const editing = step === 'fields';

  // Seed committed values from the existing .env once, then keep the draft in
  // sync with the currently selected field.
  useEffect(() => {
    setFormData(loadEnvFile());
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once on mount
  }, []);

  useEffect(() => {
    setDraftValue(formData[field.key] ?? '');
    // eslint-disable-next-line react-hooks/exhaustive-deps -- keyed on field index only
  }, [currentIndex]);

  useEffect(() => {
    onEditingChange?.(editing);
    inputFocusedRef.current = editing;
  }, [editing, onEditingChange]);

  useInput(
    (input, key) => {
      if (key.escape && editing) {
        if (currentIndex === 0) {
          setStep('welcome');
        } else {
          setCurrentIndex((prev) => prev - 1);
        }
        return;
      }
      if (key.return && !editing) {
        if (step === 'welcome') setStep('fields');
        if (step === 'options') handleSave();
      }
    },
    { isActive: !editing },
  );

  const commitDraft = () => {
    setFormData((prev) => ({ ...prev, [field.key]: draftValue }));
  };

  const handleNext = () => {
    commitDraft();
    if (currentIndex < WIZARD_FIELDS.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setStep('options');
    }
  };

  const handleSave = () => {
    try {
      const updates: Record<string, string> = { ...formData, [field.key]: draftValue };
      const existing = loadEnvFile();
      const merged = mergeEnv(existing, updates);
      writeEnvFile(serializeEnv(merged));
      setSaveError(null);
      setStep('summary');
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : String(err));
    }
  };

  if (step === 'welcome') {
    return (
      <Box flexDirection="column" gap={1}>
        <Text>Welcome to the Nomad Lakehouse setup.</Text>
        <Text>This wizard configures your repository-root .env file.</Text>
        <Text dimColor>Existing values in .env are pre-filled and preserved.</Text>
        <Text color="yellow">[Enter] start - [q] quit</Text>
      </Box>
    );
  }

  if (step === 'fields') {
    const value = formData[field.key] ?? '';
    return (
      <Box flexDirection="column" gap={1}>
        <Text color="green">
          Field {currentIndex + 1} of {WIZARD_FIELDS.length}
        </Text>
        <Box>
          <Text>{field.label}: </Text>
          <TextInput
            value={draftValue}
            onChange={setDraftValue}
            onSubmit={handleNext}
            mask={field.secure ? '*' : undefined}
            placeholder={field.placeholder ?? (field.secure ? 'Enter a secure value' : 'Enter value')}
          />
        </Box>
        {!field.secure && value !== '' ? (
          <Text dimColor>current .env value: {value}</Text>
        ) : null}
        <Text dimColor>[Enter] next - [Esc] previous</Text>
      </Box>
    );
  }

  if (step === 'options') {
    return (
      <Box flexDirection="column" gap={1}>
        <Text color="green">All fields collected.</Text>
        <Text>Write merged configuration to .env?</Text>
        <Text color="yellow">[Enter] save and finish</Text>
        {saveError !== null ? <Text color="red">Save failed: {saveError}</Text> : null}
      </Box>
    );
  }

  return (
    <Box flexDirection="column" gap={1}>
      <Text color="green">Configuration saved successfully!</Text>
      <Text>Your .env file at the repository root has been updated.</Text>
      <Text color="yellow">Press [d] to inspect Service Health.</Text>
    </Box>
  );
};
