import { InputValueSchema, ProblemInputField } from '../types';

const SCHEMA_PREFIX = 'Arguments appear in this order:';
const SCHEMA_SUFFIX = '. Every list begins';

const integer = (): InputValueSchema => ({ kind: 'int' });
const stringValue = (): InputValueSchema => ({ kind: 'str' });
const integerList = (): InputValueSchema => ({ kind: 'list', item: integer() });

const INSTRUCTOR_SCHEMAS: Record<string, ProblemInputField[]> = {
  'prob-1': [
    { name: 'elements', schema: integerList() },
    { name: 'target', schema: integer() }
  ],
  'prob-2': [
    { name: 'elements', schema: integerList() },
    { name: 'target', schema: integer() }
  ],
  'prob-3': [{ name: 'elements', schema: integerList() }],
  'prob-5': [{ name: 's', schema: stringValue() }]
};

const isInputSchema = (value: unknown): value is InputValueSchema => {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as InputValueSchema;
  if (!['int', 'float', 'str', 'bool', 'list', 'optional'].includes(candidate.kind)) return false;
  return !['list', 'optional'].includes(candidate.kind) || isInputSchema(candidate.item);
};

/**
 * Read the language-neutral argument metadata embedded by the dataset
 * normalizer. This never modifies the problem or its raw stdin.
 */
export const parseProblemInputSchema = (
  description: string,
  problemId?: string
): ProblemInputField[] => {
  if (problemId && INSTRUCTOR_SCHEMAS[problemId]) return INSTRUCTOR_SCHEMAS[problemId];

  const start = description.indexOf(SCHEMA_PREFIX);
  if (start < 0) return [];
  const schemaStart = start + SCHEMA_PREFIX.length;
  const suffix = description.indexOf(SCHEMA_SUFFIX, schemaStart);
  const source = description.slice(schemaStart, suffix < 0 ? undefined : suffix);
  const fields: ProblemInputField[] = [];
  let cursor = 0;

  while (cursor < source.length) {
    const nameMatch = source.slice(cursor).match(/^\s*,?\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*/);
    if (!nameMatch) break;
    const name = nameMatch[1];
    const objectStart = cursor + nameMatch[0].length;
    if (source[objectStart] !== '{') break;

    let depth = 0;
    let quoted = false;
    let escaped = false;
    let objectEnd = -1;
    for (let index = objectStart; index < source.length; index += 1) {
      const character = source[index];
      if (quoted) {
        if (escaped) escaped = false;
        else if (character === '\\') escaped = true;
        else if (character === '"') quoted = false;
        continue;
      }
      if (character === '"') quoted = true;
      else if (character === '{') depth += 1;
      else if (character === '}' && --depth === 0) {
        objectEnd = index + 1;
        break;
      }
    }
    if (objectEnd < 0) break;

    try {
      const schema = JSON.parse(source.slice(objectStart, objectEnd));
      if (!isInputSchema(schema)) return [];
      fields.push({ name, schema });
    } catch {
      return [];
    }
    cursor = objectEnd;
  }

  return source.slice(cursor).trim() ? [] : fields;
};

type ParsedValue = string | number | bigint | boolean | null | ParsedValue[];

const parseScalar = (raw: string, kind: InputValueSchema['kind']): ParsedValue => {
  if (kind === 'str') return raw;
  const token = raw.trim();
  if (kind === 'bool') {
    if (!['0', '1', 'true', 'false'].includes(token.toLowerCase())) throw new Error('Invalid boolean');
    return token === '1' || token.toLowerCase() === 'true';
  }
  if (kind === 'int') {
    if (!/^-?\d+$/.test(token)) throw new Error('Invalid integer');
    return BigInt(token);
  }
  const number = Number(token);
  if (!Number.isFinite(number)) throw new Error('Invalid number');
  return number;
};

const readValue = (
  lines: string[],
  lineIndex: number,
  schema: InputValueSchema,
  depth = 0
): { value: ParsedValue; nextLine: number } => {
  if (depth > 20) throw new Error('Input structure is too deeply nested');
  if (schema.kind === 'optional') {
    const present = lines[lineIndex]?.trim();
    if (present === '0') return { value: null, nextLine: lineIndex + 1 };
    if (present !== '1' || !schema.item) throw new Error('Invalid optional value');
    return readValue(lines, lineIndex + 1, schema.item, depth + 1);
  }

  if (schema.kind !== 'list') {
    if (lineIndex >= lines.length) throw new Error('Missing scalar input');
    return { value: parseScalar(lines[lineIndex], schema.kind), nextLine: lineIndex + 1 };
  }

  if (!schema.item || lineIndex >= lines.length) throw new Error('Missing list input');
  const length = Number.parseInt(lines[lineIndex].trim(), 10);
  if (!Number.isInteger(length) || length < 0 || length > 100000) throw new Error('Invalid list length');

  if (['int', 'float', 'bool'].includes(schema.item.kind)) {
    const tokens = (lines[lineIndex + 1] || '').trim().split(/\s+/).filter(Boolean);
    if (tokens.length !== length) throw new Error('List payload does not match its length');
    const hasEmptyPayloadLine = length === 0 && lines[lineIndex + 1] === '';
    return {
      value: tokens.slice(0, length).map((token) => parseScalar(token, schema.item!.kind)),
      nextLine: lineIndex + (hasEmptyPayloadLine || length > 0 ? 2 : 1)
    };
  }

  const values: ParsedValue[] = [];
  let nextLine = lineIndex + 1;
  for (let item = 0; item < length; item += 1) {
    const parsed = readValue(lines, nextLine, schema.item, depth + 1);
    values.push(parsed.value);
    nextLine = parsed.nextLine;
  }
  return { value: values, nextLine };
};

