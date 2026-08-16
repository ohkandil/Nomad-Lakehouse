import React, { useState, useEffect } from 'react';
import { Box, Text, Input, Signal } from '@opentui/core';
import { component, render, useKeyboard } from '@opentui/react';
import { Keymap } from '@opentui/keymap';

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

  useKeyboard((event) => {
    if (event.key === 'q') {
      process.exit(0);
    }
    if (event.key === 'Enter') {
      if (step === 'welcome') setStep('fields');
      else if (step === 'fields') handleNext();
    }
    if (event.key === 'Backspace' && step === 'fields') {
      handlePrev();
    }
  });

  return (
    <Box flexDirection="column" padding={1} borderStyle="single" borderColor="blue">
      <Text bold color="cyan">Nomad Lakehouse Setup Wizard</Text>
      
      {step === 'welcome' && (
        <Box flexDirection="column" marginTop={1}>
          <Text>Welcome to the Nomad Lakehouse setup!</Text>
          <Text>This wizard will help you configure your environment variables.</Text>
          <Text marginTop={1} color="yellow">Press [Enter] to start, or [q] to quit.</Text>
        </Box>
      )}

      {step === 'fields' && (
        <Box flexDirection="column" marginTop={1}>
          <Text color="green">Step: {FIELD_SPECS[currentIndex].label}</Text>
          <Box marginTop={1}>
            <Text>{FIELD_SPECS[currentIndex].label}: </Text>
            <Input 
              value={formData[FIELD_SPECS[currentIndex].key] || ''} 
              onChange={(val) => setFormData({...formData, [FIELD_SPECS[currentIndex].key]: val})}
              secure={FIELD_SPECS[currentIndex].secure}
            />
          </Box>
          <Text marginTop={1} color="gray">
            [Enter] Next | [Backspace] Prev | [q] Quit
          </Text>
        </Box>
      )}

      {step === 'options' && (
        <Box flexDirection="column" marginTop={1}>
          <Text color="green">Configuration Complete!</Text>
          <Text marginTop={1}>Ready to write .env and start the stack?</Text>
          <Text marginTop={1} color="yellow">Press [Enter] to save and finish.</Text>
        </Box>
      )}
    </Box>
  );
};

export default App;
