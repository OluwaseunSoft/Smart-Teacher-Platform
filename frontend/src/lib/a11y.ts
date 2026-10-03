export function buildAriaLabel(label: string, value?: string | number) {
  return value === undefined || value === null ? label : `${label}: ${value}`;
}

export function clampCssValue(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}
