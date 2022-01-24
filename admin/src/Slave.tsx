import { CardActionArea, CardContent, CardHeader, Chip, Grid, IconButton, LinearProgress, linearProgressClasses, LinearProgressProps, styled, Typography } from "@mui/material";
import Card from "@mui/material/Card";
import { Box } from "@mui/system";
import React from "react";
import { Socket } from "socket.io-client";
import { SlaveState } from "./types";
import MoreVertIcon from '@mui/icons-material/MoreVert';

type Props = {
  value: SlaveState,
  socket: Socket,
}

function LinearProgressWithLabel(props: LinearProgressProps & { value: number }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <Box sx={{ width: '100%', mr: 1 }}>
        <LinearProgress variant="determinate" {...props} />
      </Box>
      <Box sx={{ minWidth: 35 }}>
        <Typography variant="body2" color="text.secondary">{`${Math.round(
          props.value,
        )}%`}</Typography>
      </Box>
    </Box>
  );
}

const BorderLinearProgress = styled(LinearProgressWithLabel)(({ theme }) => ({
  height: 10,
  borderRadius: 5,
  [`&.${linearProgressClasses.colorPrimary}`]: {
    backgroundColor: theme.palette.grey[theme.palette.mode === 'light' ? 200 : 800],
  },
  [`& .${linearProgressClasses.bar}`]: {
    borderRadius: 5,
    backgroundColor: theme.palette.mode === 'light' ? '#1a90ff' : '#308fe8',
  },
}))

export class Slave extends React.Component<Props> {

  constructor(props: Props) {
    super(props)
    this.toggle = this.toggle.bind(this)
  }

  public render() {
    const label = this.props.value.status ?? 'unknown'
    let color: any = "error"
    switch (label) {
      case "mining": color = "success"; break
      case "docked": case "docking":
      case "discharging": case "undocked":
      case "undocking": case "deploying": color = "warning"; break
    }
    let online: any = {
      label: "offline",
      color: "error",
      variant: "filled"
    }
    if (this.props.value.online) {
      online = {
        label: "online",
        color: "success",
        variant: "outlined"
      }
    }
    return (
      <Box m={2} p={2}>
        <Card>
          <CardHeader
            title={`${this.props.value.device.host}:${this.props.value.device.port}`}
            subheader={`${this.props.value.device.product.manufacturer} ${this.props.value.device.product.model}`}
            action={
              <IconButton aria-label="settings">
                <MoreVertIcon />
              </IconButton>
            }
          />
          <CardContent>
            <Grid container spacing={1}>
              <Grid item>
                <Chip label={label} color={color} variant="outlined" />
              </Grid>
              <Grid item>
                <Chip label={online.label} color={online.color} variant={online.variant} onClick={this.toggle}></Chip>
              </Grid>
            </Grid>
            <Box pt={2}>
              <BorderLinearProgress
                variant="determinate"
                value={Math.min(100, Math.max(0, this.props.value.storage ?? 0))}
              />
            </Box>
          </CardContent>
        </Card>
      </Box>
    )
  }

  private toggle() {
    console.log('toggle')
    this.props.socket.emit(
      'slave_task',
      this.props.value.sid,
      this.props.value.online ? 'offline' : 'online'
    )
  }
}
