import React, { Component } from 'react';
import { withGoogleMap } from "react-google-maps";

// Map component

export default class Map extends Component {
  componentDidMount() {
    console.log('Google map', withGoogleMap)
  }
  render() {
    return <div><h3>Карта тут</h3></div>
  }
}
