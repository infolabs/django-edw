import React, {useState} from 'react';
import {View} from 'react-native';
import {OverflowMenu, MenuItem, Text, Button, useTheme} from '@ui-kitten/components';
import {Icon} from 'native-base';
import ActionCreators from '../actions';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {dropDownsStyles as styles} from '../native_styles/dropdowns';


function Dropdown(props) {
  const {selected, options} = props;
  const [visible, setVisible] = useState(false);
  const theme = useTheme();

  function fixOffset(opts = {}) {
    const total = props.count,
      offset = opts.offset,
      limit = opts.limit;
    if (total && offset && limit && total < offset + limit)
      opts.offset = total - limit - total % limit;
    return opts;
  }

  function selectItem(value) {
    const {entry_point_id, subj_ids, name, request_var, request_options} = props;

    let option = {};
    option[request_var] = value;
    let opts = Object.assign(request_options, option);
    props.selectDropdown(name, value);
    props.notifyLoadingEntities();
    props.getEntities(entry_point_id, subj_ids, fixOffset(opts));
  }

  function handleOptionClick(value) {
    selectItem(value);
    setVisible(false);
  }

  function handleSelectedClick() {
    setVisible(false);
    const {name} = props;
    props.toggleDropdown(name);
  }

  let opts = {};
  for (const opt of Object.keys(options)) {
    if (options[opt] !== selected)
      opts[opt] = options[opt];
  }

  const renderToggleButton = () => (
    <Button onPress={() => setVisible(true)} style={styles.button} size="large" appearance="ghost" status="basic">
      <View style={styles.sortView}>
        <Text style={styles.sortText}>{selected}</Text>
        <Icon name="chevron-down-outline" style={{fontSize: theme['icon-size']}}/>
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
  );
}


const mapStateToProps = state => ({
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);


export default connect(mapStateToProps, mapDispatchToProps)(Dropdown);
