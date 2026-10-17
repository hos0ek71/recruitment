// Set VITE_API_BASE_URL at build time; /api uses the local Vite proxy.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
