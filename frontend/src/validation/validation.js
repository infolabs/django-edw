const isEmpty = value => value === undefined || value === null || value === '';
const join = (rules) => value => rules.map(rule => rule(value)).filter(error => !!error)[0 /* first error */];

