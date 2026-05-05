// Clipboard Types

export interface ClipboardState {
  mode: 'copy' | 'cut' | null
  paths: string[]
  timestamp: number
}