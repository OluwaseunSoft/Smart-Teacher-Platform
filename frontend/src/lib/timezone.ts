export function getDeviceTimeZone(): string {
  try {
    const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return detected && detected !== "Etc/Unknown" ? detected : "Asia/Dubai";
  } catch {
    return "Asia/Dubai";
  }
}
