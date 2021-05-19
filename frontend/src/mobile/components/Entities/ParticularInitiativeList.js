import React, {Component} from 'react'
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native'
import {Text, Card, Layout, List} from '@ui-kitten/components'
import {Badge} from 'native-base'
import Singleton from '../../utils/singleton'
import Spinner from 'react-native-loading-spinner-overlay';
import {listStyles} from "../../styles/entities";
import EntityMixin from "../BaseEntities/EntityMixin";


const stylesComponent = StyleSheet.create({
  badge: {
    position: 'absolute',
    bottom: 15,
    left: 15,
    zIndex: 4
  },
  badgeText: {
    color: '#fff'
  }
});

const styles = Object.assign(listStyles, stylesComponent);

export default class ParticularInitiativeList extends EntityMixin(Component) {

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
              (child, i) => <ParticularInitiativeListItem key={i} data={child} domain={instance.Domain}
                                                          getEntity={getEntity} templateIsDataMart={templateIsDataMart}/>
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
            <ParticularInitiativeListItem key={i} data={child.item} domain={instance.Domain} getEntity={getEntity}
                                          templateIsDataMart={templateIsDataMart}/>
          )}
        />
      </>
    );
  }
}

class ParticularInitiativeListItem extends Component {

  render() {
    const {data, domain, templateIsDataMart} = this.props,
      {short_marks} = data;

    if (data.media.match(/.*<img.*?src=(['"])(.*?)(['"])/))
      data.media = `${domain}/${data.media.match(/.*<img.*?src=(['"])(.*?)(['"])/)[2]}`;

    let textState = null,
      backgroundColorState = 'gray';

    short_marks.map(mark => {
      if (mark.name === "Состояние" || mark.name === "Системное состояние") {
        textState = mark.values[0];
        mark.view_class.map(item => {
          if (item.startsWith('pin-color-'))
            backgroundColorState = `#${item.replace('pin-color-', '')}`;
        })
      }
    });

    return (
      <Card style={templateIsDataMart ? styles.cardContainer : styles.cardContainerRelated}
            onPress={() => templateIsDataMart ? this.props.getEntity(data) : {}}>
        <View style={templateIsDataMart ? styles.cardImageContainer : styles.cardImageRelated}>
          <ImageBackground source={{uri: data.media}} style={templateIsDataMart ? styles.imageBackground :
            styles.imageBackgroundRelated}>
            <Text style={templateIsDataMart ? {...styles.entityNameText} : {...styles.entityNameText, fontSize: 16}}>
              {data.entity_name}
            </Text>
            {textState ?
              <Badge style={{...styles.badge, backgroundColor: backgroundColorState}}>
                <Text style={styles.badgeText}>{textState}</Text>
              </Badge>
              : null
            }
          </ImageBackground>
        </View>
      </Card>
    )
  }
}
