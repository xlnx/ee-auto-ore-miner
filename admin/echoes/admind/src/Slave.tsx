import { CardContent, CardHeader, IconButton } from "@mui/material";
import Card from "@mui/material/Card";
import React from "react";
import { Socket } from "socket.io-client";
import { SlaveState } from "./types";
import MoreVertIcon from '@mui/icons-material/MoreVert';

export class Slave<State extends SlaveState = SlaveState>
  extends React.Component<{ value: State, socket: Socket }> {

  public render() {
    let title = `${this.props.value.device.product.manufacturer} ${this.props.value.device.product.model}`
    return (
      <Card>
        <CardHeader
          title={title}
          subheader={this.props.value.device.serial}
          action={
            <IconButton aria-label="settings">
              <MoreVertIcon />
            </IconButton>
          }
        />
        <CardContent>
          {this.renderContent()}
        </CardContent>
      </Card>
    )
  }

  protected renderContent() {
    return (<></>)
  }
}
