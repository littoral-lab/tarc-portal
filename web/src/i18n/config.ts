import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ptBR from './locales/pt-BR.json';
import en from './locales/en.json';

// Função para obter o idioma salvo no localStorage ou usar o padrão
const getStoredLanguage = (): string => {
  const stored = localStorage.getItem('i18nextLng');
  if (stored && (stored === 'pt-BR' || stored === 'en')) {
    return stored;
  }
  // Detecta o idioma do navegador
  const browserLang = navigator.language || 'pt-BR';
  return browserLang.startsWith('pt') ? 'pt-BR' : 'en';
};

i18n
  .use(initReactI18next)
  .init({
    resources: {
      'pt-BR': {
        translation: ptBR,
      },
      en: {
        translation: en,
      },
    },
    lng: getStoredLanguage(),
    fallbackLng: 'pt-BR',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;

