export function formatWhen(iso: string) {
  return new Date(iso).toISOString().slice(0, 16).replace('T', ' ') + 'Z'
}
