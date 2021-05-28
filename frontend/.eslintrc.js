module.exports = {
  root: true,
  extends: '@react-native-community',
  plugins: [
    'react-hooks',
  ],
  rules: {
    'prettier/prettier': 0,
    'react-hooks/rules-of-hooks': 'error', // Проверяем правила хуков
    'react-hooks/exhaustive-deps': 'warn', // Проверяем зависимости эффекта
    'curly': ['warn', 'multi-or-nest'],
  },
};
