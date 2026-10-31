import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/three')) {
            return 'vendor-three';
          }
          if (id.includes('node_modules/onnxruntime-web')) {
            return 'vendor-onnx';
          }
          if (id.includes('node_modules/lucide')) {
            return 'vendor-lucide';
          }
        },
      },
    },
  },
});

