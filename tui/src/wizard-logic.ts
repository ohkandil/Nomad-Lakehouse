// Pure wizard logic — no React, no OpenTUI, no filesystem.
// Fully unit-testable with any test runner.

export type Step = 'welcome' | 'fields' | 'options' | 'summary' | 'quitConfirm';

export interface FieldSpec {
  label: string;
  key: string;
  secure: boolean;
  validate: (v: string) => true | string;
}

export interface WizardState {
  step: Step;
  currentIndex: number;
  formData: Record<string, string>;
  errors: Record<string, string>;
}

export type WizardAction =
  | { type: 'SET_STEP'; step: Step }
  | { type: 'NEXT_FIELD' }
  | { type: 'PREV_FIELD' }
  | { type: 'SET_FIELD_VALUE'; key: string; value: string }
  | { type: 'SET_ERROR'; key: string; error: string }
  | { type: 'CLEAR_ERROR'; key: string }
  | { type: 'LOAD_STATE'; state: Partial<WizardState> }
  | { type: 'RESET' };

export const FIELD_SPECS: readonly FieldSpec[] = [
  portValidation('MinIO API port', 'MINIO_API_PORT'),
  portValidation('MinIO console port', 'MINIO_CONSOLE_PORT'),
  required('Warehouse bucket', 'WAREHOUSE_BUCKET'),
  required('Postgres DB', 'POSTGRES_DB'),
  required('Postgres user', 'POSTGRES_USER'),
  passwordValidation('Postgres password', 'POSTGRES_PASSWORD'),
  portValidation('Postgres port', 'POSTGRES_PORT'),
  required('AWS region', 'AWS_REGION'),
  required('Dashboard domain', 'DASHBOARD_DOMAIN'),
  required('Dashboard auth user', 'DASHBOARD_AUTH_USER'),
  passwordValidation('Dashboard auth password', 'DASHBOARD_AUTH_PASSWORD'),
  required('Dashboard upstream', 'DASHBOARD_UPSTREAM'),
  required('Dashboard allowed CIDRs', 'DASHBOARD_ALLOWED_CIDRS'),
  required('MinIO root user', 'MINIO_ROOT_USER'),
  passwordValidation('MinIO root password', 'MINIO_ROOT_PASSWORD'),
] as const;

function required(label: string, key: string): FieldSpec {
  return {
    label,
    key,
    secure: false,
    validate: (v: string) => v.trim().length > 0 || `${label} is required`,
  };
}

function passwordValidation(label: string, key: string): FieldSpec {
  return {
    label,
    key,
    secure: true,
    validate: (v: string) => v.length >= 8 || `${label} must be at least 8 characters`,
  };
}

function portValidation(label: string, key: string): FieldSpec {
  return {
    label,
    key,
    secure: false,
    validate: (v: string) =>
      (/^\d+$/.test(v) && Number(v) >= 1 && Number(v) <= 65535) || `${label} must be a valid port (1-65535)`,
  };
}

/** Parse an existing .env file string into a key→value record. */
export function parseEnvContent(content: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq < 0) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    out[key] = val;
  }
  return out;
}

/** Serialise form data into .env file format. */
export function buildEnvContent(data: Record<string, string>): string {
  return (
    Object.entries(data)
      .filter(([, v]) => v !== undefined && v !== '')
      .map(([k, v]) => `${k}=${v}`)
      .join('\n') + '\n'
  );
}

/** Validate a single field by key; returns true or an error message string. */
export function validateField(key: string, value: string): true | string {
  const spec = FIELD_SPECS.find((f) => f.key === key);
  if (!spec) return true;
  return spec.validate(value);
}

/** Validate every field; returns a map of key→error for invalid fields (empty if all valid). */
export function validateAllFields(data: Record<string, string>): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const spec of FIELD_SPECS) {
    const result = spec.validate(data[spec.key] ?? '');
    if (result !== true) errors[spec.key] = result;
  }
  return errors;
}

export function createInitialState(
  saved?: Partial<{ step: Step; currentIndex: number; formData: Record<string, string> }>,
  existingEnv?: string,
): WizardState {
  const formData: Record<string, string> = {};
  if (existingEnv) Object.assign(formData, parseEnvContent(existingEnv));
  if (saved?.formData) Object.assign(formData, saved.formData);

  return {
    step: saved?.step ?? 'welcome',
    currentIndex: Math.min(saved?.currentIndex ?? 0, FIELD_SPECS.length - 1),
    formData,
    errors: {},
  };
}

export function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, step: action.step };

    case 'NEXT_FIELD': {
      if (state.step !== 'fields') return state;
      const field = FIELD_SPECS[state.currentIndex];
      const value = state.formData[field.key] ?? '';
      const result = field.validate(value);
      if (result !== true) {
        return { ...state, errors: { ...state.errors, [field.key]: result } };
      }
      const cleared = { ...state.errors, [field.key]: '' };
      if (state.currentIndex < FIELD_SPECS.length - 1) {
        return { ...state, currentIndex: state.currentIndex + 1, errors: cleared };
      }
      return { ...state, step: 'options', errors: cleared };
    }

    case 'PREV_FIELD': {
      if (state.step !== 'fields') return state;
      if (state.currentIndex > 0) return { ...state, currentIndex: state.currentIndex - 1 };
      return { ...state, step: 'welcome' };
    }

    case 'SET_FIELD_VALUE':
      return {
        ...state,
        formData: { ...state.formData, [action.key]: action.value },
        errors: { ...state.errors, [action.key]: '' },
      };

    case 'SET_ERROR':
      return { ...state, errors: { ...state.errors, [action.key]: action.error } };

    case 'CLEAR_ERROR': {
      const next = { ...state.errors };
      delete next[action.key];
      return { ...state, errors: next };
    }

    case 'LOAD_STATE':
      return { ...state, ...action.state };

    case 'RESET':
      return createInitialState();

    default:
      return state;
  }
}
