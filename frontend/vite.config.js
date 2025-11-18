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
        port: 40099,
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
