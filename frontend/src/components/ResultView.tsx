import { motion, AnimatePresence } from 'framer-motion'
import { IconDownload, IconSparkles, IconLoader } from './Icons'

interface ResultViewProps {
    loading: boolean
    imageUrl: string | null
    progress: number
    error?: string
    upscaling: boolean
    upscaleProgress: number
    onDownload: (url: string) => void
    onUpscale: (url: string) => void
}

export const ResultView = ({ loading, imageUrl, progress, error, upscaling, upscaleProgress, onDownload, onUpscale }: ResultViewProps) => {
    return (
        <div className="result-area">
            <AnimatePresence mode="wait">
                {loading ? (
                    <motion.div
                        key="loading"
                        className="loading-state"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <div className="spinner-luxury" />
                        <div className="progress-display">
                            <div className="step-count">Crafting Masterpiece... {progress}%</div>
                        </div>
                        <span className="loading-text">Weaving the digital threads...</span>
                    </motion.div>
                ) : imageUrl ? (
                    <div className="image-container">
                        <motion.img
                            key={imageUrl}
                            src={imageUrl}
                            alt="Generated Masterpiece"
                            className="result-image"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.8 }}
                        />

                        <div className="image-overlay-top">
                            <button className="overlay-download-btn" onClick={() => onDownload(imageUrl)} title="Download Image">
                                <IconDownload size={32} />
                            </button>
                        </div>

                        <div className="image-actions">
                            <button
                                className={`upscale-btn ${upscaling ? 'processing' : ''}`}
                                onClick={() => onUpscale(imageUrl)}
                                disabled={upscaling}
                            >
                                {upscaling ? (
                                    <><IconLoader size={16} className="spin" /> &nbsp; Enhancing Reality... {upscaleProgress}%</>
                                ) : (
                                    <><IconSparkles size={16} /> Upscale to 4K</>
                                )}
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="placeholder-text">
                        {error ? <span style={{ color: '#d44' }}>Error: {error}</span> : "Your vision will manifest here..."}
                    </div>
                )}
            </AnimatePresence>
        </div>
    )
}
