import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Radio, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const { login, isLoading, error } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch {}
  }

  const demoLogin = () => {
    setEmail('demo@sonarx.ai')
    setPassword('demo123')
  }

  return (
    <div className="min-h-screen bg-navy-900 sonar-grid-bg flex items-center justify-center p-4">
      {/* Ambient rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[600px] h-[600px] rounded-full border border-sonar-cyan/5 absolute" />
        <div className="w-[400px] h-[400px] rounded-full border border-sonar-cyan/8 absolute" />
        <div className="w-[200px] h-[200px] rounded-full border border-sonar-cyan/12 absolute" />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo card */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-sonar-cyan/15 border border-sonar-cyan/30 mb-4">
            <Radio className="w-8 h-8 text-sonar-cyan sonar-pulse" />
          </div>
          <h1 className="text-4xl font-bold text-white tracking-wider mb-1">SONAR-X</h1>
          <p className="text-slate-400 text-sm leading-relaxed">
            Physics-Aware Explainable<br />Marine Debris Intelligence System
          </p>
          <div className="mt-3 inline-flex gap-2">
            <span className="text-xs font-mono bg-navy-800 text-sonar-cyan border border-sonar-cyan/20 px-2 py-0.5 rounded">
              SIH26057
            </span>
            <span className="text-xs font-mono bg-navy-800 text-slate-400 border border-slate-700 px-2 py-0.5 rounded">
              Team Kurukshetra
            </span>
          </div>
        </div>

        {/* Login form */}
        <div className="bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="operator@survey.com"
                required
                className="w-full bg-navy-800/60 border border-white/10 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-sonar-cyan/50 focus:ring-1 focus:ring-sonar-cyan/20 transition-all text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-navy-800/60 border border-white/10 rounded-lg px-4 py-2.5 pr-10 text-white placeholder-slate-500 focus:outline-none focus:border-sonar-cyan/50 focus:ring-1 focus:ring-sonar-cyan/20 transition-all text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-ocean-600 hover:bg-ocean-700 disabled:opacity-60 text-white font-semibold py-2.5 rounded-lg transition-colors text-sm"
            >
              {isLoading ? 'Authenticating…' : 'Login'}
            </button>

            <div className="relative flex items-center gap-3">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-xs text-slate-500">or</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            <button
              type="button"
              onClick={demoLogin}
              className="w-full border border-sonar-cyan/30 text-sonar-cyan hover:bg-sonar-cyan/10 font-medium py-2.5 rounded-lg transition-colors text-sm"
            >
              Demo Login
            </button>
          </form>

          <div className="mt-5 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
            <p className="text-xs text-amber-300 text-center">
              Demo credentials: <span className="font-mono">demo@sonarx.ai</span> / <span className="font-mono">demo123</span>
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          SONAR-X Prototype · Marine &amp; Ocean · Smart India Hackathon 2025
        </p>
      </div>
    </div>
  )
}
