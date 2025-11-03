// seat-check/theme/useTheme.ts
import { useContext } from 'react';
import { ThemeContext } from './ThemeProvider';

export const useTheme = () => useContext(ThemeContext);
