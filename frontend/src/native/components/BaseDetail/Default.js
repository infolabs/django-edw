import React from 'react';
import {ScrollView} from 'react-native';
import {Layout} from '@ui-kitten/components';
import useDetail from './useDetail';


function Default(props) {

  const { getNavigation, getMedia, getContent } = useDetail(props);

  const style = {marginBottom: 50};

  return (
    <>
      {getNavigation()}
      <ScrollView>
        <Layout level="1" style={style}>
          {getMedia()}
          {getContent()}
        </Layout>
      </ScrollView>
    </>
  );
}


export default Default;
