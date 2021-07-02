import {StyleSheet} from 'react-native';


export const termsTreeItemStyles = StyleSheet.create({
  termIsLimb: {
    fontSize: 16,
    marginTop: 3,
    display: 'flex',
    flexWrap: 'wrap',
    paddingLeft: 5,
    fontWeight: 'bold',
  },
  term: {
    fontSize: 16,
    marginTop: 3,
    display: 'flex',
    flexWrap: 'wrap',
  },
  termIsAllRadio: {
    marginTop: 10,
  },
  termIsAllText: {
    fontSize: 16,
    marginTop: 5,
    display: 'flex',
    flexWrap: 'wrap',
    marginLeft: -5,
  },
  iconReset: {
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 5,
    color: '#2980b9',
  },
  termIsLimbOrAndView: {
    flexDirection: 'column',
    marginTop: 10,
    width: 250,
  },
  termIsLimbOrAndIcon: {
    fontSize: 22,
    marginRight: 20,
  },
  termView: {
    marginTop: 2,
    width: 250,
  },
  radio: {
    display: 'flex',
    alignItems: 'flex-start',
    marginTop: 2,
  },
  checkbox: {
    display: 'flex',
    alignItems: 'flex-start',
    marginTop: 7,
  },
});
