import { http, type PageResult } from './request'

export interface Booking {
  id: number
  booking_no: string
  room_id: number
  room_name?: string
  room_no?: string
  capacity?: number
  location?: string | null
  booking_date: string
  start_time: string
  end_time: string
  purpose: string
  participants: number
  status: string
  applicant_id: number | null
  applicant_name: string | null
  instance_id: number | null
  created_at: string
  flow_status?: string
}

export const bookingApi = {
  list(params: { page?: number; size?: number; booking_no?: string; room_id?: number; booking_date?: string; status?: string }) {
    return http.get<PageResult<Booking>>('/booking', params)
  },
  get(id: number) {
    return http.get<Booking>(`/booking/${id}`)
  },
  createDraft(data: Partial<Booking>) {
    return http.post<Booking>('/booking/draft', data)
  },
  updateDraft(id: number, data: Partial<Booking>) {
    return http.put<Booking>(`/booking/${id}/draft`, data)
  },
  submit(id: number) {
    return http.post<Booking>(`/booking/${id}/submit`)
  },
  withdraw(id: number) {
    return http.post<Booking>(`/booking/${id}/withdraw`)
  },
}
