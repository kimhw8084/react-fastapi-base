import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from './platform/ui/ErrorBoundary'
import { ExperienceLab } from './app/lab/ExperienceLab'
import { Application } from './app/Application'
import { loadRuntime } from './platform/api/runtime'
import { errorMessage } from './platform/api/client'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import './theme/tokens.css'
import './theme/application.css'

const root = ReactDOM.createRoot(document.getElementById('root')!)
const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 10000, retry: 1, refetchOnWindowFocus: false }, mutations: { retry: false } } })
if(window.location.pathname==='/lab'||window.location.pathname.startsWith('/lab/')){root.render(<ExperienceLab/>)}else loadRuntime().then(runtime => root.render(<React.StrictMode><QueryClientProvider client={queryClient}><ErrorBoundary><BrowserRouter><Application runtime={runtime}/></BrowserRouter></ErrorBoundary></QueryClientProvider></React.StrictMode>)).catch(error => root.render(<main className="startup"><h1>Configuration needs attention</h1><p role="alert">{errorMessage(error)}</p><p>Correct runtime-config.json and reload. No identity or storage fallback has been applied.</p></main>))
