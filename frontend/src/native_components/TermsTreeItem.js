import React, {Component} from 'react';
import {View} from 'react-native';
import {Text, CheckBox, Radio} from '@ui-kitten/components';
import {Icon} from 'native-base';
import platformSettings from '../constants/Platform';
import {TouchableWithoutFeedback} from '@ui-kitten/components/devsupport';
import {structures, semanticRules} from '../constants/TermsTree';
import {termsTreeItemStyles as styles} from '../native_styles/terms';


export default class TermsTreeItem extends Component {

  handleItemPress() {
    const {term, actions} = this.props;
    actions.toggleTerm(term);
    this.resizeTermsContainer();
  }

  handleResetTermPress() {
    const {term, actions} = this.props;
    actions.resetTerm(term);
    this.resizeTermsContainer();
  }

  handleResetBranchPress() {
    const {term, actions} = this.props;
    actions.resetBranch(term);
    this.resizeTermsContainer();
  }

  // HACK: Для правильного определения высоты нужно переоткрыть ветку термина
  resizeTermsContainer() {
    const {actions, term} = this.props;
    let termParent = term;
    while (termParent.parent && termParent.parent.id !== null && termParent.structure !== structures.STRUCTURE_LIMB)
      termParent = termParent.parent;
    actions.toggleTerm(termParent);
    setTimeout(() => {
      actions.toggleTerm(termParent);
    }, 10);
  }

  render() {
    const {deviceWidth} = platformSettings;

    const {term, actions, tagged, expanded, realPotential, terms, termsIdsTaggedBranch} = this.props,
      {children, parent} = term;

    let ex_no_term = '';
    if (realPotential.has_metadata && !realPotential.rils[term.id])
      ex_no_term = !realPotential.pots[term.id] ? 'ex-no-potential ' : 'ex-no-real ';

    if (ex_no_term === 'ex-no-potential ' && term.name.length)
      return null;

    let render_item = '',
      reset_icon = '',
      reset_item = () => <></>,
      semantic_class = '',
      state_class = '';

    const is_limb_or_and = term.isLimbOrAnd(),
      is_tagged = tagged[term.id],
      is_expanded = expanded[term.id],
      show_children = (!is_limb_or_and && is_tagged || is_expanded) && !term.is_leaf;

    // Считаем количество выбранных веток
    if (terms.tagged.items.includes(term.id) && term.structure !== structures.STRUCTURE_LIMB &&
      term.structure !== structures.STRUCTURE_TRUNK) {
      let termParent = term;
      while (termParent.parent && termParent.parent.id !== null && termParent.structure !== structures.STRUCTURE_LIMB)
        termParent = termParent.parent;
      termsIdsTaggedBranch.add(termParent);
    }

    if (term.isVisible()) {
      const rule = parent.semantic_rule || semanticRules.SEMANTIC_RULE_AND,
        siblings = term.siblings;

      if (is_limb_or_and) {
        semantic_class = 'ex-and';
      } else {
        switch (rule) {
          case semanticRules.SEMANTIC_RULE_OR:
            semantic_class = 'ex-or';
            break;
          case semanticRules.SEMANTIC_RULE_XOR:
            semantic_class = 'ex-xor';
            break;
        }
      }

      let color = '#000';
      let fontWeight = 'normal';
      if (!is_limb_or_and && is_tagged || is_limb_or_and && is_expanded) {
        fontWeight = 'bold';
        state_class = 'ex-on';
      } else {
        state_class = 'ex-off';
      }

      // Если из потомков можно выбрать лишь один элемент (radioButton), то остальные термины в этом дереве делаем
      // неактивными
      if (rule !== semanticRules.SEMANTIC_RULE_AND && tagged[term.id] !== true && tagged.isAnyTagged(siblings) ||
        ex_no_term === 'ex-no-real ') {
        color = '#a9a9a9';
        state_class = 'ex-other';
      }

      let marginLeft = semantic_class === 'ex-and' ? 5 : -5;
      render_item = (
        <TouchableWithoutFeedback onPress={() => this.handleItemPress()}>
          {term.structure === structures.STRUCTURE_LIMB ?
            <Text style={styles.termIsLimb}>
              {term.name}
            </Text>
            :
            <Text style={{...styles.term, fontWeight, color, marginLeft}}>
              {term.name}
            </Text>
          }
        </TouchableWithoutFeedback>
      );

      if (term.semantic_rule === semanticRules.SEMANTIC_RULE_XOR && show_children) {
        const mrgnLeft = is_limb_or_and ? 25 : 0;
        const any_tagged = tagged.isAnyTagged(children);
        fontWeight = any_tagged ? 'normal' : 'bold';
        reset_item = () => (
          <Radio checked={!any_tagged}
                 onChange={() => this.handleResetTermPress()} style={{...styles.termIsAllRadio, mrgnLeft}}>
            <TouchableWithoutFeedback onPress={() => this.handleItemPress()}>
              <Text style={{...styles.termIsAllText, fontWeight, color}}>
                Всё
              </Text>
            </TouchableWithoutFeedback>
          </Radio>
        );
      }

      if (children.length && !tagged.isAncestorTagged(term) && tagged.isAnyTagged(children) &&
        term.structure === structures.STRUCTURE_LIMB) {
        reset_icon = (
          <TouchableWithoutFeedback onPress={() => this.handleResetBranchPress()}>
            <Icon style={styles.iconReset} name="md-close-circle"/>
          </TouchableWithoutFeedback>
        );
      }
    }

    let render_children = (children.map(child =>
        <TermsTreeItem key={child.id}
                       term={child}
                       tagged={tagged}
                       expanded={expanded}
                       realPotential={realPotential}
                       actions={actions}
                       terms={terms}
                       termsIdsTaggedBranch={termsIdsTaggedBranch}
        />)
    );

    let ret = null;

    if (render_item === '') {
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
      if (term.structure === structures.STRUCTURE_LIMB)
        marginLeft = 20;

      if (is_limb_or_and) {
        ret = (
          <>
            <TouchableWithoutFeedback onPress={() => this.handleItemPress()}
                                      style={{...styles.termIsLimbOrAndView, marginLeft}}>
              <Text>
                <Icon style={styles.termIsLimbOrAndIcon} name={iconName}/>
                {render_item}
                {reset_icon}
              </Text>
            </TouchableWithoutFeedback>
            <View style={{marginLeft}}>
              {render_children}
            </View>
          </>
        );
      } else {
        marginLeft = term.parent.isLimbOrAnd() ? 25 : 0;
        ret = (
          <View style={{...styles.termView, marginLeft}}>
            {semantic_class === 'ex-xor' ?
              <Radio checked={state_class === 'ex-on'}
                     style={styles.radio}
                     onChange={() => this.handleItemPress()}>
                {render_item}
                {render_children}
              </Radio>
              :
              <CheckBox checked={state_class === 'ex-on'}
                        style={styles.checkbox}
                        onChange={() => this.handleItemPress()}>
                {render_item}
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
