import React, { Component } from 'react';
import * as consts from '../constants/TermsTree';
import TermsTreeItemInfo from './TermsTreeItemInfo';


export default class TermsTreeItem extends Component {

  handleItemClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.toggleTerm(term);
  }

  handleResetTermClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.resetTerm(term);
  }

  handleResetBranchClick(e) {
    const { term, actions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.resetBranch(term);
  }


  render() {

    const props = this.props,
          {term, details, actions, tagged, expanded, infoExpanded, realPotential} = props,
          {children, parent} = term;

    let render_item = "",
        reset_icon = "",
        reset_item = "",
        info = "",
        semantic_class = "",
        state_class = "";
    const is_limb_or_and = term.isLimbOrAnd(),
          is_tagged = tagged[term.id],
          is_expanded = expanded[term.id],
          show_children = (!is_limb_or_and && is_tagged || is_expanded) && !term.is_leaf;

    if (term.isVisible()) {
      const rule = parent.semantic_rule || consts.SEMANTIC_RULE_AND,
            siblings = term.siblings;

      if (is_limb_or_and) {
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

      if (!is_limb_or_and && is_tagged || is_limb_or_and && is_expanded)
        state_class = 'ex-on';
      else
        state_class = 'ex-off';

      // Если из потомков можно выбрать лишь один элемент (radioButton), то остальные термины в этом дереве делаем неактивными
      if (rule != consts.SEMANTIC_RULE_AND
          && tagged[term.id] != true
          && (tagged.isAnyTagged(siblings)))
        state_class = 'ex-other';

      render_item = (
        <span className="ex-label" onClick={e => { ::this.handleItemClick(e) } } >
          <i className="ex-icon-slug"/>
          {term.name}
        </span>
      );

      if (term.semantic_rule == consts.SEMANTIC_RULE_XOR && show_children) {

        let any_tagged = tagged.isAnyTagged(children),
            reset_class = any_tagged ? "ex-xor ex-off" : "ex-xor ex-on";

        reset_item = (
          <li className={reset_class}>
              <span className="ex-label" onClick={e => { ::this.handleResetTermClick(e) } } >
                <i className="ex-icon-slug"/>
                { gettext("All") }
              </span>
          </li>
        );
      }

      if (children.length && !tagged.isAncestorTagged(term) && tagged.isAnyTagged(children)
        && term.structure === consts.STRUCTURE_LIMB) {
        reset_icon = (
          <i onClick={e => { ::this.handleResetBranchClick(e) } }
             className="ex-icon-reset"/>
        );
      }

      if (term.short_description) {
        info = (
          <TermsTreeItemInfo term={term}
                             infoExpanded={infoExpanded}
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
                     infoExpanded={infoExpanded}
                     realPotential={realPotential}
                     actions={actions}/>)
    );

    let li_classname = semantic_class + " " + state_class + " ";
    if (realPotential.has_metadata && !realPotential.rils[term.id]) {
      li_classname += !realPotential.pots[term.id] ? "ex-no-potential " : "ex-no-real "
    }

    let ret = <li className="ex-empty"/>;
    if (render_item == "") {
      ret = <li className="ex-empty"><ul>{render_children}</ul></li>;
    } else {
      if (show_children) {
        render_children = <ul>{reset_item}{render_children}</ul>;
      } else {
        render_children = "";
      }
      ret = (
        <li className={li_classname}
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
