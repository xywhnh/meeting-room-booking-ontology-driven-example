import { http } from './request'

export interface RoomSummaryRow {
  id: number
  room_no: string
  room_name: string
  capacity: number
  location: string | null
  total_count: number
  approved_count: number
}

export const reportApi = {
  roomSummary(params?: { date_from?: string; date_to?: string }) {
    return http.get<RoomSummaryRow[]>('/report/room-summary', params)
  },
}
