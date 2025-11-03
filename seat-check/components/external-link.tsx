import { Href, Link } from 'expo-router';
import { openBrowserAsync, WebBrowserPresentationStyle } from 'expo-web-browser';
import { Platform, StyleSheet } from 'react-native';
import { type ComponentProps } from 'react';

type Props = Omit<ComponentProps<typeof Link>, 'href'> & { href: Href & string };

const safeStyle = (s: any) => {
  const flat = Array.isArray(s)
    ? Object.assign({}, ...s.filter(Boolean).map(StyleSheet.flatten))
    : StyleSheet.flatten(s) || {};
  return flat;
};

export function ExternalLink({ href, style, ...rest }: Props) {
  const webSafeProps =
    Platform.OS === 'web' ? { ...rest, style: safeStyle(style) } : { ...rest, style };

  return (
    <Link
      target="_blank"
      {...webSafeProps}
      href={href}
      onPress={async (event) => {
        if (process.env.EXPO_OS !== 'web') {
          event.preventDefault();
          await openBrowserAsync(href, {
            presentationStyle: WebBrowserPresentationStyle.AUTOMATIC,
          });
        }
      }}
    />
  );
}
