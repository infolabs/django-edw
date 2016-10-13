import React, { Component, PropTypes } from 'react';

export default class TermsTreeItemInfo extends Component {

  constructor(props) {
    super(props);
    this.state = {'baloon': false };
  }

  handleIconClick(e) {
    e.preventDefault();
    e.stopPropagation();
    this.setState({'baloon': true });
  }

  handleCloseClick(e) {
    e.preventDefault();
    e.stopPropagation();
    this.setState({'baloon': false });
  }

  render() {
    return (
      <span className="ex-description-wrapper">
        <i className="ex-icon-info"
           title="Info"
           onClick={e => { ::this.handleIconClick(e)}}></i>
        <div className={this.state.baloon ? "ex-baloon ex-baloon-show" : "ex-baloon ex-baloon-hide"}>
        <button type="button"
                className="ex-close"
                onClick={e => { ::this.handleCloseClick(e)}}>×</button>
            {this.props.description}
        </div>
      </span>
    )
  }
}
