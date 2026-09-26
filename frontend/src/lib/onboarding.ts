const key = (userId: number) => `suhail.onboarded:${userId}`;

export function isOnboarded(userId: number): boolean {
  return localStorage.getItem(key(userId)) === "1";
}

export function markOnboarded(userId: number): void {
  localStorage.setItem(key(userId), "1");
}
