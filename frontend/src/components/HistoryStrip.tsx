import { motion } from 'framer-motion'
import { IconDownload, IconWatermark } from './Icons'
import type { GenerateResponse } from '../types'

interface HistoryStripProps {
    history: GenerateResponse[]
    currentImageUrl: string | null
    onSelect: (item: GenerateResponse) => void
    onDownloadZip: () => void
    onWatermark: (url: string) => void
    onDownloadItem: (url: string) => void
    getFullUrl: (url: string) => string
}

export const HistoryStrip = ({ history, currentImageUrl, onSelect, onDownloadZip, onWatermark, onDownloadItem, getFullUrl }: HistoryStripProps) => {
    return (
        <footer className="history-slider-section">
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '15px' }}>
                <button className="utility-btn" onClick={onDownloadZip}>
                    <IconDownload size={16} /> Export History (ZIP)
                </button>
                {currentImageUrl && (
                    <button className="utility-btn" onClick={() => onWatermark(currentImageUrl)}>
                        <IconWatermark size={16} /> Add Watermark
                    </button>
                )}
            </div>

            {history.length > 0 && (
                <div className="marquee-container">
                    <div className="marquee-content">
                        {[...history, ...history].map((item, i) => (
                            <motion.div
                                key={`${item.image_url}-${i}`}
                                className="history-card-slide"
                                whileHover={{ scale: 1.05 }}
                                onClick={() => onSelect(item)}
                            >
                                <img src={getFullUrl(item.image_url || '')} alt={item.prompt || `Archived ${i}`} loading="lazy" />
                                <div className="history-overlay">
                                    <button
                                        className="history-download-btn"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            if (item.image_url) onDownloadItem(getFullUrl(item.image_url))
                                        }}
                                    >
                                        <IconDownload size={14} />
                                    </button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            )}
        </footer>
    )
}
