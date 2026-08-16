import React, { useState } from 'react';
import { Box, Text, Input, createCliRenderer } from '@opentui/core';
import { createRoot, useKeyboard } from '@opentui/react';

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

  useKeyboard((event: any) => {
    if (event.key === 'q') {
      process.exit(0);
    }
    if (step === 'welcome' && event.key === 'Enter') {
      setStep('fields');
    }
    if (step === 'fields' && event.key === 'Escape') {
      setStep('welcome');
    }
  });

  const handleNext = (val: string) => {
    const field = FIELD_SPECS[currentIndex];
    const newData = { ...formData, [field.key]: val };
    setFormData(newData);
    
    if (currentIndex < FIELD_SPECS.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      setStep('summary');
    }
  };

  if (step === 'welcome') {
    return (
      <Box flexDirection="column" padding={2} borderStyle="double" borderColor="cyan">
        <Text bold color="cyan" content="Nomad Lakehouse Setup Wizard" />
        <Box marginTop={1}>
          <Text content="Welcome to the Nomad Lakehouse setup. This wizard will guide you through the initial configuration." />
        </Box>
        <Box marginTop={2}>
          <Text italic color="gray" content="Press [Enter] to continue or [q] to quit" />
        </Box>
      </Box>
    );
  }

  if (step === 'fields') {
    const field = FIELD_SPECS[currentIndex];
    return (
      <Box flexDirection="column" padding={2} borderStyle="single" borderColor="blue">
        <Text bold content={`Configuring: ${field.label}`} />
        <Box marginTop={1}>
          <Input 
            value={formData[field.key] || ''} 
            onSubmit={handleNext}
            placeholder={`Enter ${field.label}...`}
          />
        </Box>
        <Box marginTop={2} flexDirection="row">
          <Text color="gray" content={`[${currentIndex + 1} / ${FIELD_SPECS.length}] `} />
          <Text italic color="gray" content="Press [Esc] for previous, [q] to quit" />
        </Box>
      </Box>
    );
  }

  return (
    <Box flex={1} padding={2}>
      <Text content="Setup Complete! Review your .env file." />
    </Box>
  );
};
