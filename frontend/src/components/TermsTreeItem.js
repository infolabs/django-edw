import React, { Component, PropTypes } from 'react';
import {
         SEMANTIC_RULE_OR,
         SEMANTIC_RULE_XOR,
         SEMANTIC_RULE_AND,
         STRUCTURE_LIMB,
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
    const siblings_tagged = term.getParent().areChildrenTagged && term.getParent().areChildrenTagged();
    const expanded = term.isExpanded();

    let list_item = "";
    if (!term.isLimbLine()
        || (term.structure == STRUCTURE_LIMB && term.is_leaf)
        ) {
      list_item = "";
    } else {
      if (semantic_rule == SEMANTIC_RULE_XOR) {
        list_item = (
          <span onClick={e => { ::this.handleItemClick(e)}} className={expanded ? "" : siblings_tagged ? "ex-dim" : ""}>
            <i className={expanded ? "ex-icon-checkbox-on" : siblings_tagged ? "ex-icon-checkbox-off" : "ex-icon-checkbox-dot"}></i>
            {term.name}
          </span>
        )
      } else if (semantic_rule == SEMANTIC_RULE_AND || term.structure == STRUCTURE_LIMB) {
        list_item = (
            <span onClick={e => { ::this.handleItemClick(e)}}>
              <i className={expanded ? "ex-icon-caret-on" : "ex-icon-caret-off"}></i>
              {term.name}
            </span>
        )
      } else if (semantic_rule == SEMANTIC_RULE_OR) {
        list_item = (
          <span onClick={e => { ::this.handleItemClick(e)}} className={expanded ? "" : siblings_tagged ? "ex-dim" : ""}>
            <i className={expanded ? "ex-icon-radio-on" : "ex-icon-radio-off"}></i>
            {term.name}
          </span>
        )
      }
    }

    let description = "";
    if (term.short_description) {
      description = (
        <TermsTreeIteaInfo description={term.short_description}/>
      );
    }

    let reset_icon = "";
    if (expanded && term.areChildrenTagged()) {
      reset_icon = (
        <i onClick={e => { ::this.handleResetClick(e)}}
           className="ex-icon-reset" title="Reset filter"></i>
      );
    }

    let reset_item = "";
    if (term.children.length && term.semantic_rule == SEMANTIC_RULE_OR) {
      reset_item = (
        <li>
          <span onClick={e => { ::this.handleResetClick(e)}} className={term.areChildrenTagged() ? "ex-dim" : ""}>
          <i className={term.areChildrenTagged() ? "ex-icon-radio-off" : "ex-icon-radio-on"}></i>
          All (TODO: React Perevod)
          </span>
        </li>
      );
    }

    let term_children = (
    <frag>
      {term.children.map(term =>
            <TermsTreeItem key={term.id}
                           term={term}
                           actions={actions}
                           />
      )}
    </frag>
    );

    let final_render = "";
    if (list_item == "") {
      final_render = term_children;
    } else {
      if (term.isExpanded()) {
        term_children = (
          <ul>
            {reset_item}
            {term_children}
          </ul>
        );
      } else {
        term_children = "";
      }

      final_render = (
        <li>
          {list_item}{description}{reset_icon}
          {term_children}
        </li>
      )
    }

    return final_render;
  }
}

