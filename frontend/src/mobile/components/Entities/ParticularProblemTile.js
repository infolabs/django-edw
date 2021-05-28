import React from 'react';
import {ScrollView, View, ImageBackground, StyleSheet} from 'react-native';
import {Text, Card, Layout} from '@ui-kitten/components';
import {Badge} from 'native-base';
import Singleton from '../../utils/singleton';
import Spinner from 'react-native-loading-spinner-overlay';
import {tileStyles} from '../../styles/entities';
import useEntities from '../BaseEntities/useEntities';


const stylesComponent = StyleSheet.create({
  badge: {
    position: 'absolute',
    bottom: 15,
    left: 15,
    zIndex: 4,
  },
  badgeText: {
    color: '#fff',
  },
});


const styles = Object.assign(tileStyles, stylesComponent);


function ParticularProblemTile(props) {

  const [maxLengthDescriptionTile, handleScroll] = useEntities(props);
  const {items, loading, loadingEntity, getEntity} = props;
  const instance = Singleton.getInstance();

  return (
    <ScrollView scrollEventThrottle={2000}
                onScroll={handleScroll}>
      {loading || loadingEntity ?
        <View style={styles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
        : null
      }
      <Layout style={styles.layout}>
        {items.map(
          (child, i) => <ParticularProblemTileItem key={i}
                          data={child} domain={instance.Domain} getEntity={getEntity}
                          maxLengthDescriptionTile={maxLengthDescriptionTile}/>
        )}
      </Layout>
    </ScrollView>
  );
}


function ParticularProblemTileItem(props) {
  const {data, domain, maxLengthDescriptionTile} = props,
    {short_marks} = data;

  if (data.media.match(/.*<img.*?src=(['"])(.*?)(['"])/))
    data.media = `${domain}/${data.media.match(/.*<img.*?src=(['"])(.*?)(['"])/)[2]}`;

  let textState = null,
    backgroundColorState = 'gray';

  short_marks.map(mark => {
    if (mark.name === 'Состояние' || mark.name === 'Системное состояние') {
      textState = mark.values[0];
      mark.view_class.map(item => {
        if (item.startsWith('pin-color-'))
          backgroundColorState = `#${item.replace('pin-color-', '')}`;
      });
    }
  });

  return (
    <Card style={styles.cardContainer} onPress={() => props.getEntity(data)}>
      <View style={styles.cardImageContainer}>
        <ImageBackground source={{uri: data.media}} style={styles.imageBackground}>
          <Text style={styles.entityNameText}>
            {data.entity_name.length > maxLengthDescriptionTile ?
              `${data.entity_name.slice(0, maxLengthDescriptionTile)}...`
              : data.entity_name
            }
          </Text>
          {textState ?
            <Badge style={{...styles.badge, backgroundColor: backgroundColorState}}>
              <Text style={styles.badgeText}>
                {textState.length > 12 ?
                  `${textState.slice(0, 12)}...`
                  : textState
                }
              </Text>
            </Badge>
            : null
          }
        </ImageBackground>
      </View>
    </Card>
  );
}


export default ParticularProblemTile;
