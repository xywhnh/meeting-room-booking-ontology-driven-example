import {
  Users, UserPlus, Search, ClipboardList, Inbox, CheckSquare, FileText,
  GitBranch, Workflow, List, ListChecks, Settings, User, Shield, Key, Menu,
  Calendar, CalendarPlus, DoorOpen, BarChart3,
  Circle, type LucideIcon,
} from 'lucide-react'

const iconMap: Record<string, LucideIcon> = {
  Users, UserPlus, Search, ClipboardList, Inbox, CheckSquare, FileText,
  GitBranch, Workflow, List, ListChecks, Settings, User, Shield, Key, Menu,
  Calendar, CalendarPlus, DoorOpen, BarChart3,
}

export function MenuIcon({ name, size = 16 }: { name: string | null; size?: number }) {
  const Comp = iconMap[name || ''] || Circle
  return <Comp size={size} />
}
