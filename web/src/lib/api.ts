import type { Device } from "./mock-data"

// Re-exportar tipos para uso externo
export type { Device, SensorReading } from "./mock-data"

// URL da API - deve ser configurada via variável de ambiente
// Em desenvolvimento local: http://localhost:8000
// Em Docker/produção: http://localhost:8000 ou http://seu-servidor:8000
// No Vite, variáveis de ambiente precisam ter prefixo VITE_
// Mas mantemos compatibilidade com NEXT_PUBLIC_API_URL
const API_URL = import.meta.env.VITE_API_URL || 
                import.meta.env.NEXT_PUBLIC_API_URL || 
                "http://localhost:8000"

console.log(import.meta.env.VITE_API_URL)
console.log(import.meta.env.NEXT_PUBLIC_API_URL)
if (!import.meta.env.VITE_API_URL && !import.meta.env.NEXT_PUBLIC_API_URL) {
  console.warn(
    "⚠️ VITE_API_URL ou NEXT_PUBLIC_API_URL não configurada, usando padrão:",
    API_URL
  )
}

export interface HistoricalReading {
  timestamp: string
  t: number
  h: number
  g: number
  fluxo: number
  pulso: number
  sensor: number
  solo: number
}

export interface Stats {
  totalDevices: number
  onlineDevices: number
  offlineDevices: number
  avgTemperature: number
  avgHumidity: number
}

/**
 * Busca lista de todos os dispositivos
 */
export async function getDevices(): Promise<Device[]> {
  const response = await fetch(`${API_URL}/devices`)
  if (!response.ok) {
    throw new Error(`Erro ao buscar dispositivos: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Busca detalhes de um dispositivo específico
 */
export async function getDevice(deviceId: string): Promise<Device> {
  const response = await fetch(`${API_URL}/devices/${deviceId}`)
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Dispositivo não encontrado")
    }
    throw new Error(`Erro ao buscar dispositivo: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Busca histórico de leituras de um dispositivo
 */
export async function getDeviceReadings(
  deviceId: string,
  timeRange: string = "24h"
): Promise<HistoricalReading[]> {
  const response = await fetch(
    `${API_URL}/devices/${deviceId}/readings?time_range=${timeRange}`
  )
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Dispositivo não encontrado")
    }
    throw new Error(`Erro ao buscar histórico: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Busca estatísticas agregadas
 */
export async function getStats(): Promise<Stats> {
  const response = await fetch(`${API_URL}/stats`)
  if (!response.ok) {
    throw new Error(`Erro ao buscar estatísticas: ${response.statusText}`)
  }
  return response.json()
}

// Tipos para eventos do ChirpStack
export interface ChirpStackEvent {
  id: number
  event_type: string
  dev_eui: string
  device_name: string | null
  application_name: string | null
  event_time: string
  deduplication_id: string | null
  f_cnt: number | null
  f_port: number | null
  dr: number | null
  rssi: number | null
  snr: number | null
  frequency: number | null
  spreading_factor: number | null
  log_level: string | null
  log_code: string | null
  log_description: string | null
  payload: Record<string, any>
  received_at: string
}

export interface ChirpStackEventStats {
  total_events: number
  events_by_type: Record<string, number>
  unique_devices: number
  latest_event: string | null
  date_range: {
    earliest: string | null
    latest: string | null
  }
}

export interface ChirpStackDevice {
  dev_eui: string
  device_name: string | null
  application_name: string | null
  event_count: number
  last_event: string
}

export interface ChirpStackEventFilters {
  dev_eui?: string
  event_type?: string
  start_date?: string
  end_date?: string
  min_id?: number
  max_id?: number
  limit?: number
  offset?: number
}

/**
 * Busca lista de eventos do ChirpStack com filtros opcionais
 */
export async function getChirpStackEvents(
  filters?: ChirpStackEventFilters
): Promise<ChirpStackEvent[]> {
  const params = new URLSearchParams()
  
  if (filters?.dev_eui) params.append("dev_eui", filters.dev_eui)
  if (filters?.event_type) params.append("event_type", filters.event_type)
  if (filters?.start_date) params.append("start_date", filters.start_date)
  if (filters?.end_date) params.append("end_date", filters.end_date)
  if (filters?.min_id !== undefined) params.append("min_id", filters.min_id.toString())
  if (filters?.max_id !== undefined) params.append("max_id", filters.max_id.toString())
  if (filters?.limit) params.append("limit", filters.limit.toString())
  if (filters?.offset) params.append("offset", filters.offset.toString())

  const queryString = params.toString();
  const url = queryString ? `${API_URL}/chirpstack/events?${queryString}` : `${API_URL}/chirpstack/events`;
  const response = await fetch(url)
  
  if (!response.ok) {
    throw new Error(`Erro ao buscar eventos: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Busca detalhes de um evento específico
 */
export async function getChirpStackEvent(eventId: number): Promise<ChirpStackEvent> {
  const response = await fetch(`${API_URL}/chirpstack/events/${eventId}`)
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Evento não encontrado")
    }
    throw new Error(`Erro ao buscar evento: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Busca estatísticas dos eventos do ChirpStack
 */
export async function getChirpStackStats(): Promise<ChirpStackEventStats> {
  const response = await fetch(`${API_URL}/chirpstack/stats`)
  if (!response.ok) {
    throw new Error(`Erro ao buscar estatísticas: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Busca resumo de eventos de um dispositivo específico
 */
export async function getChirpStackDeviceSummary(devEui: string): Promise<any> {
  const response = await fetch(`${API_URL}/chirpstack/devices/${devEui}/summary`)
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Nenhum evento encontrado para este dispositivo")
    }
    throw new Error(`Erro ao buscar resumo: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Lista todos os dispositivos únicos que geraram eventos
 */
export async function getChirpStackDevices(): Promise<ChirpStackDevice[]> {
  const response = await fetch(`${API_URL}/chirpstack/devices`)
  if (!response.ok) {
    throw new Error(`Erro ao buscar dispositivos: ${response.statusText}`)
  }
  return response.json()
}

