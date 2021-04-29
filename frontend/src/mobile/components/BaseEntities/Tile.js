import React, {Component} from 'react'
import {ScrollView, View, ImageBackground} from 'react-native'
import {Text, Card, Layout} from '@ui-kitten/components'
import Singleton from '../../utils/singleton'
import Spinner from 'react-native-loading-spinner-overlay';
import {tileStyles} from "../../styles/entities";


export default class Tile extends Component {
  render() {
    const {items, loading} = this.props;
    const instance = Singleton.getInstance();

    if (loading) {
      return (
        <View style={tileStyles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
      )
    } else {
      return (
        <ScrollView>
          <Layout style={tileStyles.layout}>
            {items.map(
              (child, i) => <TileItem key={i} data={child} domain={instance.Domain}/>
            )}
          </Layout>
        </ScrollView>
      );
    }
  }
}

class TileItem extends Component {
  render() {
    const {data, domain} = this.props;

    if (data.media.match(/.*<img.*?src=('|")(.*?)('|")/))
      data.media = `${domain}/${data.media.match(/.*<img.*?src=('|")(.*?)('|")/)[2]}`;

    return (
      <Card style={tileStyles.cardContainer}>
        <View style={tileStyles.cardImageContainer}>
          <ImageBackground source={{uri: data.media}} style={tileStyles.imageBackground}>
            <Text style={tileStyles.entityNameText}>
              {data.entity_name.length > 90 ?
                `${data.entity_name.slice(0, 90)}...`
                : data.entity_name
              }
            </Text>
          </ImageBackground>
        </View>
      </Card>
    )
  }
}
