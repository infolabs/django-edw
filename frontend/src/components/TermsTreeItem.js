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
        info = "";

    const show_children = !term.isLimbOrAnd() && tagged[term.id] || expanded[term.id];

    if (term.isVisible()) {

      const parent = term.parent,
            rule = parent.semantic_rule || consts.SEMANTIC_RULE_AND,
            siblings = term.siblings;

      let i_class_name = "";
      let span_class_name = "";
      let t_span_class_name = "";

      if (term.isLimbOrAnd()) {
        i_class_name = "ex-icon-caret";
        t_span_class_name = "ex-expandable";
      } else {
        switch (rule) {
          case consts.SEMANTIC_RULE_OR:
            i_class_name = "ex-icon-radio";
            break;
          case consts.SEMANTIC_RULE_XOR:
            i_class_name = "ex-icon-checkbox";
            break;
        }
      }

      if ((term.isLimbOrAnd() && expanded[term.id] == true) ||
          (!term.isLimbOrAnd() && tagged[term.id] == true)) {
        i_class_name += '-on';
        t_span_class_name == "" && (t_span_class_name = "ex-tagged");
      } else if (!term.isLimbOrAnd() && rule == consts.SEMANTIC_RULE_XOR
                 && !tagged.isAnyTagged(siblings)) {
        i_class_name += '-dot';
      } else {
        i_class_name += '-off';
      }

      if (rule != consts.SEMANTIC_RULE_AND
          && tagged[term.id] != true
          && tagged.isAnyTagged(siblings))
        span_class_name = 'ex-dim';

      render_item = (
        <span onClick={e => { ::this.handleItemClick(e) } }
              className={span_class_name}>
          <i className={i_class_name}></i>
          <span className={t_span_class_name}>{term.name}</span>
        </span>
      );

      if (term.semantic_rule == consts.SEMANTIC_RULE_OR && show_children) {
        let any_tagged = tagged.isAnyTagged(children),
            r_span_class_name = any_tagged ? "ex-dim" : "",
            r_t_span_class_name = any_tagged ? "" : "ex-tagged",
            r_i_class_name = any_tagged ? "ex-icon-radio-off" : "ex-icon-radio-on";

        reset_item = (
          <li>
            <span onClick={e => { ::this.handleResetClick(e) } }
                  className={r_span_class_name}>
              <i className={r_i_class_name}></i>
              <span className={r_t_span_class_name}>{ gettext("All") }</span>
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

    let li_clasname = "";
    if (real_potential.has_metadata && !real_potential.rils[term.id]) {
      li_clasname = !real_potential.pots[term.id] ? "ex-no-potential" : "ex-no-real"
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
        <li className={li_clasname}>
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

