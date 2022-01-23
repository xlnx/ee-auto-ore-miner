import { Chip, LinearProgress, linearProgressClasses, LinearProgressProps, styled, Typography } from "@mui/material";
import Card from "@mui/material/Card";
import { Box } from "@mui/system";
import React from "react";
import { SlaveState } from "./types";

type Props = { value: SlaveState }

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
  }

  public render() {
    const progress = Math.min(100, Math.max(0, this.props.value.storage ?? 0))
    const addr = `${this.props.value.device.host}:${this.props.value.device.port}`
    const label = this.props.value.status ?? 'unknown'
    let color: any = "error"
    switch (label) {
      case "mining": color = "success"; break
      case "docked": case "docking":
      case "discharging": case "undocked":
      case "undocking": case "deploying": color = "warning"; break
    }
    return (
      <Box m={2} p={2}>
        <Card>
          <Box p={2}>
            <h2>{addr}</h2>
            <Chip label={label} color={color} variant="outlined" />
            <Box pt={2}>
              <BorderLinearProgress variant="determinate" value={progress} />
            </Box>
          </Box>
        </Card>
      </Box>
    )
  }
}
