const tintColorLight = '#2f95dc';
const tintColorDark = '#fff';

export default {
  light: {
    text: '#000',
    background: '#fff',
    tint: tintColorLight,
    tabIconDefault: '#ccc',
    tabIconSelected: tintColorLight,
  },
  dark: {
    text: '#fff',
    background: '#121212',
    tint: tintColorDark,
    tabIconDefault: '#ccc',
    tabIconSelected: tintColorDark,
  },
  // Trading platform specific colors
  trading: {
    primary: '#5B48D2',
    secondary: '#2C2F3F',
    accent: '#43D1A7',
    positive: '#1EB980', // For profit/gain
    negative: '#FF4757', // For loss
    warning: '#FFC107',
    info: '#2196F3',
    surface: '#1A1C28',
    card: '#2C2F3F',
    border: '#3F4455',
    disabled: '#9E9E9E',
    placeholder: '#9E9E9E',
    backdrop: 'rgba(0, 0, 0, 0.5)',
    notification: '#FF4757',
  }
};