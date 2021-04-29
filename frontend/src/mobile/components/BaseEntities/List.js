import React, {Component} from 'react'
import {ScrollView, View, ImageBackground} from 'react-native'
import {Text, Card, Layout} from '@ui-kitten/components'
import Singleton from '../../utils/singleton'
import Spinner from 'react-native-loading-spinner-overlay';
import {listStyles} from "../../styles/entities";


export default class List extends Component {
  render() {
    const {items, loading} = this.props;
    const instance = Singleton.getInstance();

    if (loading) {
      return (
        <View style={listStyles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
      )
    } else {
      return (
        <ScrollView>
          <Layout style={listStyles.layout}>
            {items.map(
              (child, i) => <ListItem key={i} data={child} domain={instance.Domain}/>
            )}
          </Layout>
        </ScrollView>
      );
    }
  }
}

class ListItem extends Component {
  render() {
    const {data, domain} = this.props;

    if (data.media.match(/.*<img.*?src=('|")(.*?)('|")/))
      data.media = `${domain}/${data.media.match(/.*<img.*?src=('|")(.*?)('|")/)[2]}`;

    return (
      <Card style={listStyles.cardContainer}>
        <View style={listStyles.cardImageContainer}>
          <ImageBackground source={{uri: data.media}} style={listStyles.imageBackground}>
            <Text style={listStyles.entityNameText}>{data.entity_name}</Text>
          </ImageBackground>
        </View>
      </Card>
    )
  }
}
