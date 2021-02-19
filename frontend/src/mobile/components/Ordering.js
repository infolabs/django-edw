import React, {useState} from 'react'
import {View, StyleSheet} from 'react-native'
import {Button, Text, OverflowMenu, MenuItem} from "@ui-kitten/components"
import {Icon} from "native-base"
import ActionCreators from "../actions";
import {connect} from 'react-redux'
import {bindActionCreators} from "redux"
import Singleton from "../utils/singleton";


const Ordering = () => {
  const [visible, setVisible] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);

  const renderToggleButton = () => (
    <Button onPress={() => setVisible(true)} size='large' appearance='ghost' status='basic'>
      <View style={styles.sortView}>
        <Text style={styles.sortText}>test</Text>
        <Icon name='chevron-down-outline' style={styles.sortIcon}/>
      </View>
    </Button>
  );

  const onItemSelect = (index) => {
    const instance = Singleton.getInstance();
    if (instance && instance['private-person-initiatives']) {
      console.log(instance)
    }
    setSelectedIndex(index);
    setVisible(false);
  };

  return (
    <View>
      <OverflowMenu
        anchor={renderToggleButton}
        visible={visible}
        selectedIndex={selectedIndex}
        onSelect={onItemSelect}
        onBackdropPress={() => setVisible(false)}>
        <MenuItem title='Users'/>
        <MenuItem title='Orders'/>
        <MenuItem title='Transactions'/>
      </OverflowMenu>
    </View>
  )
};

const styles = StyleSheet.create({
  sortView: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sortText: {
    fontSize: 16,
    marginRight: 5
  },
  sortIcon: {
    fontSize: 18,
  }
});

const mapStateToProps = state => ({});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(Ordering);
