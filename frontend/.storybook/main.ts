import type { StorybookConfig } from '@storybook/react-vite'
const config: StorybookConfig = {
  framework: '@storybook/react-vite',
  stories: ['../stories/**/*.stories.tsx'],
  addons: ['@storybook/addon-docs', '@storybook/addon-a11y'],
  core: { disableTelemetry: true },
  docs: { autodocs: true },
  viteFinal: async config => ({
    ...config,
    // Storybook's docs/a11y iframe is a tooling aggregate. The application
    // build is independently route-split and has its own 1.2 MB budget.
    build: { ...config.build, chunkSizeWarningLimit: 1200 },
  }),
}
export default config
