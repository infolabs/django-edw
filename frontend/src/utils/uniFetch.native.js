import {Alert} from 'react-native';
import * as Sentry from '@sentry/react-native';


const STATUS_SERVER_ERRORS = [408, 500, 501, 502, 503, 504];
const STATUS_ERRORS = [400, 401, 402, 403, ...STATUS_SERVER_ERRORS];
const DEFAULT_ERROR_FIELDS = ['detail', 'non_field_errors', '__all__', 'token'];
const NETWORK_ERROR = 'Network request failed';
const RETRY = 'Повторить попытку';
const CANCEL = 'Отменить';
const title = {
  SUCCESS: 'Запрос выполнен успешно',
  ERROR: 'Ошибка выполнения запроса',
};
const errors = {
  NETWORK: 'Ошибка сети! Проверьте подключение и попробуйте еще раз.',
  SERVER: 'Ошибка сервера! Приложение временно недоступно. Попробуйте позже.',
  UNKNOWN: 'Неизвестная ошибка.',
};



//onPress: () => uniFetch(...args),
const AsyncAlert = (title, msg, args) => new Promise((resolve, reject) => {
  Alert.alert(title, msg, [{
    text: CANCEL,
    style: 'cancel',
    onPress: () => { resolve(false); },
  }, {
    text: RETRY,
    style: 'default',
    onPress: () => { resolve(true); },
  }], { cancelable: false });
});


async function handleFetchError(error, args) {
  if (error instanceof TypeError && error.message === NETWORK_ERROR) {
    const retry = await AsyncAlert(title.ERROR, errors.NETWORK, args);
    if (retry)
      return await uniFetch(...args);
  } else {
    const url = args[0];
    Sentry.captureMessage(`${url}. Error: ${error}`);
  }
  return null;
}

function handleFieldErrors(json, response, nameFields) {
  const jsonIsArray = json instanceof Array,
        jsonKeys = jsonIsArray ? Object.keys(json[0]) : Object.keys(json);

  let msg = `Response error. Code: ${response.code}. Status: ${response.status}. Url: ${response.url}`;
  if (!STATUS_SERVER_ERRORS.includes(response.status)) {
    jsonKeys.map(item => {
      const fieldError = nameFields.hasOwnProperty(item) ? nameFields[item] : item,
            valueError = jsonIsArray ? json[0][item] : json[item];
      msg = DEFAULT_ERROR_FIELDS.includes(fieldError) ? `${valueError}` : `${fieldError}: ${valueError}`;
      Alert.alert(
        title.ERROR,
        msg
      );
    });
  }
  return msg;
}

async function resolveJson(response) {
  let json;

  try {
    json = await response.json();
  } catch (error) {
    const msg = `Response without json. Status: ${response.status}. Error: ${error}. Url: ${response.url}.`;
    if (STATUS_SERVER_ERRORS.includes(response.status)){
      Alert.alert(title.ERROR, errors.SERVER);
    } else {
      Alert.alert(title.ERROR, errors.UNKNOWN);
      Sentry.captureMessage(msg, response);
    }
    throw new Error(msg);
  }
  return json;
}


async function uniFetch(url, params = {}, nameFields = {}, returnJson = true) {
  params.credentials = 'include';

  let response;
  try {
    response = await fetch(url, params);
  } catch (error) {
    const handled = await handleFetchError(error, arguments);
    if (handled instanceof Response)
      return handled;
    throw error;
  }

  if (response.ok) {
    if (returnJson) {
      const json = await resolveJson(response);
      return Object.assign(response, {json: async () => json});
    } else {
      return response;
    }
  } else {
    let msg;
    if (STATUS_ERRORS.includes(response.status)) {
      const json = await resolveJson(response);
      msg = handleFieldErrors(json, response, nameFields);
    } else {
      Alert.alert(title.ERROR, errors.UNKNOWN);
      msg = `Unknow response code: ${response.code}. Url: ${url}. Status: ${response.status}`;
      Sentry.captureMessage(msg, response);
    }
    throw new Error(msg);
  }
}

export default uniFetch;
