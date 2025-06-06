import {Platform} from 'react-native';
import matchAll from 'string.prototype.matchall';
import reCache from '../utils/reCache';
import uniFetch from '../utils/uniFetch';
import {actionTypes} from '../constants/Entity';
import Singleton from '../utils/singleton';
import {getToken} from '../utils/token';


export const setDataEntity = (id, data, textLoader = null, nameFields = {}) => dispatch => {
  const instance = Singleton.getInstance(),
    {Urls, navigation, Domain} = instance;

  getToken().then(token => {
    const url = reCache(`${Domain}${Urls['edw:entity-detail'](id)}`),
      parameters = {
        method: 'PATCH',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify(data),
      };

    textLoader && navigation.navigate({name: 'Preloader', props: {textLoader}, merge: true});

    uniFetch(url, parameters, nameFields)
      .then(() => {
        dispatch({type: actionTypes.SET_DATA_ENTITY});
      })
      .catch((error) => {
        dispatch({type: actionTypes.ERROR_SET_DATA_ENTITY});
      });
  });
};

export const createEntity = params => dispatch => {
  const {
    data,
    url,
    actionType,
    refreshDataMart,
    textLoader = null,
    nameFields = {},
    slugConfig = null,
    nextScreen = {name: 'Home'},
  } = params;

  const instance = Singleton.getInstance(),
    {navigation} = instance;

  getToken().then(token => {
    const parameters = {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`,
      },
      credentials: 'include',
      body: JSON.stringify(data),
    };

    textLoader && navigation.navigate({name: 'Preloader', props: {textLoader}, merge: true});

    uniFetch(url, parameters, nameFields)
      .then(() => {
        navigation.navigate(nextScreen.name, nextScreen.params);
        dispatch({type: actionType});
        slugConfig && refreshDataMart(slugConfig);
      })
      .catch(() => {
        textLoader && navigation.goBack();
        dispatch({type: actionTypes.ERROR_CREATE_ENTITY});
      });
  });
};


export const getEntity = (id, dispatchType = actionTypes.GET_ENTITY, extraQuery = '') => dispatch => {
  getToken().then((token) => {
    const instance = Singleton.getInstance(),
          {Urls, Domain, navigation} = instance;

    const url = reCache(`${Domain}${Urls['edw:entity-detail'](id,'json')}`),
          parameters = {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
              'Authorization': `Token ${token}`,
            },
          };

    uniFetch(url + extraQuery, parameters)
      .then(response => response.json()).then(json => {
        // TODO: MatchAll в react-native v0.64.2 для андроида не поддерживается. Возможно, пофиксят в будущем, и тогда
        // нужно будет убрать проверку и удалить пакет string.prototype.matchall.
        // нужно ли это делать в edw или перенести в мобильное приложение, тк явно используется json объект osk?
        const arrayMediaEntity = media => Platform.OS === 'ios' ?
            Array.from(media.matchAll(/(?:href=['"])(\/media\S+.[jpg|jpeg|png|pdf|docx|xlsx])['"]/gm))
            :
            [...matchAll(media, /(?:href=['"])(\/media\S+.[jpg|jpeg|png|pdf|docx|xlsx])['"]/gm)];

        const arrayMediaPerson = media => Platform.OS === 'ios' ?
            Array.from(media.matchAll(/(?:src=['"])(\/media\S+.[jpg|jpeg|png])['"]/gm))
            :
            [...matchAll(media, /(?:src=['"])(\/media\S+.[jpg|jpeg|png])['"]/gm)];

        json.media = arrayMediaEntity(json.media).map(item => `${Domain}${item[1]}`);

        if (json.private_person)
          json.private_person.media = arrayMediaPerson(json.private_person.media).map(item => `${Domain}${item[1]}`);

        if (json.messages)
          json.messages.reverse();

        json.description = json.description ? json.description.replace(/<\/p>/gi, '. ').replace(/<.*?>/gi, '') : '';
        if (json.solution)
          json.solution = json.solution.replace(/<\/p>/gi, '. ').replace(/<.*?>/gi, '');
        if (json.result)
          json.result = json.result.replace(/<\/p>/gi, '. ').replace(/<.*?>/gi, '');
        dispatch({type: dispatchType, data: json});
      })
      .catch(error => {
        //console.error(error);
        dispatch({type: actionTypes.ERROR_GET_ENTITY, error});
        navigation?.navigate({name: 'Home', params: {}, merge: true});
      });
  }).catch(error => {
    //console.error(error);
  });
};

export const deleteEntity = params => dispatch => {
  const {id, nextNavigate, refreshDataMart} = params,
    textLoader = params.textLoader || null,
    slugConfig = params.slugConfig || null,
    instance = Singleton.getInstance(),
    {Urls, Domain, navigation} = instance;

    getToken().then(token => {
      const url = `${Domain}${Urls['edw:entity-detail'](id)}`,
        parameters = {
          method: 'DELETE',
          headers: {
            Authorization: `Token ${token}`,
          },
        };

      navigation.navigate({name: 'Preloader', props: {textLoader}, merge: true});

      uniFetch(url, parameters, {}, false)
        .then(() => {
          navigation.navigate({name: nextNavigate, props: {}, merge: true});
          dispatch({type: actionTypes.DELETE_ENTITY, id});
          slugConfig && refreshDataMart(slugConfig);
        })
        .catch(error => {
          navigation.goBack()
          dispatch({type: actionTypes.ERROR_DELETE_ENTITY, error});
        });
    })
}

export const uploadImage = (entityId, data, nextNavigationName, dispatchType = actionTypes.UPLOAD_IMAGE) => dispatch => {
  const instance = Singleton.getInstance(),
    {Urls, Domain, navigation} = instance;

  getToken().then(token => {
    const url = `${Domain}${Urls['edw:entity-image-list'](entityId)}`,
      parameters = {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
        },
        body: data,
      };
    uniFetch(url, parameters)
      .then(response => response.json()).then(json => {
        dispatch({type: dispatchType, image: json});
      })
      .catch((error) => {
        console.error(error);
        navigation.navigate({name: nextNavigationName, props: {}, merge: true});
        dispatch({type: actionTypes.ERROR_UPLOAD_IMAGE});
      });
  });
};

export const getEntityImages = (entityId, dispatchType = actionTypes.GET_ENTITY_IMAGES) => dispatch => {
  const instance = Singleton.getInstance(),
    {Urls, Domain} = instance;

  getToken().then(token => {
    const url = reCache(`${Domain}${Urls['edw:entity-image-list'](entityId)}`),
      parameters = {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        },
      };

    uniFetch(url, parameters)
      .then(response => response.json()).then(json => {
        dispatch({type: dispatchType, images: json.results});
      })
      .catch(() => {
        dispatch({type: actionTypes.ERROR_GET_ENTITY_IMAGES});
      });
  });
};

export const deleteImage = (entityId, imageId, dispatchType = actionTypes.DELETE_IMAGE) => dispatch => {
  const instance = Singleton.getInstance(),
    {Urls, Domain} = instance;

  getToken().then(token => {
    const url = `${Domain}${Urls['edw:entity-image-detail'](entityId, imageId)}`,
      parameters = {
        method: 'DELETE',
        headers: {
          'Authorization': `Token ${token}`,
        },
      };

    uniFetch(url, parameters, {}, false)
      .then(() => {
        dispatch({type: dispatchType, imageId});
      })
      .catch(() => {
        dispatch({type: actionTypes.ERROR_DELETE_IMAGE});
      });
  });
};
