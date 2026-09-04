export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

export function hasAllowedKeys(
  value: Record<string, unknown>,
  required: readonly string[],
  optional: readonly string[],
): boolean {
  const keys = Object.keys(value);
  return required.every((key) => keys.includes(key))
    && keys.every((key) => required.includes(key) || optional.includes(key));
}

export function isCanonicalColor(value: unknown): value is `#${string}` {
  return typeof value === "string" && /^#[0-9a-f]{6}(?:[0-9a-f]{2})?$/.test(value);
}

export function isBoundedString(value: unknown, maxLength = 128): value is string {
  return typeof value === "string" && value.length >= 1 && value.length <= maxLength;
}

export function assertNever(value: never): never {
  throw new Error(`Unexpected value: ${String(value)}`);
}
