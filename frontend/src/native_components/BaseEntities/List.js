import React from 'react';
import {ScrollView, View, ImageBackground} from 'react-native';
import {Text, Card, Layout} from '@ui-kitten/components';
import Singleton from '../../utils/singleton';
import Spinner from 'react-native-loading-spinner-overlay';
import {listStyles as styles} from '../../native_styles/entities';
import useEntities from './useEntities';


function List(props) {
  const [, handleScroll] = useEntities(props);
  const {items, loading, loadingEntity, templateIsDataMart, getEntity} = props;
  const instance = Singleton.getInstance();

  if (templateIsDataMart) {
    return (
      <ScrollView scrollEventThrottle={2000}
                  onScroll={e => handleScroll(e)}>
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


function ListItem(props) {
  const {data, domain, templateIsDataMart} = props;

  const style = templateIsDataMart ? {...styles.entityNameText} : {...styles.entityNameText, fontSize: 16};

  const mediaRe = /.*<img.*?src=(['"])(.*?)(['"])/;
  if (data.media.match(mediaRe))
    data.media = `${domain}/${data.media.match(mediaRe)[2]}`;

  return (
    <Card style={templateIsDataMart ? styles.cardContainer : styles.cardContainerRelated}
          onPress={() => templateIsDataMart ? props.getEntity(data) : {}}>
      <View style={templateIsDataMart ? styles.cardImageContainer : styles.cardImageRelated}>
        <ImageBackground source={{uri: data.media}} style={templateIsDataMart ? styles.imageBackground :
          styles.imageBackgroundRelated}>
          <Text style={style}>
            {data.entity_name}
          </Text>
        </ImageBackground>
      </View>
    </Card>
  );
}


export default List;
