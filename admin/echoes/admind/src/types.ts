export interface SlaveState {
  sid: string,
  device: {
    id: string,
    serial: string,
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
  type: string,
  heartbeat: number,
  dead: number,
  state: {}
}

export interface MinerState extends SlaveState {
  state: {
    online: number,
    status: ('docked' | 'discharging' | 'undocking' |
      'undocked' | 'deploying' | 'mining' | 'docking' | 'unknown'),
    local: number[],
    system: string,
    storage: number,
  }
}
