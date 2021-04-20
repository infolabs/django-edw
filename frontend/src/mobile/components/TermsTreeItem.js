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
  }

  handleResetItemPress() {
    const {term, actions} = this.props;
    actions.resetItem(term);
  }

  handleResetBranchPress() {
    const {term, actions} = this.props;
    actions.resetBranch(term);
  }

  render() {
    const {deviceHeight, deviceWidth} = platformSettings;

    const {term, details, actions, tagged, expanded, info_expanded, real_potential} = this.props,
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
    if (real_potential.has_metadata && !real_potential.rils[term.id])
      ex_no_term = !real_potential.pots[term.id] ? "ex-no-potential " : "ex-no-real ";

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
      if (rule !== consts.SEMANTIC_RULE_AND
        && tagged[term.id] !== true
        && (tagged.isAnyTagged(siblings)))
        state_class = 'ex-other';

      render_item = (
        <TouchableWithoutFeedback  onPress={() => this.handleItemPress()}>
          <Text style={{fontSize: 16, marginTop: 3, display: 'flex', flexWrap: 'wrap'}}>
            {term.name}
          </Text>
        </TouchableWithoutFeedback>
      );

      if (term.semantic_rule === consts.SEMANTIC_RULE_XOR && show_children) {
        let any_tagged = tagged.isAnyTagged(children);

        reset_item = () => (
          <TouchableWithoutFeedback onPress={() => this.handleResetItemPress()}>
            <View style={{marginLeft: 10, marginTop: 15, marginBottom: 5}}>
              <Radio checked={!any_tagged}
                     onChange={() => this.handleResetItemPress()}>
                <Text style={{fontSize: 16}}>Всё</Text>
              </Radio>
            </View>
          </TouchableWithoutFeedback>
        );
      }

      if (children.length && !tagged.isAncestorTagged(term) &&
        tagged.isAnyTagged(children)) {
        reset_icon = (
          <Text className="ex-icon-reset"/>
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
    );

    let liClassName = semantic_class + " " + state_class + " ";
    liClassName += ex_no_term;

    let ret = null;

    if (render_item === "") {
      ret = <View>{render_children}</View>;
    } else {
      let iconName = '';
      if (show_children) {
        iconName = 'ios-chevron-down';
        render_children = (
          <View style={{width: deviceWidth}}>
            {reset_item()}
            {render_children}
          </View>
        );
      } else {
        iconName = 'ios-chevron-forward';
        render_children = null;
      }

      if (term.structure === 'limb') {
        ret = (
          <View style={{flexDirection: 'column', marginTop: 10, marginLeft: 5, paddingRight: 15, width: 250}}>
            <Text>
              <Icon style={{fontSize: 20}} name={iconName}/>
              {render_item}
              {info}
              {reset_icon}
              {render_children}
            </Text>
          </View>
        );
      } else {
        const regexVisibleTerm = /(ex-no-potential)/;
        const isMatchVisibleTerm = liClassName.match(regexVisibleTerm);
        ret = (
          <View style={isMatchVisibleTerm !== null ? {display: 'none'} : {marginLeft: 10, marginTop: 2, width: 250}}>
            {semantic_class === 'ex-xor' ?
              <Radio checked={state_class === 'ex-on'} style={{display: 'flex', alignItems: 'flex-start', marginTop: 2}}
                     onChange={() => this.handleItemPress()}>
                {render_item}
                {info}
                {reset_icon}
                {render_children}
              </Radio>
              :
              <CheckBox checked={state_class === 'ex-on'} style={{display: 'flex', alignItems: 'flex-start', marginTop: 5}}
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
