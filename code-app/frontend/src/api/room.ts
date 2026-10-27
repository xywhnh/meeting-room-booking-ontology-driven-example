import { http } from './request'

export interface Room {
  id: number
  room_no: string
  room_name: string
  capacity: number
  location: string | null
  status: string
}

export const roomApi = {
  list(status?: string) {
    return http.get<Room[]>('/rooms', status ? { status } : undefined)
  },
  create(data: Partial<Room>) {
    return http.post<Room>('/rooms', data)
  },
}
