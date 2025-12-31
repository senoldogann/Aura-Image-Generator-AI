import { useState, useEffect, useCallback } from 'react'
import type { GenerateResponse, AspectRatio, ToastState } from '../types'

const API_URL = 'http://127.0.0.1:8000'

const STORAGE_KEYS = {
    model: 'aura_model',
    aspectRatio: 'aura_aspect_ratio',
    negativePrompt: 'aura_negative_prompt',
    history: 'aura_history'
}

export const useAuraEngine = () => {
    // State
    const [prompt, setPrompt] = useState('')
    const [aspectRatio, setAspectRatio] = useState<AspectRatio>('auto')
    const [negativePrompt, setNegativePrompt] = useState('')
    const [model, setModel] = useState<'classic' | 'realistic'>('realistic')
    const [autoUpscale, setAutoUpscale] = useState(false)

    const [loading, setLoading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [result, setResult] = useState<GenerateResponse | null>(null)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [history, setHistory] = useState<GenerateResponse[]>([])

    const [upscaling, setUpscaling] = useState(false)
    const [upscaleProgress, setUpscaleProgress] = useState(0)

    const [toast, setToast] = useState<ToastState>({ message: '', type: null })

    // Actions
    const showToast = useCallback((message: string, type: 'success' | 'error') => {
        setToast({ message, type })
        setTimeout(() => setToast({ message: '', type: null }), 3000)
    }, [])

    const getFullUrl = useCallback((url?: string) => {
        if (!url) return ''
        if (url.startsWith('http')) return url
        const path = url.startsWith('/') ? url.substring(1) : url
        return `${API_URL}/${path}`
    }, [])

    // Initialization
    useEffect(() => {
        const savedModel = localStorage.getItem(STORAGE_KEYS.model) as 'classic' | 'realistic' | null
        const savedRatio = localStorage.getItem(STORAGE_KEYS.aspectRatio) as AspectRatio | null
        const savedNegative = localStorage.getItem(STORAGE_KEYS.negativePrompt)

        if (savedModel) setModel(savedModel)
        if (savedRatio) setAspectRatio(savedRatio)
        if (savedNegative) setNegativePrompt(savedNegative)

        // Load History
        fetch(`${API_URL}/images`)
            .then(res => res.json())
            .then(data => {
                if (data.images?.length > 0) {
                    setHistory(data.images.map((img: any) => ({
                        success: true,
                        image_url: img.url,
                        created_at: img.created_at
                    })))
                }
            })
            .catch(() => {
                const saved = localStorage.getItem(STORAGE_KEYS.history)
                if (saved) setHistory(JSON.parse(saved))
            })
    }, [])

    // Persistence
    useEffect(() => { localStorage.setItem(STORAGE_KEYS.model, model) }, [model])
    useEffect(() => { localStorage.setItem(STORAGE_KEYS.aspectRatio, aspectRatio) }, [aspectRatio])
    useEffect(() => { localStorage.setItem(STORAGE_KEYS.negativePrompt, negativePrompt) }, [negativePrompt])
    useEffect(() => { localStorage.setItem(STORAGE_KEYS.history, JSON.stringify(history)) }, [history])

    // Handlers
    const generateImage = async () => {
        if (!prompt.trim() || loading) return

        setLoading(true)
        setResult(null)
        setImageUrl(null)
        setProgress(1)

        const evtSource = new EventSource(`${API_URL}/progress`)
        evtSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.percentage) setProgress(data.percentage)
            } catch (_) { }
        }

        try {
            const response = await fetch(`${API_URL}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt, model_key: model, aspect_ratio: aspectRatio, negative_prompt: negativePrompt || undefined,
                    auto_upscale: autoUpscale
                })
            })

            const data: GenerateResponse = await response.json()

            if (data.success && data.image_url) {
                await new Promise(r => setTimeout(r, 500)) // Wait for write
                const fullUrl = getFullUrl(data.image_url)
                const timestampedUrl = `${fullUrl}?t=${Date.now()}`
                const newEntry = { ...data, image_url: timestampedUrl, prompt }

                setImageUrl(timestampedUrl)
                setHistory((prev: GenerateResponse[]) => [newEntry, ...prev].slice(0, 50))
                setResult(newEntry)
                showToast("Masterpiece Created", "success")
            } else {
                setResult(data)
                showToast(data.error || "Generation failed", "error")
            }
        } catch (error) {
            showToast("Connection failed", "error")
        } finally {
            evtSource.close()
            setLoading(false)
            setProgress(0)
        }
    }

    const upscaleImage = async (currentUrl: string) => {
        if (upscaling) return
        setUpscaling(true)
        setUpscaleProgress(0)

        const evtSource = new EventSource(`${API_URL}/progress`)
        evtSource.onmessage = (e) => {
            const data = JSON.parse(e.data)
            if (data.percentage > 0) setUpscaleProgress(data.percentage)
        }

        try {
            const res = await fetch(`${API_URL}/upscale`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_path: currentUrl, prompt })
            })
            const data = await res.json()
            if (data.success && data.upscaled_image_url) {
                const full = getFullUrl(data.upscaled_image_url)
                const tsUrl = `${full}?t=${Date.now()}`
                setImageUrl(tsUrl)
                showToast("Upscaled to 4K", "success")
            } else {
                showToast(data.error || "Upscale failed", "error")
            }
        } catch {
            showToast("Upscale error", "error")
        } finally {
            evtSource.close()
            setUpscaling(false)
            setUpscaleProgress(0)
        }
    }

    const applyWatermark = async (currentUrl: string) => {
        try {
            const res = await fetch(`${API_URL}/watermark`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_path: currentUrl, text: 'AURA' })
            })
            const data = await res.json()
            if (data.success && data.watermarked_url) {
                setImageUrl(getFullUrl(data.watermarked_url))
                showToast('Watermark applied!', 'success')
            }
        } catch {
            showToast('Watermark failed', 'error')
        }
    }

    return {
        state: { prompt, aspectRatio, negativePrompt, model, autoUpscale, loading, progress, imageUrl, result, history, upscaling, upscaleProgress, toast },
        setters: { setPrompt, setAspectRatio, setNegativePrompt, setModel, setAutoUpscale, setImageUrl, setResult, showToast },
        actions: { generateImage, upscaleImage, applyWatermark, getFullUrl }
    }
}

