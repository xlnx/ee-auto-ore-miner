import { Card, CardContent, CardHeader, Chip, Grid, IconButton, LinearProgress, linearProgressClasses, LinearProgressProps, styled, Typography } from "@mui/material";
import { Box } from "@mui/system";
import { Slave } from "./Slave";
import { MinerState } from "./types";
import MoreVertIcon from '@mui/icons-material/MoreVert';

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

export class Miner extends Slave<MinerState> {

  constructor(props: any) {
    super(props)
    this.toggle = this.toggle.bind(this)
  }

  public render() {
    const label = this.props.value.state.status ?? 'unknown'
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
    if (this.props.value.state.online) {
      online = {
        label: "online",
        color: "success",
        variant: "outlined"
      }
    }
    const chips = [
      (
        <Grid item>
          <Chip label={label} color={color} variant="outlined" />
        </Grid>
      ),
    ]
    if (this.props.value.state.local) {
      const [x, y, z] = this.props.value.state.local
      const color = (x + y) ? "warning" : "success"
      chips.push((
        <Grid item>
          <Chip label={`${x}/${y}/${z}`} color={color} variant="outlined" />
        </Grid>
      ))
    }
    if (!this.props.value.dead) {
      chips.push((
        <Grid item>
          <Chip label={online.label} color={online.color} variant={online.variant} onClick={this.toggle} />
        </Grid>
      ))
    } else {
      chips.push((
        <Grid item>
          <Chip label="abnormal" color="error" variant="filled" />
        </Grid>
      ))
    }
    let subtitle = this.props.value.device.product.manufacturer
    subtitle += ' ' + this.props.value.device.product.model
    subtitle += ' - ' + this.props.value.device.serial
    let title = `${this.props.value.device.id}`
    if (this.props.value.state.system) {
      title += ` - ${this.props.value.state.system}`
    }
    return (
      <Card>
        <CardHeader
          title={title}
          subheader={subtitle}
          action={
            <IconButton aria-label="settings">
              <MoreVertIcon />
            </IconButton>
          }
        />
        <CardContent>
          <Grid container spacing={1}>
            {chips}
          </Grid>
          <Box pt={2}>
            <BorderLinearProgress
              variant="determinate"
              value={Math.min(100, Math.max(0, this.props.value.state.storage ?? 0))}
            />
          </Box>
        </CardContent>
      </Card>
    )
  }

  private toggle() {
    console.log('toggle')
    this.props.socket.emit(
      'dispatch',
      'task',
      this.props.value.sid,
      this.props.value.state.online ? 'offline' : 'online'
    )
  }
}