import { Box, Text, useApp, useInput } from 'ink';

import React, { useCallback, useMemo, useState } from 'react';

import { Dashboard } from './components/Dashboard.js';
import { Wizard } from './components/Wizard.js';
import { loadEnvFile } from './lib/env.js';

type Tab = 'wizard' | 'dashboard';

const TAB_LABELS: Record<Tab, string> = {
  wizard: '[w] Setup Wizard',
  dashboard: '[d] Service Health',
};

export const App = () => {
  const { exit } = useApp();
  const [tab, setTab] = useState<Tab>('wizard');
  const [wizardEditing, setWizardEditing] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  // Re-read .env whenever the active tab changes (covers wizard saves) or on demand.
  const env = useMemo(() => loadEnvFile(), [tab, reloadKey]);

  const handleEditingChange = useCallback((editing: boolean) => {
    setWizardEditing(editing);
  }, []);

  useInput((input, key) => {
    if (key.tab && key.shift) {
      setTab((prev) => (prev === 'wizard' ? 'dashboard' : 'wizard'));
      return;
    }
    if (key.tab) {
      setTab('dashboard');
      return;
    }
    if (wizardEditing) return;
    if (input === 'w') setTab('wizard');
    if (input === 'd') setTab('dashboard');
    if (input === 'q') exit();
  });

  return (
    <Box flexDirection="column" borderStyle="round" borderColor="cyan" paddingX={1} gap={1}>
      <Box>
        <Text bold color="cyan">
          Nomad Lakehouse Control
        </Text>
        {(Object.keys(TAB_LABELS) as Tab[]).map((name) => (
          <Text key={name} color={tab === name ? 'cyan' : undefined} dimColor={tab !== name}>
            {' '}
            {TAB_LABELS[name]}{' '}
          </Text>
        ))}
      </Box>

      {tab === 'wizard' ? (
        <Wizard onEditingChange={handleEditingChange} />
      ) : (
        <Dashboard env={env} />
      )}

      <Text dimColor>[Tab]/[Shift+Tab] switch view - [q] quit</Text>
    </Box>
  );
};
