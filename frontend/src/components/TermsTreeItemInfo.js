import React, { Component } from 'react';

export default class TermsTreeItemInfo extends Component {

  handleIconClick(e) {
    const { term, infoExpanded, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    if (!infoExpanded[term.id])
      actions.showInfo(term);
    else
      actions.hideInfo(term);
  }

  handleCloseClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.hideInfo(term);
  }

  render() {

    const { term, infoExpanded, actions, details } = this.props;

    let description = term.short_description;
    if (infoExpanded[term.id]) {
      if (details[term.id])
        description = details[term.id].description;
      else
        actions.getTermsItem(term.url);
    }

    return (
      <span className="ex-description-wrapper">
        <i className="ex-icon-info"
           title="Info"
           onClick={e => { ::this.handleIconClick(e);}}/>
        <div className={infoExpanded[term.id] ? 'ex-baloon ex-baloon-show' : 'ex-baloon ex-baloon-hide'}>
          <div className="ex-arrow"/>
          <button type="button"
                className="ex-close"
                onClick={e => { ::this.handleCloseClick(e); }}>×</button>
          <p>{description}</p>
        </div>
      </span>
    );
  }
}
