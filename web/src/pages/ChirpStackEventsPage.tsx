import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Activity,
  Loader2,
  AlertCircle,
  RefreshCw,
  Filter,
  X,
  Calendar,
  Radio,
} from "lucide-react";
import { ChirpStackEventsTable } from "@/components/chirpstack-events-table";
import { ChirpStackCharts } from "@/components/chirpstack-charts";
import {
  getChirpStackEvents,
  getChirpStackStats,
  getChirpStackDevices,
  type ChirpStackEvent,
  type ChirpStackEventStats,
  type ChirpStackDevice,
  type ChirpStackEventFilters,
} from "@/lib/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function ChirpStackEventsPage() {
  const [events, setEvents] = useState<ChirpStackEvent[]>([]);
  const [stats, setStats] = useState<ChirpStackEventStats | null>(null);
  const [devices, setDevices] = useState<ChirpStackDevice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Filtros
  const [selectedDevice, setSelectedDevice] = useState<string>("all");
  const [selectedEventType, setSelectedEventType] = useState<string>("all");
  const [limit, setLimit] = useState<number>(100);
  const [minId, setMinId] = useState<string>("");
  const [maxId, setMaxId] = useState<string>("");

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const filters: ChirpStackEventFilters = {
        limit,
      };

      if (selectedDevice !== "all") {
        filters.dev_eui = selectedDevice;
      }

      if (selectedEventType !== "all") {
        filters.event_type = selectedEventType;
      }

      if (minId.trim() !== "") {
        const minIdNum = Number.parseInt(minId.trim(), 10);
        if (!Number.isNaN(minIdNum) && minIdNum > 0) {
          filters.min_id = minIdNum;
        }
      }

      if (maxId.trim() !== "") {
        const maxIdNum = Number.parseInt(maxId.trim(), 10);
        if (!Number.isNaN(maxIdNum) && maxIdNum > 0) {
          filters.max_id = maxIdNum;
        }
      }

      const [eventsData, statsData, devicesData] = await Promise.all([
        getChirpStackEvents(filters),
        getChirpStackStats(),
        getChirpStackDevices(),
      ]);

      setEvents(eventsData);
      setStats(statsData);
      setDevices(devicesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dados");
      console.error("Erro ao buscar dados:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedDevice, selectedEventType, limit, minId, maxId]);

  const handleViewDetails = (event: ChirpStackEvent) => {
    // Abrir modal ou navegar para página de detalhes
    console.log("Ver detalhes do evento:", event);
    // Por enquanto apenas log, pode ser expandido depois
    alert(
      `Evento ID: ${event.id}\nTipo: ${event.event_type}\nDevice EUI: ${event.dev_eui}`
    );
  };

  const clearFilters = () => {
    setSelectedDevice("all");
    setSelectedEventType("all");
    setLimit(100);
    setMinId("");
    setMaxId("");
  };

  if (loading && events.length === 0) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Carregando eventos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">
                Eventos ChirpStack
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Visualização e monitoramento de eventos do ChirpStack
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="w-4 h-4 mr-2" />
                Filtros
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchData}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Atualizando...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Atualizar
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-destructive" />
              <p className="text-destructive">{error}</p>
            </div>
          </div>
        )}

        {/* Stats Overview */}
        {stats && (
          <div className="mb-8">
            <h2 className="text-lg font-medium text-foreground mb-4">
              Estatísticas
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="p-6 bg-card border-border">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-lg bg-blue-500/10">
                    <Activity className="w-6 h-6 text-blue-500" />
                  </div>
                </div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">
                  Total de Eventos
                </h3>
                <p className="text-3xl font-semibold text-foreground">
                  {stats.total_events}
                </p>
              </Card>

              <Card className="p-6 bg-card border-border">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-lg bg-green-500/10">
                    <Radio className="w-6 h-6 text-green-500" />
                  </div>
                </div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">
                  Dispositivos Únicos
                </h3>
                <p className="text-3xl font-semibold text-foreground">
                  {stats.unique_devices}
                </p>
              </Card>

              <Card className="p-6 bg-card border-border">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-lg bg-purple-500/10">
                    <Calendar className="w-6 h-6 text-purple-500" />
                  </div>
                </div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">
                  Último Evento
                </h3>
                <p className="text-sm font-semibold text-foreground">
                  {stats.latest_event
                    ? new Date(stats.latest_event).toLocaleString("pt-BR")
                    : "—"}
                </p>
              </Card>

              <Card className="p-6 bg-card border-border">
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-lg bg-yellow-500/10">
                    <Activity className="w-6 h-6 text-yellow-500" />
                  </div>
                </div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">
                  Eventos por Tipo
                </h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  {Object.entries(stats.events_by_type).map(([type, count]) => (
                    <Badge key={type} variant="outline" className="text-xs">
                      {type}: {count}
                    </Badge>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* Filtros */}
        {showFilters && (
          <Card className="mb-6 p-6 bg-card border-border">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-foreground">Filtros</h3>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="text-muted-foreground"
                >
                  <X className="w-4 h-4 mr-2" />
                  Limpar
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label
                  htmlFor="device-select"
                  className="text-sm font-medium text-foreground mb-2 block"
                >
                  Dispositivo
                </label>
                <Select
                  value={selectedDevice}
                  onValueChange={setSelectedDevice}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Todos os dispositivos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os dispositivos</SelectItem>
                    {devices.map((device: ChirpStackDevice) => (
                      <SelectItem key={device.dev_eui} value={device.dev_eui}>
                        {device.device_name ?? device.dev_eui} (
                        {device.event_count} eventos)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label
                  htmlFor="event-type-select"
                  className="text-sm font-medium text-foreground mb-2 block"
                >
                  Tipo de Evento
                </label>
                <Select
                  value={selectedEventType}
                  onValueChange={setSelectedEventType}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Todos os tipos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os tipos</SelectItem>
                    <SelectItem value="up">UP (Uplink)</SelectItem>
                    <SelectItem value="join">JOIN</SelectItem>
                    <SelectItem value="log">LOG</SelectItem>
                    <SelectItem value="ack">ACK</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label
                  htmlFor="limit-select"
                  className="text-sm font-medium text-foreground mb-2 block"
                >
                  Limite de Resultados
                </label>
                <Select
                  value={limit.toString()}
                  onValueChange={(value) =>
                    setLimit(Number.parseInt(value, 10))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="200">200</SelectItem>
                    <SelectItem value="500">500</SelectItem>
                    <SelectItem value="1000">1000</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Filtros de ID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-border">
              <div>
                <label
                  htmlFor="min-id-input"
                  className="text-sm font-medium text-foreground mb-2 block"
                >
                  ID Mínimo (a partir de)
                </label>
                <input
                  id="min-id-input"
                  type="number"
                  min="1"
                  value={minId}
                  onChange={(e) => setMinId(e.target.value)}
                  placeholder="Ex: 100"
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Eventos com ID maior ou igual a este valor
                </p>
              </div>
              <div>
                <label
                  htmlFor="max-id-input"
                  className="text-sm font-medium text-foreground mb-2 block"
                >
                  ID Máximo (até)
                </label>
                <input
                  id="max-id-input"
                  type="number"
                  min="1"
                  value={maxId}
                  onChange={(e) => setMaxId(e.target.value)}
                  placeholder="Ex: 200"
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Eventos com ID menor ou igual a este valor
                </p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground">
                💡 <strong>Dica:</strong> Use apenas ID Mínimo para buscar "a
                partir do ID X", apenas ID Máximo para buscar "até o ID X", ou
                ambos para um range específico (ex: 100 a 200).
              </p>
            </div>
          </Card>
        )}

        {/* Charts Section */}
        {events.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-medium text-foreground mb-4">
              Análise de Dados RF
            </h2>
            <ChirpStackCharts events={events} />
          </div>
        )}

        {/* Events Table */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-foreground">
              Eventos ({events.length})
            </h2>
          </div>
          <ChirpStackEventsTable
            events={events}
            onViewDetails={handleViewDetails}
          />
        </div>
      </main>
    </div>
  );
}
