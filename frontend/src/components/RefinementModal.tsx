import { motion } from 'framer-motion'
import { IconSettings, IconX } from './Icons'
import type { AspectRatio } from '../types'

interface RefinementModalProps {
    show: boolean
    onClose: () => void
    model: 'classic' | 'realistic'
    setModel: (m: 'classic' | 'realistic') => void
    aspectRatio: AspectRatio
    setAspectRatio: (r: AspectRatio) => void
    negativePrompt: string
    setNegativePrompt: (s: string) => void
    autoUpscale: boolean
    setAutoUpscale: (b: boolean) => void
}

export const RefinementModal = ({ show, onClose, model, setModel, aspectRatio, setAspectRatio, negativePrompt, setNegativePrompt, autoUpscale, setAutoUpscale }: RefinementModalProps) => {
    if (!show) return null

    return (
        <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
        >
            <motion.div
                className="modal-content"
                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.9, opacity: 0, y: 20 }}
            >
                <div className="modal-header">
                    <div className="modal-title-wrapper">
                        <IconSettings size={22} className="text-gold" />
                        <h2>Refinement Studio</h2>
                    </div>
                    <button onClick={onClose} className="close-btn"><IconX size={20} /></button>
                </div>

                <div className="advanced-controls">
                    <div className="control-group">
                        <label>Reality Engine</label>
                        <div className="model-selector">
                            <button className={`model-btn ${model === 'classic' ? 'active' : ''}`} onClick={() => setModel('classic')}>Aura Classic</button>
                            <button className={`model-btn ${model === 'realistic' ? 'active' : ''}`} onClick={() => setModel('realistic')}>Aura Realistic</button>
                        </div>
                    </div>

                    <div className="control-group">
                        <label>Output Quality</label>
                        <button
                            className={`text-btn ${autoUpscale ? 'active-gold' : ''}`}
                            onClick={() => setAutoUpscale(!autoUpscale)}
                            style={{ width: '100%', padding: '10px', border: '1px solid #333', borderRadius: '8px', background: autoUpscale ? 'rgba(212, 175, 55, 0.1)' : 'transparent', color: autoUpscale ? '#d4af37' : '#888', cursor: 'pointer', transition: 'all 0.3s' }}
                        >
                            {autoUpscale ? '✨ 4K Upscale Enabled' : 'Standard Resolution'}
                        </button>
                    </div>

                    <div className="control-group">
                        <label>Aspect Ratio</label>
                        <div className="ratio-selector">
                            {['auto', '1:1', '16:9', '9:16', '4:3', '3:4'].map((ratio) => (
                                <button
                                    key={ratio}
                                    className={`ratio-btn ${aspectRatio === ratio ? 'active' : ''}`}
                                    onClick={() => setAspectRatio(ratio as AspectRatio)}
                                >
                                    {ratio === 'auto' ? '🎯 Auto' : ratio}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="control-group">
                        <label>Negative Prompt</label>
                        <textarea
                            value={negativePrompt}
                            onChange={(e) => setNegativePrompt(e.target.value)}
                            placeholder="Describe what to exclude..."
                            rows={3}
                        />
                    </div>
                </div>
            </motion.div>
        </motion.div>
    )
}
