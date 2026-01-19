import { useState, useEffect } from 'react';
import { themes } from '../utils/theme-constants';

export const useTheme = (initialTheme = "default") => {
  const [theme, setTheme] = useState(initialTheme);

  useEffect(() => {
    const currentTheme = themes[theme];
    if (currentTheme) {
      document.documentElement.style.setProperty('--theme-bg-gradient', currentTheme.bgGradient);
      document.documentElement.style.setProperty('--theme-header-bg', currentTheme.headerBg);
      document.documentElement.style.setProperty('--theme-primary', currentTheme.primaryColor);
      document.documentElement.style.setProperty('--theme-secondary', currentTheme.secondaryColor);
      document.documentElement.setAttribute('data-theme', theme);
    }
  }, [theme]);

  return { theme, setTheme };
};
