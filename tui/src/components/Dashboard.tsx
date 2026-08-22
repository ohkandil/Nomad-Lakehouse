import { Box, Text, useInput } from 'ink';

import React, { useCallback, useEffect, useState } from 'react';

import type { ServiceHealth, StatusLevel } from '../lib/health.js';
import { collectServiceHealth } from '../lib/health.js';

import type { EnvMap } from '../lib/env.js';

const POLL_INTERVAL_MS = 10_000;

const STATUS_COLOR: Record<StatusLevel, string> = {
  ok: 'green',
  warn: 'yellow',
  fail: 'red',
  unknown: 'gray',
};

const STATUS_SYMBOL: Record<StatusLevel, string> = {
  ok: '●',
  warn: '▲',
  fail: '✖',
  unknown: '○',
};

interface DashboardProps {
  env: EnvMap;
}

export const Dashboard = ({ env }: DashboardProps) => {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [overall, setOverall] = useState<StatusLevel>('unknown');
  const [collectedAt, setCollectedAt] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const result = await collectServiceHealth(env);
      setServices(result.services);
      setOverall(result.overall);
      setCollectedAt(result.collectedAt);
    } finally {
      setRefreshing(false);
    }
  }, [env]);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => {
      void refresh();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [refresh]);

  useInput((input) => {
    if (input === 'r') void refresh();
  });

  return (
    <Box flexDirection="column" gap={1}>
      <Box>
        <Text bold>Overall: </Text>
        <Text color={STATUS_COLOR[overall]}>
          {STATUS_SYMBOL[overall]} {overall.toUpperCase()}
        </Text>
        <Text dimColor>
          {' '}
          {refreshing ? '(refreshing...)' : `(checked ${collectedAt?.toLocaleTimeString() ?? '-'})`}
        </Text>
      </Box>

      <ServiceTable services={services} />

      <Text dimColor>[r] refresh now - auto-refresh every {POLL_INTERVAL_MS / 1000}s</Text>
    </Box>
  );
};

interface ServiceTableProps {
  services: readonly ServiceHealth[];
}

export const ServiceTable = ({ services }: ServiceTableProps) => {
  if (services.length === 0) {
    return <Text dimColor>Loading service health...</Text>;
  }

  return (
    <Box flexDirection="column" borderStyle="round" borderColor="gray" paddingX={1}>
      <Row
        cells={[
          { text: 'STATUS', width: 9, bold: true },
          { text: 'SERVICE', width: 20, bold: true },
          { text: 'ENDPOINT', width: 44, bold: true },
          { text: 'IP ADDRESSES', width: 18, bold: true },
          { text: 'LATENCY', width: 10, bold: true },
        ]}
      />
      {services.map((service) => (
        <Row
          key={service.name}
          cells={[
            { text: `${STATUS_SYMBOL[service.status]} ${service.status}`, color: STATUS_COLOR[service.status], width: 9 },
            { text: service.name, width: 20 },
            { text: service.endpoint, width: 44 },
            { text: service.ips.length > 0 ? service.ips.join(', ') : 'unresolved', width: 18 },
            { text: service.latencyMs !== null ? `${service.latencyMs}ms` : '-', width: 10 },
          ]}
        />
      ))}
      {services
        .filter((service) => (service.hint ?? '') !== '' || (service.detail ?? '') !== '')
        .map((service) => (
          <Box key={`${service.name}-detail`} paddingLeft={1}>
            <Text dimColor>
              {service.name}: {service.detail}
              {service.hint !== undefined ? ` — hint: ${service.hint}` : ''}
            </Text>
          </Box>
        ))}
    </Box>
  );
};

interface Cell {
  text: string;
  width: number;
  bold?: boolean;
  color?: string;
}

const Row = ({ cells }: { cells: readonly Cell[] }) => (
  <Box>
    {cells.map((cell, index) => (
      <Text key={index} bold={cell.bold === true} color={cell.color}>
        {pad(cell.text, cell.width)}{' '}
      </Text>
    ))}
  </Box>
);

function pad(value: string, width: number): string {
  if (value.length > width - 1) return `${value.slice(0, Math.max(width - 4, 0))}... `;
  return value.padEnd(width, ' ');
}
