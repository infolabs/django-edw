export const dateFormat = (dateFormatted) => {
  const d = new Date(dateFormatted);
  const day = d.getDate();
  const monthIndex = d.getMonth();
  const year = d.getFullYear();
  return `${day} ${MONTHS[monthIndex]} ${year} г.`
};

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
