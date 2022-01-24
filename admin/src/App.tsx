import React from 'react';
import './App.css';
import { Slave } from './Slave';
import { io } from "socket.io-client";
import { SlaveState } from './types';
import { AppBar, Grid, IconButton, Toolbar, Typography } from '@mui/material';
import { Box } from '@mui/system';
import MenuIcon from '@mui/icons-material/Menu';

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
        <Slave value={slave} socket={this.socket}></Slave>
      </Grid>
    ))
    return (
      <Box>
        <AppBar position="static">
          <Toolbar>
            <IconButton
              size="large"
              edge="start"
              color="inherit"
              aria-label="open drawer"
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography
              variant="h6"
              noWrap
              component="div"
              sx={{ flexGrow: 1, display: { xs: 'none', sm: 'block' } }}
            >
              Admin
            </Typography></Toolbar>
        </AppBar>
        <Grid container spacing={3}>
          {doms}
        </Grid>
      </Box>
    )
  }
}

export default App
