import { http } from './request'

export interface Rule {
  id: string
  name: string
  description: string | null
  expression: string
  rule_type: string
  input_params: { name: string; type: string; sourceField?: string }[]
}

export const metaApi = {
  bookingStatus() {
    return http.get<string[]>('/meta/booking-status')
  },
  roomStatus() {
    return http.get<string[]>('/meta/room-status')
  },
  rules() {
    return http.get<Rule[]>('/meta/rules')
  },
}
