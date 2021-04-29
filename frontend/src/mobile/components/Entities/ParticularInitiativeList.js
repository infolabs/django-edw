import React, {Component} from 'react'
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native'
import {Text, Card, Layout} from '@ui-kitten/components'
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
    const {items, loading} = this.props;
    const instance = Singleton.getInstance();

    return (
      <ScrollView scrollEventThrottle={2000}
                  onScroll={e => this.handleScroll(e)}>
        {loading ?
          <View style={styles.spinnerContainer}>
            <Spinner visible={true}/>
          </View>
          : null
        }
        <Layout style={styles.layout}>
          {items.map(
            (child, i) => <ParticularInitiativeListItem key={i} data={child} domain={instance.Domain}/>
          )}
        </Layout>
      </ScrollView>
    );
  }
}

class ParticularInitiativeListItem extends Component {
  render() {
    const {data, domain} = this.props,
      {short_marks} = data;

    if (data.media.match(/.*<img.*?src=('|")(.*?)('|")/))
      data.media = `${domain}/${data.media.match(/.*<img.*?src=('|")(.*?)('|")/)[2]}`;

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
      <Card style={styles.cardContainer} onPress={() => console.log(data.id)}>
        <View style={styles.cardImageContainer}>
          <ImageBackground source={{uri: data.media}} style={styles.imageBackground}>
            <Text style={styles.entityNameText}>{data.entity_name}</Text>
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
