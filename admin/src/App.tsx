import React from 'react';
import './App.css';
import { Slave } from './Slave';
import { io } from "socket.io-client";
import { SlaveState } from './types';
import { Grid } from '@mui/material';

type Props = {}

type States = {
  [_: string]: SlaveState | null
}

class App extends React.Component<Props, States> {

  private readonly socket = io(`${window.location.protocol}//${window.location.host}`)

  constructor(props: {}) {
    super(props)
    console.log('ctor()')
    this.socket.emit('client_init')
    this.socket.on('update_slave', (states: States) => {
      console.log('update_slave', states)
      this.setState(states)
    })
    this.socket.on('remove_slave', (sid) => {
      console.log('remove_slave', sid)
      this.setState({ [sid]: null })
    })
  }

  public render() {
    let slaves: SlaveState[] = []
    for (let sid in this.state) {
      let slave = this.state[sid]
      if (slave != null) {
        slaves.push(slave)
      }
    }
    let doms = slaves.map(slave => (
      <Grid item xs={12}>
        <Slave value={slave}></Slave>
      </Grid>
    ))
    return (
      <Grid container spacing={3}>
        {doms}
      </Grid>
    )
  }
}

export default App
