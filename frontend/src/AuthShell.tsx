import { useState } from 'react'
import type React from 'react'
import App from './App'
import { service } from './services'

export default function AuthShell() {
  const [authenticated, setAuthenticated] = useState(() => service.isAuthenticated?.() ?? true)

  if (!authenticated) {
    return <AuthScreen onAuthenticated={() => setAuthenticated(true)} />
  }

  const handleClickCapture = (event: React.MouseEvent<HTMLDivElement>) => {
    const button = (event.target as HTMLElement).closest('button')
    if (button?.textContent?.includes('Sign out')) {
      service.logout?.()
      setAuthenticated(false)
    }
  }

  return <div onClickCapture={handleClickCapture}><App /></div>
}

function AuthScreen({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [registering, setRegistering] = useState(true)
  const [error, setError] = useState('')
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    const form = new FormData(event.currentTarget)
    try {
      const email = String(form.get('email'))
      const password = String(form.get('password'))
      if (registering) await service.register?.(email, password)
      else await service.login?.(email, password)
      onAuthenticated()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to authenticate')
    }
  }

  return <main className="auth-page"><section className="auth-card"><div className="brand auth-brand"><span className="brand-mark">◒</span><span>spend<span>lens</span></span></div><h1>{registering ? 'Create your account' : 'Welcome back'}</h1><p>{registering ? 'Start seeing your spending clearly.' : 'Sign in to your personal workspace.'}</p><form onSubmit={submit}><label>Email<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" minLength={8} autoComplete={registering ? 'new-password' : 'current-password'} required /></label>{error && <p className="auth-error" role="alert">{error}</p>}<button className="primary" type="submit">{registering ? 'Register' : 'Log in'}</button></form><button className="auth-toggle" onClick={() => { setRegistering(!registering); setError('') }}>{registering ? 'Already have an account? Log in' : 'Need an account? Register'}</button></section></main>
}
