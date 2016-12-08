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

    const props = this.props,
          term = props.term,
          details = props.details,
          actions = props.actions,
          tagged = props.tagged,
          expanded = props.expanded,
          info_expanded = props.info_expanded,
          real_potential = props.real_potential,
          children = term.children,
          parent = term.parent;

    let render_item = "",
        reset_icon = "",
        reset_item = "",
        info = "",
        semantic_class = "",
        state_class = "";

    const show_children = !term.isLimbOrAnd() && tagged[term.id] || expanded[term.id];

    if (term.isVisible()) {

      const parent = term.parent,
            rule = parent.semantic_rule || consts.SEMANTIC_RULE_AND,
            siblings = term.siblings;

      if (term.isLimbOrAnd()) {
        semantic_class = "ex-and";
      } else {
        switch (rule) {
          case consts.SEMANTIC_RULE_OR:
            semantic_class = "ex-or";
            break;
          case consts.SEMANTIC_RULE_XOR:
            semantic_class = "ex-xor";
            break;
        }
      }

      if ((term.isLimbOrAnd() && expanded[term.id] == true) ||
          (!term.isLimbOrAnd() && tagged[term.id] == true)) {
        state_class = 'ex-on';
      } else {
        state_class = 'ex-off';
      }

      if (rule != consts.SEMANTIC_RULE_AND
          && tagged[term.id] != true
          && tagged.isAnyTagged(siblings))
        state_class = 'ex-other';

      render_item = (
        <span className="ex-label" onClick={e => { ::this.handleItemClick(e) } } >
          <i className="ex-icon-slug"></i>
          {term.name}
        </span>
      );

      if (term.semantic_rule == consts.SEMANTIC_RULE_OR && show_children) {
        let any_tagged = tagged.isAnyTagged(children),
            reset_class = any_tagged ? "ex-or ex-off" : "ex-or ex-on";

        reset_item = (
          <li className={reset_class}>
              <span className="ex-label" onClick={e => { ::this.handleResetClick(e) } } >
                <i className="ex-icon-slug"></i>
                { gettext("All") }
              </span>
          </li>
        );
      }

      if (children.length && !tagged.isAncestorTagged(term) &&
          tagged.isAnyTagged(children)) {
        reset_icon = (
          <i onClick={e => { ::this.handleResetClick(e) } }
             className="ex-icon-reset"></i>
        );
      }

      if (term.short_description) {
        info = (
          <TermsTreeItemInfo term={term}
                             info_expanded={info_expanded}
                             details={details}
                             actions={actions}/>
        );
      }
    }

    let render_children = (children.map(child =>
      <TermsTreeItem key={child.id}
                     term={child}
                     details={details}
                     tagged={tagged}
                     expanded={expanded}
                     info_expanded={info_expanded}
                     real_potential={real_potential}
                     actions={actions}/>)
    )

    let li_clasname = semantic_class + " " + state_class + " ";
    if (real_potential.has_metadata && !real_potential.rils[term.id]) {
      li_clasname += !real_potential.pots[term.id] ? "ex-no-potential " : "ex-no-real "
    }

    let ret = "";
    if (render_item == "") {
      ret = <span>{render_children}</span>;
    } else {
      if (show_children)
        render_children = <ul>{reset_item}{render_children}</ul>;
      else
        render_children = ""
      ret = (
        <li className={li_clasname}
            data-structure={term.structure}
            data-view-class={term.view_class}
            data-slug={term.slug}>
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

