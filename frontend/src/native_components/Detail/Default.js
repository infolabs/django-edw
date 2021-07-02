import React, {Component} from 'react';
import {ScrollView} from 'react-native';
import {Layout} from '@ui-kitten/components';
import BaseDetail from './BaseDetail';


export default class Default extends BaseDetail(Component) {

  render() {
    const style = {marginBottom: 50};

    return (
      <>
        {this.getNavigation()}
        <ScrollView>
          <Layout level="1" style={style}>
            {this.getMedia()}
            {this.getContent()}
          </Layout>
        </ScrollView>
      </>
    );
  }
}
