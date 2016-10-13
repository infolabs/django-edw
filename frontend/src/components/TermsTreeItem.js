import React, { Component, PropTypes } from 'react';
import {
         SEMANTIC_RULE_OR,
         SEMANTIC_RULE_XOR,
         SEMANTIC_RULE_AND,
       } from '../constants/TermsTree';

import TermsTreeIteaInfo from './TermsTreeItemInfo';

// https://github.com/Excentrics/publication-backbone/blob/master/publication_backbone/templates/publication_backbone/rubricator/partials/rubric.html

export default class TermsTreeItem extends Component {

  static propTypes = {
    term: PropTypes.object.isRequired
  };

  handleItemClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.toggle(term);
  }

  handleResetClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.resetItem(term);
  }

  render() {

    const { term, actions } = this.props;
    const semantic_rule = term.getParent().semantic_rule || SEMANTIC_RULE_AND;

    let list_item = "";
    if (!term.is_leaf && semantic_rule == SEMANTIC_RULE_AND) {
      list_item = (
        <span onClick={e => { ::this.handleItemClick(e)}}>
          <i className={term.children.length ? "ex-icon-caret-on" : "ex-icon-caret-off"}></i>
          {term.name}
        </span>
      )
    } else {
      if (semantic_rule == SEMANTIC_RULE_XOR) {
        list_item = (
          <span onClick={e => { ::this.handleItemClick(e)}}>
            <i className={term.tagged ? "ex-icon-checkbox-on" : "ex-icon-checkbox-off"}></i>
            {term.name}
          </span>
        )
      } else if (semantic_rule == SEMANTIC_RULE_AND) {
        list_item = (
            <span onClick={e => { ::this.handleItemClick(e)}}>
              <i className={term.tagged ? "ex-icon-caret-on" : "ex-icon-caret-off"}></i>
              {term.name}
            </span>
        )
      } else if (semantic_rule == SEMANTIC_RULE_OR) {
        list_item = (
          <span onClick={e => { ::this.handleItemClick(e)}}>
            <i className={term.tagged ? "ex-icon-radio-on" : "ex-icon-radio-off"}></i>
            {term.name}
          </span>
        )
      }
    }

    let description = "";
    if (term.short_description) {
      description = (
        <TermsTreeIteaInfo description={term.short_description}/>
      )
    }

    let reset_icon = "";
    if (term.children.length) {
      reset_icon = (
        <i onClick={e => { ::this.handleResetClick(e)}}
           className="ex-icon-reset" title="Reset filter"></i>
      )
    }

    let reset_item = "";
    if (term.children.length && term.semantic_rule == SEMANTIC_RULE_OR) {
      reset_item = (
        <li>
          <span onClick={e => { ::this.handleResetClick(e)}}>
          <i className={term.isChildrenTagged() ? "ex-icon-radio-off" : "ex-icon-radio-on"}></i>
          All (TODO: React Perevod)
          </span>
        </li>
      )
    }

    return (
      <li>
        {list_item}{description}{reset_icon}
        <ul>
          {reset_item}
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

