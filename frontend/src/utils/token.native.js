import AsyncStorage from '@react-native-async-storage/async-storage';
import {TOKEN} from '../constants/Common';


export const getToken = () => new Promise((resolve, reject) => {
  AsyncStorage.getItem(TOKEN).then((token) => {
    token == null ? reject(token) : resolve(token);
  });
});

export const removeToken = () => new Promise((resolve) => {
  AsyncStorage.setItem(TOKEN, '').then(() => resolve());
});

export const setToken = token => new Promise((resolve) => {
  AsyncStorage.setItem(TOKEN, token).then(() => resolve());
});
