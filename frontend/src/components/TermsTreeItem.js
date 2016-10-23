import React, { Component } from 'react';
import * as consts from '../constants/TermsTree';

// https://github.com/Excentrics/publication-backbone/blob/master/publication_backbone/templates/publication_backbone/rubricator/partials/rubric.html

export default class TermsTreeItem extends Component {

  handleItemClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.toggle(term);
  }

  render() {

    const { term, actions } = this.props;

    let list_item = "";

    if (term.getParent() != false
        && term.isLimbDescendant()
        && !term.isLimbAndLeaf()) {

      const parent = term.getParent(),
            semantic_rule = parent.semantic_rule || consts.SEMANTIC_RULE_AND;

      let class_name = "";
      if (semantic_rule == consts.SEMANTIC_RULE_AND) {
        class_name = "ex-icon-caret-on";
      } else if (semantic_rule == consts.SEMANTIC_RULE_OR) {
        class_name = "ex-icon-radio-on";
      } else if (semantic_rule == consts.SEMANTIC_RULE_XOR) {
        class_name = "ex-icon-checkbox-on";
      }

      list_item = (
        <span onClick={e => { ::this.handleItemClick(e) } }>
          <i className={class_name}></i>
          {term.name}
        </span>
      )

    }

    let children = (term.children.map(child =>
      <TermsTreeItem key={child.id}
                     term={child}
                     actions={actions}/>)
    )

    let ret = "";
    if (list_item == "") {
      ret = <span>{children}</span>;
    } else {
      children = <ul>{children}</ul>;
      ret = <li>{list_item}{children}</li>;
    }

    return ret;
  }
}

