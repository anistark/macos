import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { runsApi } from './vite-plugins/runs-api'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), runsApi()],
})
