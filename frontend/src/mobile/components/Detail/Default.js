import React, {Component} from 'react';
import {ScrollView} from 'react-native';
import {Layout} from "@ui-kitten/components";
import BaseDetail from "./BaseDetail";


export default class Default extends BaseDetail(Component) {

  render() {
    return (
      <>
        {this.getNavigation()}
        <ScrollView>
          <Layout level='1' style={{marginBottom: 50}}>
            {this.getMedia()}
            {this.getContent()}
          </Layout>
        </ScrollView>
      </>
    )
  }
};
