import {StyleSheet, Platform} from 'react-native';
import platformSettings from '../constants/Platform';


const {deviceHeight, deviceWidth} = platformSettings;
let showObjectsBtnViewHeight,
  showObjectsBtnViewHeightBottom,
  termsScrollViewContainerMarginBottom;

if (Platform.OS === 'android') {
  showObjectsBtnViewHeight = 145;
  showObjectsBtnViewHeightBottom = 0;
  termsScrollViewContainerMarginBottom = showObjectsBtnViewHeight + 70;
} else {
  if (deviceHeight < 700) {
    showObjectsBtnViewHeightBottom = 40;
    showObjectsBtnViewHeight = 105;
    termsScrollViewContainerMarginBottom = showObjectsBtnViewHeight * 2;
  } else {
    showObjectsBtnViewHeightBottom = 10;
    showObjectsBtnViewHeight = 150;
    termsScrollViewContainerMarginBottom = showObjectsBtnViewHeight + 50;
  }
}

export const dataMartStyles = StyleSheet.create({
  headerBtnView: {
    width: deviceWidth,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 15,
  },
  headerBtn: {
    height: 50,
  },
  orderingView: {
    width: '50%',
    marginRight: '20%',
  },
  textDelimiter: {
    width: 1,
    height: 18,
    backgroundColor: '#b4b4b4',
  },
  viewAndFilteredIcon: {
    width: 100,
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  termTreeAnimatedView: {
    height: deviceHeight,
    width: deviceWidth,
    position: 'absolute',
    backgroundColor: '#fff',
    bottom: 0,
    zIndex: 4,
  },
  termsTreeView: {
    height: '100%',
  },
  navigationTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    paddingHorizontal: 40,
    textAlign: 'center',
  },
  emptyContainerEntities: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10,
  },
  emptyContainerEntitiesText: {
    fontSize: 18,
  },
  showObjectsBtnView: {
    position: 'absolute',
    bottom: showObjectsBtnViewHeightBottom,
    width: deviceWidth,
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    borderTopWidth: 1,
    borderTopLeftRadius: 15,
    borderTopEndRadius: 15,
    borderColor: '#d5d5d5',
    backgroundColor: '#fff',
    height: showObjectsBtnViewHeight,
  },
  showObjectsBtn: {
    borderWidth: 0,
    marginHorizontal: 25,
    marginTop: 15,
    borderRadius: 10,
  },
  termsScrollViewContainer: {
    marginBottom: termsScrollViewContainerMarginBottom,
  },
});
