export type AspectRatio = 'auto' | '1:1' | '16:9' | '9:16' | '4:3' | '3:4'

export interface GenerateResponse {
    success: boolean
    image_url?: string
    error?: string
    prompt?: string
    created_at?: number
}

export type ToastType = 'success' | 'error' | null

export interface ToastState {
    message: string
    type: ToastType
}
