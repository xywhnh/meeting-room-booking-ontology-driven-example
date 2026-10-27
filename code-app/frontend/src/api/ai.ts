import { http } from './request'

export interface AssistantAction { label: string; path: string }
export interface AssistantReply { reply: string; data: any[]; action: AssistantAction | null }

export const aiApi = {
  chat(message: string) {
    return http.post<AssistantReply>('/ai/chat', { message })
  },
}
