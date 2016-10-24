import React, { Component } from 'react';
import * as consts from '../constants/TermsTree';
import TermsTreeItemInfo from './TermsTreeItemInfo';


export default class TermsTreeItem extends Component {

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

    const { term, actions, tagged, expanded, info_expanded} = this.props,
          term_children = term.getChildren();

    let render_item = "",
        reset_icon = "",
        reset_item = "",
        info = "";

    if (term.getParent() != false &&
        term.isLimbDescendant() &&
        !term.isLimbAndLeaf()) {

      const parent = term.getParent(),
            rule = parent.semantic_rule || consts.SEMANTIC_RULE_AND,
            siblings = term.getSiblings();

      let i_class_name = "";
      switch (rule) {
        case consts.SEMANTIC_RULE_AND:
          i_class_name = "ex-icon-caret";
          break;
        case consts.SEMANTIC_RULE_OR:
          i_class_name = "ex-icon-radio";
          break;
        case consts.SEMANTIC_RULE_XOR:
          i_class_name = "ex-icon-checkbox";
          break;
      }

      if ((rule == consts.SEMANTIC_RULE_AND && expanded[term.id] == true) ||
          (rule != consts.SEMANTIC_RULE_AND && tagged[term.id] == true))
        i_class_name += '-on';
      else if (rule == consts.SEMANTIC_RULE_XOR
               && !tagged.isAnyTagged(siblings))
        i_class_name += '-dot';
      else
        i_class_name += '-off';

      let span_class_name = false;
      if (rule != consts.SEMANTIC_RULE_AND
          && tagged[term.id] != true
          && tagged.isAnyTagged(siblings))
        span_class_name = 'ex-dim';

      render_item = (
        <span onClick={e => { ::this.handleItemClick(e) } }
              className={span_class_name}>
          <i className={i_class_name}></i>
          {term.name}
        </span>
      );

      if (term.semantic_rule == consts.SEMANTIC_RULE_OR &&
          expanded[term.id]) {
        let any_tagged = tagged.isAnyTagged(term_children),
            r_span_class_name = any_tagged ? "ex-dim" : "",
            r_i_class_name = any_tagged ? "ex-icon-radio-off" : "ex-icon-radio-on";

        reset_item = (
          <li>
            <span onClick={e => { ::this.handleResetClick(e) } }
                  className={r_span_class_name}>
              <i className={r_i_class_name}></i>
              All (TODO: React Perevod)
            </span>
          </li>
        );
      }

      if (term_children.length &&
          tagged.isAnyTagged(term_children)) {
        reset_icon = (
          <i onClick={e => { ::this.handleResetClick(e) } }
             className="ex-icon-reset"></i>
        );
      }

      if (term.short_description) {
        info = (
          <TermsTreeItemInfo term={term}
                             info_expanded={info_expanded}
                             actions={actions}/>
        );
      }
    }

    let render_children = (term_children.map(child =>
      <TermsTreeItem key={child.id}
                     term={child}
                     tagged={tagged}
                     expanded={expanded}
                     info_expanded={info_expanded}
                     actions={actions}/>)
    )

    let ret = "";
    if (render_item == "") {
      ret = <span>{render_children}</span>;
    } else {
      if (expanded[term.id] == true)
        render_children = <ul>{reset_item}{render_children}</ul>;
      else
        render_children = ""
      ret = (
        <li>
          {render_item}
          {info}
          {reset_icon}
          {render_children}
        </li>
      );
    }

    return ret;
  }
}

