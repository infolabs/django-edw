import React, {Component} from 'react';
import {ScrollView, View, SafeAreaView, StyleSheet, Platform} from 'react-native';
import {Layout, Avatar, Text} from "@ui-kitten/components";
import BaseDetail from "./BaseDetail";
import {dateFormat} from '../../utils/dateformat';
import platformSettings from '../../constants/Platform';


const {deviceHeight, deviceWidth} = platformSettings;
let personContainerHeight,
    personContainerPaddingBottom;

if (Platform.OS === 'android'){
  personContainerHeight = 90;
  personContainerPaddingBottom = 20;
} else {
  if (deviceHeight < 700) {
    personContainerHeight = 90;
    personContainerPaddingBottom = 20;
  } else {
    personContainerHeight = 140;
    personContainerPaddingBottom = 70;
  }
}

const styles = StyleSheet.create({
  safeAreaView: {
    height: deviceHeight,
    marginTop: 20,
  },
  scrollView: {
    marginBottom: 50
  },
  layout: {
    marginBottom: 40
  },
  personContainer: {
    width: deviceWidth,
    alignItems: 'center',
    justifyContent: 'flex-start',
    borderTopWidth: 1,
    borderColor: '#e3e3e3',
    paddingHorizontal: 16,
    flexDirection: 'row',
    backgroundColor: '#fff',
    height: personContainerHeight,
    paddingBottom: personContainerPaddingBottom,
    position: 'absolute',
    bottom: 0,
    shadowColor: '#636363',
    shadowOffset: {
      width: 0,
      height: 5,
    },
    shadowOpacity: 0.5,
    shadowRadius: 18.00,
    elevation: 24,
  },
  personView: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    marginRight: 16
  },
  personName: {
    fontWeight: 'bold'
  }
});

export default class Idea extends BaseDetail(Component) {

  render() {
    const {data} = this.props;

    return (
      <SafeAreaView style={styles.safeAreaView}>
        {this.getNavigation('Идея')}
        <ScrollView style={styles.scrollView}>
          <Layout level='1' style={styles.layout}>
            {this.getMedia()}
            {this.getContent()}
          </Layout>
        </ScrollView>
        {data.private_person ?
          <View style={styles.personContainer}>
            <View style={styles.personView}>
              <Avatar
                size="large"
                source={{uri: (data.private_person.media)}}
                style={styles.avatar}
              />
              <View>
                <Text style={styles.personName}>{data.private_person.entity_name}</Text>
                <Text>{dateFormat(data.created_at)}</Text>
              </View>
            </View>
          </View>
          : null
        }
      </SafeAreaView>
    )
  }
};
