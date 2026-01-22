import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'


export default defineConfig({
    plugins: [
        react()
    ],
    //base: './',
    root: __dirname,
    publicDir: resolve(__dirname, 'public'),
    server: {
        host: '0.0.0.0',
        port: 40099,
        //strictPort: true,    // Don't try other ports if occupied
        //open: false,         // Don't open browser automatically
        //cors: true,          // Enable CORS for captive portal
        hmr: {
            host: 'localhost', // HMR still on localhost for dev
            port: 24678
        }
    },
    // For captive portal, you might want different config
    preview: {
        host: '0.0.0.0',
        port: 40099
    },
    build: {
        outDir: resolve(__dirname, 'build'),
        emptyOutDir: true,
        rollupOptions: {
            input: 'index.html',
        },
    },
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
            crypto: resolve('crypto-browserify'),
            process: resolve('process/browser'),
            fs: resolve('browserify-fs'),
            buffer: resolve('buffer/'),
        },
    },
    define: {
        'process.env': {}
    },
    optimizeDeps: {
        include: ['buffer'],
    },
});
