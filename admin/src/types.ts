export type SlaveState = {
  sid: string,
  device: {
    host: string,
    port: number,
  },
  storage: number,
  status: ('docked' | 'discharging' | 'undocking' |
    'undocked' | 'deploying' | 'mining' | 'docking' | 'unknown'),
  heartbeat: number,
}