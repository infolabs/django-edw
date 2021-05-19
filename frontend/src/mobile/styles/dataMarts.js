import {StyleSheet} from 'react-native';
import platformSettings from "../constants/Platform";


const {deviceHeight, deviceWidth} = platformSettings;

export const dataMartStyles = StyleSheet.create({
  headerBtnView: {
    width: deviceWidth,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 15,
  },
  headerBtn: {
    height: 50
  },
  orderingView: {
    width: '50%',
    marginRight: '20%',
  },
  textDelimiter: {
    width: 1,
    height: 18,
    backgroundColor: '#b4b4b4'
  },
  viewAndFilteredIcon: {
    width: 100,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center'
  },
  termTreeAnimatedView: {
    height: deviceHeight,
    width: deviceWidth,
    position: 'absolute',
    backgroundColor: '#fff',
    bottom: 0,
    zIndex: 4
  },
  termsTreeView: {
    height: '100%',
  },
  navigationTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    paddingHorizontal: 40,
    textAlign: 'center'
  },
  emptyContainerEntities: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10
  },
  emptyContainerEntitiesText: {
    fontSize: 18
  },
  showObjectsBtnView: {
    position: 'absolute',
    bottom: 0,
    height: 120,
    width: deviceWidth,
    shadowOffset: {
      width: 0,
      height: 2
    },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    borderTopWidth: 1,
    borderRadius: 15,
    borderColor: '#d5d5d5',
    backgroundColor: "#fff"
  },
  showObjectsBtn: {
    borderWidth: 0,
    marginHorizontal: 25,
    marginTop: 10,
    borderRadius: 10
  },
  emptyView: {
    height: 200
  },
  swipeWrapper: {
    height: 300,
  },
  slide: {
    height: 300,
  },
  imageSlide: {
    height: 300,
    resizeMode: 'cover',
  },
  infoEntity: {
    paddingHorizontal: 24,
    marginTop: 8,
    marginVertical: 16,
  },
});