const scalarText = (value: ParsedValue): string => {
  if (typeof value === 'string') return JSON.stringify(value);
  if (value === null) return 'null';
  return String(value);
};

const listText = (value: ParsedValue[]): string =>
  `[${value.map((item) => Array.isArray(item) ? listText(item) : scalarText(item)).join(', ')}]`;

const isMatrix = (value: ParsedValue): value is ParsedValue[][] =>
  Array.isArray(value) && value.every((row) => Array.isArray(row));

const MATRIX_FIELD_NAMES = new Set(['matrix', 'grid', 'board', 'image', 'mat']);

const arrayLabel = (name: string): string =>
  ['nums', 'arr', 'array', 'values'].includes(name.toLowerCase()) ? 'elements' : name;

/** Convert raw judge stdin to labels for display only. */
export const formatInputForDisplay = (
  rawInput: string,
  fields: ProblemInputField[] | undefined
): string => {
  if (!fields?.length) return rawInput.replace(/\r\n/g, '\n').replace(/\n$/, '') || '∅ (empty input)';
  const normalized = rawInput.replace(/\r\n/g, '\n').replace(/\n$/, '');
  const lines = normalized.split('\n');

  try {
    const parsedFields: Array<{ field: ProblemInputField; value: ParsedValue }> = [];
    let lineIndex = 0;
    for (const field of fields) {
      const parsed = readValue(lines, lineIndex, field.schema);
      parsedFields.push({ field, value: parsed.value });
      lineIndex = parsed.nextLine;
    }

    const listFields = parsedFields.filter(({ value }) => Array.isArray(value));
    const hasExplicitN = parsedFields.some(({ field, value }) => field.name === 'n' && !Array.isArray(value));
    const hasExplicitEdgeCount = parsedFields.some(({ field, value }) =>
      ['m', 'edgecount', 'edgescount'].includes(field.name.toLowerCase()) && !Array.isArray(value)
    );
    const hasEdges = parsedFields.some(({ field, value }) =>
      field.name.toLowerCase() === 'edges'
      && isMatrix(value)
    );
    const displayLines: string[] = [];

    for (const { field, value } of parsedFields) {
      if (!Array.isArray(value)) {
        const fieldName = field.name.toLowerCase();
        const label = hasEdges && ['n', 'v', 'vertices'].includes(fieldName)
          ? 'vertices'
          : hasEdges && ['m', 'edgecount', 'edgescount'].includes(fieldName)
            ? 'edges'
            : field.name;
        displayLines.push(`${label} = ${scalarText(value)}`);
        continue;
      }

      if (isMatrix(value) && MATRIX_FIELD_NAMES.has(field.name.toLowerCase())) {
        const rowLengths = value.map((row) => row.length);
        const sameWidth = rowLengths.length > 0 && rowLengths.every((length) => length === rowLengths[0]);
        displayLines.push(`rows = ${value.length}`);
        if (sameWidth) displayLines.push(`cols = ${rowLengths[0]}`);
        displayLines.push(`${field.name} =`);
        displayLines.push('[');
        value.forEach((row, index) => {
          displayLines.push(`  ${listText(row)}${index < value.length - 1 ? ',' : ''}`);
        });
        displayLines.push(']');
        continue;
      }

      if (isMatrix(value)) {
        if (field.name.toLowerCase() === 'edges') {
          if (!hasExplicitEdgeCount) displayLines.push(`edges = ${value.length}`);
          displayLines.push('edge list:');
          value.forEach((edge) => displayLines.push(edge.map(scalarText).join(' ')));
          continue;
        }
        displayLines.push(`${field.name}Count = ${value.length}`);
        displayLines.push(`${field.name} =`);
        displayLines.push('[');
        value.forEach((row, index) => {
          displayLines.push(`  ${listText(row)}${index < value.length - 1 ? ',' : ''}`);
        });
        displayLines.push(']');
        continue;
      }

      const label = arrayLabel(field.name);
      const countLabel = hasExplicitN
        ? undefined
        : listFields.length === 1
          ? 'n'
          : `${label}Count`;
      if (countLabel) displayLines.push(`${countLabel} = ${value.length}`);
      displayLines.push(`${label} = ${listText(value)}`);
    }
    if (lineIndex !== lines.length) throw new Error('Unparsed stdin remains');
    return displayLines.join('\n');
  } catch {
    // Unknown or legacy inputs stay truthful instead of receiving guessed labels.
    return normalized || '∅ (empty input)';
  }
};

export const rawStdinText = (rawInput: string): string =>
  rawInput.replace(/\r\n/g, '\n').replace(/\n$/, '') || '∅ (empty input)';

export const describeInputSchema = (fields: ProblemInputField[] | undefined): string[] => {
  if (!fields?.length) return [];
  const descriptions: string[] = [];
  const hasEdges = fields.some((field) => field.name.toLowerCase() === 'edges');
  for (const field of fields) {
    const { kind, item } = field.schema;
    const name = hasEdges && ['n', 'v', 'vertices'].includes(field.name.toLowerCase()) ? 'vertices' : field.name;
    if (kind === 'str') descriptions.push(`${name}: one raw text line (no automatic length prefix)`);
    else if (kind === 'list' && item?.kind === 'list' && field.name.toLowerCase() === 'edges') descriptions.push('edges: edge count followed by each edge size and values');
    else if (kind === 'list' && item?.kind === 'list') descriptions.push(`${name}: row count followed by each row's size and values`);
    else if (kind === 'list') descriptions.push(`${arrayLabel(field.name)}: element count followed by the values`);
    else descriptions.push(`${name}: one ${kind === 'int' ? 'integer' : kind} value`);
  }
  return descriptions;
};
