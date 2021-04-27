import React, {Component} from 'react';
import {View} from 'react-native';
import {Text, CheckBox, Radio} from "@ui-kitten/components";
import {Icon} from "native-base";
import platformSettings from "../constants/Platform";
import {TouchableWithoutFeedback} from "@ui-kitten/components/devsupport";
import * as consts from "../constants/TermsTree";


export default class TermsTreeItem extends Component {

  handleItemPress() {
    const {term, actions} = this.props;
    actions.toggle(term);
    this.resizeTermsContainer ();
  }

  handleResetItemPress() {
    const {term, actions} = this.props;
    actions.resetItem(term);
    this.resizeTermsContainer ();
  }

  handleResetBranchPress() {
    const {term, actions} = this.props;
    actions.resetBranch(term);
    this.resizeTermsContainer ();
  }

  // HACK: Для правильного определения высоты нужно переоткрыть ветку термина
  resizeTermsContainer () {
    const {actions, term} = this.props;
    let termParent = term;
    while (termParent.parent && termParent.parent.id !== null && termParent.structure !== consts.STRUCTURE_LIMB){
      termParent = termParent.parent
    }
    actions.toggle(termParent);
    setTimeout(() => {
      actions.toggle(termParent);
    },10);
  }

  render() {
    const {deviceHeight, deviceWidth} = platformSettings;

    const {term, details, actions, tagged, expanded, info_expanded, realPotential} = this.props,
      {children, parent} = term;

    let render_item = "",
      reset_icon = "",
      reset_item = () => <></>,
      info = "",
      semantic_class = "",
      state_class = "";

    const is_limb_or_and = term.isLimbOrAnd(),
      is_tagged = tagged[term.id],
      is_expanded = expanded[term.id],
      show_children = (!is_limb_or_and && is_tagged || is_expanded) && !term.is_leaf;

    let ex_no_term = '';
    if (realPotential.has_metadata && !realPotential.rils[term.id])
      ex_no_term = !realPotential.pots[term.id] ? "ex-no-potential " : "ex-no-real ";

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

      let color = "#000";
      let fontWeight = 'normal';
      if (!is_limb_or_and && is_tagged || is_limb_or_and && is_expanded){
        fontWeight = 'bold';
        state_class = 'ex-on';
      } else
        state_class = 'ex-off';

      // Если из потомков можно выбрать лишь один элемент (radioButton), то остальные термины в этом дереве делаем неактивными
      if (rule !== consts.SEMANTIC_RULE_AND && tagged[term.id] !== true && tagged.isAnyTagged(siblings)) {
        color = "#a9a9a9";
        state_class = 'ex-other';
      }

      let marginLeft = semantic_class === 'ex-and' ? 5 : 0;
      render_item = (
        <TouchableWithoutFeedback  onPress={() => this.handleItemPress()}>
          {term.structure === consts.STRUCTURE_LIMB ?
            <Text style={{fontSize: 16, marginTop: 3, display: 'flex', flexWrap: 'wrap', paddingLeft: 5, fontWeight: 'bold'}}>
              {term.name}
            </Text>
            :
            <Text style={{fontSize: 16, marginTop: 3, display: 'flex', flexWrap: 'wrap', fontWeight, color, marginLeft}}>
              {term.name}
            </Text>
          }
        </TouchableWithoutFeedback>
      );

      if (term.semantic_rule === consts.SEMANTIC_RULE_XOR && show_children) {
        const marginLeft = term.isLimbOrAnd() ? 25 : 0;
        const any_tagged = tagged.isAnyTagged(children);
        fontWeight = any_tagged ? 'normal' : 'bold';
        reset_item = () => (
          <TouchableWithoutFeedback onPress={() => this.handleResetItemPress()}>
              <Radio checked={!any_tagged}
                     onChange={() => this.handleResetItemPress()} style={{marginTop: 10, marginBottom: 5, marginLeft}}>
                <Text style={{fontSize: 16, fontWeight}}>Всё</Text>
              </Radio>
          </TouchableWithoutFeedback>
        );
      }

      if (children.length && !tagged.isAncestorTagged(term) && tagged.isAnyTagged(children) && term.structure === consts.STRUCTURE_LIMB) {
        reset_icon = (
          <TouchableWithoutFeedback onPress={() => this.handleResetBranchPress()}>
            <Icon style={{fontSize: 18, fontWeight: 'bold', marginLeft: 5, color: '#2980b9'}} name='md-close-circle'/>
          </TouchableWithoutFeedback>
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
                       realPotential={realPotential}
                       actions={actions}/>)
    );

    let liClassName = semantic_class + " " + state_class + " ";
    liClassName += ex_no_term;

    let ret = null;

    if (render_item === "") {
      ret = <View>{render_children}</View>;
    } else {
      let iconName = '';
      if (show_children) {
        iconName = 'caret-down';
        render_children = (
          <View style={{width: deviceWidth}}>
            {reset_item()}
            {render_children}
          </View>
        );
      } else {
        iconName = 'caret-forward';
        render_children = null;
      }

      let marginLeft = 0;
      if (term.structure === consts.STRUCTURE_LIMB)
        marginLeft = 20;

      if (is_limb_or_and) {
        ret = (
          <TouchableWithoutFeedback onPress={() => this.handleItemPress()}
                                    style={{flexDirection: 'column', marginTop: 10, marginLeft, width: 250}}>
            <Text>
              <Icon style={{fontSize: 20, marginRight: 20}} name={iconName}/>
              {render_item}
              {info}
              {reset_icon}
              {render_children}
            </Text>
          </TouchableWithoutFeedback>
        );
      } else {
        const regexVisibleTerm = /(ex-no-potential)/;
        const isMatchVisibleTerm = liClassName.match(regexVisibleTerm);
        marginLeft = term.parent.isLimbOrAnd() ? 25 : 0;
        ret = (
          <View style={isMatchVisibleTerm !== null ? {display: 'none'} : {marginTop: 2, width: 250, marginLeft}}>
            {semantic_class === 'ex-xor' ?
              <Radio checked={state_class === 'ex-on'} style={{display: 'flex', alignItems: 'flex-start', marginTop: 2}}
                     onChange={() => this.handleItemPress()}>
                {render_item}
                {info}
                {render_children}
              </Radio>
              :
              <CheckBox checked={state_class === 'ex-on'} style={{display: 'flex', alignItems: 'flex-start', marginTop: 7}}
                        onChange={() => this.handleItemPress()}>
                {render_item}
                {info}
                {reset_icon}
                {render_children}
              </CheckBox>
            }
          </View>
        );
      }
    }
    return ret;
  }
}
