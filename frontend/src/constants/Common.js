export const WEB = 'WEB';
export const NATIVE = 'NATIVE';
export const NODE = 'NODE';

function platform() {
  if (typeof document != 'undefined')
    return WEB;
  else if (typeof navigator != 'undefined' && navigator.product == 'ReactNative')
    return NATIVE;
  else
    return NODE;
}

export const PLATFORM = platform();

export const RECACHE_RATE = 60000;
