export type SlaveState = {
  sid: string,
  device: {
    host: string,
    port: number,
    product: {
      manufacturer: string,
      model: string,
      abi: string,
    },
    soc: {
      manufacturer: string,
      model: string,
    }
  },
  online: number,
  dead: number,
  status: ('docked' | 'discharging' | 'undocking' |
    'undocked' | 'deploying' | 'mining' | 'docking' | 'unknown'),
  heartbeat: number,
  local: number[],
  system: string,
  storage: number,
}