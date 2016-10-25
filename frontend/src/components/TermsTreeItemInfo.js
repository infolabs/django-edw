import React, { Component } from 'react';

export default class TermsTreeItemInfo extends Component {

  handleIconClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    console.log("OLOLO")
    actions.showInfo(term);
  }

  handleCloseClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.hideInfo(term);
  }

  render() {

    const { term, info_expanded, actions } = this.props;


    return (
      <span className="ex-description-wrapper">
        <i className="ex-icon-info"
           title="Info"
           onClick={e => { ::this.handleIconClick(e)}}></i>
        <div className={info_expanded[term.id] == true ? "ex-baloon ex-baloon-show" : "ex-baloon ex-baloon-hide"}>
        <button type="button"
                className="ex-close"
                onClick={e => { ::this.handleCloseClick(e)}}>×</button>
            {term.short_description}
        </div>
      </span>
    )
  }
}
