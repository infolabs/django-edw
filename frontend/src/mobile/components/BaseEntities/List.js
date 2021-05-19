import React, {Component} from 'react'
import {ScrollView, View, ImageBackground} from 'react-native'
import {Text, Card, Layout} from '@ui-kitten/components'
import Singleton from '../../utils/singleton'
import Spinner from 'react-native-loading-spinner-overlay';
import {listStyles as styles} from "../../styles/entities";
import EntityMixin from "./EntityMixin";


export default class List extends EntityMixin(Component) {

  render() {
    const {items, loading, loadingEntity, templateIsDataMart, getEntity} = this.props;
    const instance = Singleton.getInstance();

    if (templateIsDataMart) {
      return (
        <ScrollView scrollEventThrottle={2000}
                    onScroll={e => this.handleScroll(e)}>
          {loading || loadingEntity ?
            <View style={styles.spinnerContainer}>
              <Spinner visible={true}/>
            </View>
            : null
          }
          <Layout style={styles.layout}>
            {items.map(
              (child, i) => <ListItem key={i} data={child} domain={instance.Domain} getEntity={getEntity}
                                      templateIsDataMart={templateIsDataMart}/>
            )}
          </Layout>
        </ScrollView>
      );
    }

    // Related
    return (
      <>
        <List
          style={styles.containerRelated}
          contentContainerStyle={styles.containerContentRelated}
          horizontal={true}
          showsHorizontalScrollIndicator={false}
          data={items}
          renderItem={(child, i) => (
            <ListItem key={i} data={child.item} domain={instance.Domain} getEntity={getEntity}
                      templateIsDataMart={templateIsDataMart}/>
          )}
        />
      </>
    );
  }
}

class ListItem extends Component {

  render() {
    const {data, domain, templateIsDataMart} = this.props;

    if (data.media.match(/.*<img.*?src=(['"])(.*?)(['"])/))
      data.media = `${domain}/${data.media.match(/.*<img.*?src=(['"])(.*?)(['"])/)[2]}`;

    return (
      <Card style={templateIsDataMart ? styles.cardContainer : styles.cardContainerRelated}
            onPress={() => templateIsDataMart ? this.props.getEntity(data) : {}}>
        <View style={templateIsDataMart ? styles.cardImageContainer : styles.cardImageRelated}>
          <ImageBackground source={{uri: data.media}} style={templateIsDataMart ? styles.imageBackground :
            styles.imageBackgroundRelated}>
            <Text style={templateIsDataMart ? {...styles.entityNameText} : {...styles.entityNameText, fontSize: 16}}>
              {data.entity_name}
            </Text>
          </ImageBackground>
        </View>
      </Card>
    )
  }
}
