export function getPinColor(item) {
  let pinColor = "FEFEFE";
  const pinColorPattern = item.extra.group_size ? "group-pin-color-" : "pin-color-";
  if (item.short_marks.length) {
    for (const sm of item.short_marks) {
      if (sm.view_class.length) {
        for (const cl of sm.view_class) {
          if(cl.startsWith(pinColorPattern)) {
            pinColor = cl.replace(pinColorPattern, "").toUpperCase();
            return pinColor;
          }
        }
      }
    }
  }
  return pinColor;
}