import React, {useState} from 'react';
import {View} from 'react-native';
import {OverflowMenu, MenuItem, Text, Button, useTheme} from '@ui-kitten/components'
import {Icon} from "native-base"
import ActionCreators from "../actions";
import {connect} from 'react-redux'
import {bindActionCreators} from "redux"
import {dropDownsStyles as styles} from "../native_styles/dropdowns";


const Dropdown = props => {
  const {selected, options, open} = props;
  const [visible, setVisible] = useState(false);
  const theme = useTheme();

  const fixOffset = (options = {}) => {
    const total = props.count,
      offset = options.offset,
      limit = options.limit;
    if (total && offset && limit && total < offset + limit)
      options.offset = total - limit - total % limit;
    return options;
  };

  const selectItem = value => {
    const {entry_point_id, subj_ids, name, request_var, request_options, entry_points} = props;

    let option = {};
    option[request_var] = value;
    let options = Object.assign(request_options, option);
    props.selectDropdown(name, value);
    props.notifyLoadingEntities();
    props.getEntities(entry_point_id, subj_ids, fixOffset(options));
  };

  const handleOptionClick = value => {
    const {entry_point_id, request_var} = props;
    selectItem(value);
    setVisible(false);
  };

  const handleSelectedClick = () => {
    setVisible(false);
    const {name} = props;
    props.toggleDropdown(name);
  };

  let opts = {};
  for (const opt of Object.keys(options)) {
    if (options[opt] !== selected)
      opts[opt] = options[opt];
  }

  const renderToggleButton = () => (
    <Button onPress={() => setVisible(true)} style={styles.button} size='large' appearance='ghost' status='basic'>
      <View style={styles.sortView}>
        <Text style={styles.sortText}>{selected}</Text>
        <Icon name='chevron-down-outline' style={{fontSize: theme['icon-size']}}/>
      </View>
    </Button>
  );

  return (
    <OverflowMenu
      anchor={renderToggleButton}
      visible={visible}
      onSelect={handleSelectedClick}
      onBackdropPress={() => setVisible(false)}>
      {Object.keys(opts).map((item, key) =>
        <MenuItem key={key} title={opts[item]} onPress={() => handleOptionClick(item)}/>
      )}
    </OverflowMenu>
  )
};

const mapStateToProps = state => ({
  entities: state.entities
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(Dropdown);
