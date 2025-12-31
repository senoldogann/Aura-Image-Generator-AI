import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import './App.css'
import { IconSettings, IconLoader, IconWand } from './components/Icons'

// Logic Layer
import { useAuraEngine } from './hooks/useAuraEngine'

// Presentation Layer
import { RefinementModal } from './components/RefinementModal'
import { ResultView } from './components/ResultView'
import { HistoryStrip } from './components/HistoryStrip'

function App() {
  const { state, setters, actions } = useAuraEngine()
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Standard Download Helper
  const handleDownload = async (url: string, filename?: string) => {
    try {
      const response = await fetch(url)
      const blob = await response.blob()
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      link.setAttribute('download', filename || `aura_${Date.now()}.png`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      setters.showToast("Download Started", "success")
    } catch {
      setters.showToast("Download failed", "error")
    }
  }

  const handleDownloadZip = () => {
    const link = document.createElement('a')
    link.href = `http://127.0.0.1:8000/export-zip`
    link.setAttribute('download', `aura_history_${Date.now()}.zip`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    setters.showToast("Exporting History...", "success")
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    actions.generateImage()
  }

  return (
    <div className="app-container">
      {/* Toast Notification */}
      <AnimatePresence>
        {state.toast.type && (
          <motion.div
            className={`toast-notification ${state.toast.type}`}
            initial={{ opacity: 0, y: -20, right: 20 }}
            animate={{ opacity: 1, y: 0, right: 24 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <span className="toast-icon">{state.toast.type === 'success' ? '✨' : '⚠️'}</span>
            {state.toast.message}
          </motion.div>
        )}
      </AnimatePresence>

      <RefinementModal
        show={showAdvanced}
        onClose={() => setShowAdvanced(false)}
        model={state.model} setModel={setters.setModel}
        aspectRatio={state.aspectRatio} setAspectRatio={setters.setAspectRatio}
        negativePrompt={state.negativePrompt} setNegativePrompt={setters.setNegativePrompt}
        autoUpscale={state.autoUpscale} setAutoUpscale={setters.setAutoUpscale}
      />

      <div className="content-wrapper">
        <header className="header">
          <motion.h1 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            A U R A
          </motion.h1>
          <motion.p className="subtitle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
            Digital Artisan Reality • <a href="https://www.senoldogan.dev" target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'none', opacity: 0.8 }}>By Senol Dogan</a>
          </motion.p>
        </header>

        <main className="main-content">
          <div className="input-section">
            <form onSubmit={handleSubmit}>
              <div className="input-wrapper">
                <button type="button" onClick={() => setShowAdvanced(true)} className="settings-btn" title="Open Studio">
                  <IconSettings size={32} />
                </button>
                <input
                  type="text"
                  value={state.prompt}
                  onChange={(e) => setters.setPrompt(e.target.value)}
                  placeholder="Imagine something timeless..."
                  disabled={state.loading}
                />
                <button type="submit" className="main-btn" disabled={state.loading}>
                  {state.loading ? (
                    <span className="btn-content"><IconLoader size={18} className="spin" /> Creating...</span>
                  ) : (
                    <span className="btn-content"><IconWand size={18} /> Visualize</span>
                  )}
                </button>
              </div>
            </form>
          </div>

          <ResultView
            loading={state.loading}
            imageUrl={state.imageUrl}
            progress={state.progress}
            error={state.result?.error}
            upscaling={state.upscaling}
            upscaleProgress={state.upscaleProgress}
            onDownload={handleDownload}
            onUpscale={actions.upscaleImage}
          />
        </main>

        <HistoryStrip
          history={state.history}
          currentImageUrl={state.imageUrl}
          onSelect={(item) => {
            setters.setResult(item)
            if (item.image_url) setters.setImageUrl(actions.getFullUrl(item.image_url))
          }}
          onDownloadZip={handleDownloadZip}
          onWatermark={actions.applyWatermark}
          onDownloadItem={handleDownload}
          getFullUrl={actions.getFullUrl}
        />
      </div>
    </div>
  )
}

export default App
