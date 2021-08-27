export const dateFormat = (date, onlyDate = true) => {
  const d = new Date(date);
  const day = d.getDate();
  const monthIndex = d.getMonth();
  const year = d.getFullYear();
  if (onlyDate)
    return `${day} ${MONTHS[monthIndex]} ${year} г.`;

  const hour = d.getHours();
  const minutes = d.getMinutes();
  return `${day} ${MONTHS[monthIndex]} ${year} г. ${hour > 10 ? hour : `0${hour}`}:${minutes > 10 ? minutes : `0${minutes}`}`;
};

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
