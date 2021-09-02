import {StyleService} from '@ui-kitten/components';


export const termsTreeItemStyles = StyleService.create({
  treeContainer: {
    marginLeft: 10,
  },
  termChildren: {
    marginLeft: 23,
    marginTop: 2,
    marginBottom: 4,
  },
  termView: {
    width: 250,
    marginVertical: 4,
  },
  termIsLimb: {
    fontSize: 16,
    display: 'flex',
    flexWrap: 'wrap',
    fontWeight: 'bold',
  },
  term: {
    fontSize: 14,
    display: 'flex',
    flexWrap: 'wrap',
  },
  iconReset: {
    top: 1,
    marginLeft: 6,
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2980b9',
  },
  termIsLimbOrAndView: {
    flexDirection: 'row',
    alignItems: 'center',
    width: 250,
  },
  termIsLimbOrAndIcon: {
    marginLeft: 3,
    marginRight: 7,
    fontSize: 22,
  },
  radioTouchableOpacity: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  radioView: {
    height: 20,
    width: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#828693',
    backgroundColor: '#f6f7f9',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  radioCheckedView: {
    height: 12,
    width: 12,
    borderRadius: 6,
    backgroundColor: 'color-primary-default',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'flex-start',
  },
});
