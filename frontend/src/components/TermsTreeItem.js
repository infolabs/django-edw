import React, { Component, PropTypes } from 'react';
import {
         SEMANTIC_RULE_OR,
         SEMANTIC_RULE_XOR,
         SEMANTIC_RULE_AND,
       } from '../constants/TermsTree';

// https://github.com/Excentrics/publication-backbone/blob/master/publication_backbone/templates/publication_backbone/rubricator/partials/rubric.html

export default class TermsTreeItem extends Component {

  static propTypes = {
    term: PropTypes.object.isRequired
  };

  handleClick(e) {
    const { term, actions } = this.props;
    e.preventDefault()
    e.stopPropagation()
    actions.toggle(term)
  }

  render() {

    const { term, actions } = this.props;
    const semantic_rule = term.parent.semantic_rule;

    let list_item = "";
    if (!term.is_leaf) {
      list_item = (
        <span>
          <i className="ex-icon-details ex-expand"></i>
          <span className="ex-title children-tagged">
            {term.name}
          </span>
        </span>
      )
    } else {
      if (semantic_rule == SEMANTIC_RULE_XOR) {
        list_item = (
          <span className="ex-label">
            <input type="checkbox" checked={term.tagged}/>
            <i className="ex-ico-slug"></i>
            {term.name}
          </span>
        )
      } else if (semantic_rule == SEMANTIC_RULE_AND) {
        list_item = (
            <span className="ex-label">
              <i className="ex-ico-slug"></i>
              {term.name}
            </span>
        )
      } else if (semantic_rule == SEMANTIC_RULE_OR) {
        list_item = (
          <span className="ex-label">
            <input type="radio" checked={term.tagged}/>
            <i className="ex-ico-slug"></i>
            {term.name}
          </span>
        )
      }
    }

    let short_description = "";
    if ( term.short_description && (!term.is_leaf || term.children.length) ) {
      short_description = (
        <span className="ex-description-wrapper">
          <i className="ex-icon-question" title="{% trans 'Info' %}"></i>
          <div className="ex-baloon">
            <div className="ex-arrow"></div>
            <button type="button" className="ex-close">×</button>
              {term.short_description}
          </div>
        </span>
      )
    }

    let reset_filter = "";
    if (term.children.length && term.tagged) {
      reset_filter = (
        <i className="ex-icon-reset" title="Reset filter"></i>
      )
    }

    return (
      <li onClick={e => { ::this.handleClick(e)}}>
        {list_item}{short_description}{reset_filter}
        <ul>
          {term.children.map(term =>
            <TermsTreeItem key={term.id}
                            term={term}
                            actions={actions}
                            />
          )}
        </ul>
      </li>
    )
  }
}

