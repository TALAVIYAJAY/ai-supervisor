/**
 * Date and Time Formatter Utilities
 * Formats timestamps directly in the user's local timezone (IST, 12-hour AM/PM format).
 */

export function parseLocalDate(isoString?: string | null): Date | null {
  if (!isoString) return null;
  // Normalize string to ISO without double-timezone shifting
  const cleanStr = isoString.trim().replace(/Z$/, '').replace(' ', 'T');
  const d = new Date(cleanStr);
  return isNaN(d.getTime()) ? null : d;
}

export function formatLocalDateTime(isoString?: string | null): string {
  if (!isoString) return 'None';
  try {
    const d = parseLocalDate(isoString);
    if (!d) return isoString;
    return d.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return isoString;
  }
}

export function formatLocalTime(isoString?: string | null): string {
  if (!isoString) return '';
  try {
    const d = parseLocalDate(isoString);
    if (!d) return isoString;
    return d.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  } catch {
    return isoString;
  }
}
