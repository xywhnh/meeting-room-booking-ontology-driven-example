import { http, type PageResult } from './request'
import type { FlowTask } from './flow'
import type { Booking } from './booking'

export interface TodoItem extends FlowTask {
  purpose?: string
  booking_no?: string
  room_name?: string
  applicant_name?: string
  started_at?: string
}

export interface DoneItem extends FlowTask {
  purpose?: string
  booking_no?: string
}

export interface RequestedItem extends Booking {
  room_name?: string
  flow_status?: string
}

export const workbenchApi = {
  todo(params: { page?: number; size?: number }) {
    return http.get<PageResult<TodoItem>>('/workbench/todo', params)
  },
  done(params: { page?: number; size?: number }) {
    return http.get<PageResult<DoneItem>>('/workbench/done', params)
  },
  requested(params: { page?: number; size?: number }) {
    return http.get<PageResult<RequestedItem>>('/workbench/requested', params)
  },
  approve(taskId: number, comment: string) {
    return http.post(`/workbench/todo/${taskId}/approve`, { comment })
  },
  reject(taskId: number, comment: string) {
    return http.post(`/workbench/todo/${taskId}/reject`, { comment })
  },
  returnTask(taskId: number, comment: string) {
    return http.post(`/workbench/todo/${taskId}/return`, { comment })
  },
}
