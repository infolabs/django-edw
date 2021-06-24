export const dateFormat = (dateFormatted) => {
  return new Date(dateFormatted).toLocaleString('ru', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};
