import React from 'react';
import {View} from 'react-native';
import {Text, CheckBox, Radio} from '@ui-kitten/components';
import {Icon} from 'native-base';
import platformSettings from '../constants/Platform';
import {structures, semanticRules} from '../constants/TermsTree';
import {termsTreeItemStyles as styles} from '../native_styles/terms';


function TermsTreeItem(props) {

  function handleItemPress() {
    const {term, actions} = props;
    actions.toggleTerm(term);
  }

  function handleResetTermPress() {
    const {term, actions} = props;
    actions.resetTerm(term);
  }

  function handleResetBranchPress() {
    const {term, actions} = props;
    actions.resetBranch(term);
  }

  const {deviceWidth} = platformSettings;

  const {term, actions, tagged, expanded, realPotential, terms, termsIdsTaggedBranch} = props,
    {children, parent} = term;

  let ex_no_term = '';
  if (realPotential.has_metadata && !realPotential.rils[term.id])
    ex_no_term = !realPotential.pots[term.id] ? 'ex-no-potential ' : 'ex-no-real ';

  if (ex_no_term === 'ex-no-potential ' && term.name.length)
    return null;

  let reset_item = null,
    render_item = '',
    reset_icon = null,
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

    render_item = term.structure === structures.STRUCTURE_LIMB ?
      <Text style={styles.termIsLimb}
            onPress={() => handleItemPress()}>
        {term.name}
      </Text>
      :
      <Text style={{...styles.term, fontWeight, color}}
            onPress={() => handleItemPress()}>
        {term.name}
      </Text>;

    if (term.semantic_rule === semanticRules.SEMANTIC_RULE_XOR && show_children) {
      const any_tagged = tagged.isAnyTagged(children);
      fontWeight = any_tagged ? 'normal' : 'bold';
      const key = `reset_item_${term.id}`;
      reset_item = <View style={styles.termView} key={key}>
          <Radio checked={!any_tagged}
                 onChange={() => handleResetTermPress()}
                 style={{...styles.radio}}>
            <Text style={{...styles.term, fontWeight, color}}
                  onPress={() => handleItemPress()}>
              Всё
            </Text>
          </Radio>
        </View>;
    }

    if (children.length && !tagged.isAncestorTagged(term) && tagged.isAnyTagged(children) &&
      term.structure === structures.STRUCTURE_LIMB) {
      reset_icon = (
          <Icon style={styles.iconReset} name="md-close-circle"
                onPress={() => handleResetBranchPress()} />
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

  if (reset_item)
    render_children.unshift(reset_item);

  let ret = null;

  if (render_item === '') {
    ret = <View>{render_children}</View>;
  } else {
    let iconName = '';
    if (show_children) {
      iconName = 'caret-down';
      render_children = (
        <View style={{...styles.termChildren, width: deviceWidth}}>
          {render_children}
        </View>
      );
    } else {
      iconName = 'caret-forward';
      render_children = null;
    }

    if (is_limb_or_and) {
      ret = (
        <View style={styles.termView}>
          <View style={{...styles.termIsLimbOrAndView}}>
            <Icon style={styles.termIsLimbOrAndIcon} name={iconName}
                  onPress={() => handleItemPress()}/>
            <Text onPress={() => handleItemPress()}>{render_item}</Text>
            {reset_icon}
          </View>
          {render_children}
        </View>
      );
    } else {
      ret = (
        <View style={styles.termView}>
          {semantic_class === 'ex-xor' ?
            <Radio checked={state_class === 'ex-on'}
                   style={styles.radio}
                   onChange={() => handleItemPress()}>
              {render_item}
            </Radio>
            :
            <CheckBox checked={state_class === 'ex-on'}
                      style={styles.checkbox}
                      onChange={() => handleItemPress()}>
              {render_item}
              {reset_icon}
            </CheckBox>
          }
          {render_children}
        </View>
      );
    }
  }
  return ret;
}


export default TermsTreeItem;
