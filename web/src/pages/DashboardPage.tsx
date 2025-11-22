import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Activity,
  Thermometer,
  Droplets,
  Server,
  Loader2,
  AlertCircle,
  Radio,
  Brain,
} from "lucide-react";
import { DeviceTable } from "@/components/device-table";
import { LanguageSelector } from "@/components/language-selector";
import { getDevices, getStats, type Device, type Stats } from "@/lib/api";
import { Link } from "react-router-dom";

export default function DashboardPage() {
  const { t } = useTranslation();
  const [devices, setDevices] = useState<Device[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [devicesData, statsData] = await Promise.all([
        getDevices(),
        getStats(),
      ]);
      setDevices(devicesData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.error"));
      console.error("Erro ao buscar dados:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">{t("common.loading")}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-8 h-8 mx-auto mb-4 text-destructive" />
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={fetchData}>{t("common.retry")}</Button>
        </div>
      </div>
    );
  }

  // Usar todos os dispositivos, mas filtrar apenas para cálculos de médias
  // Não filtrar dispositivos da lista - mostrar todos mesmo sem dados
  const allDevices = devices;

  const onlineDevices =
    stats?.onlineDevices ??
    allDevices.filter((d) => d.status === "online").length;
  const offlineDevices =
    stats?.offlineDevices ??
    allDevices.filter((d) => d.status === "offline").length;

  // Calcular médias apenas com dispositivos que têm valores válidos (> 0)
  const devicesWithTemp = allDevices.filter((d) => d.lastReading.t > 0);
  const devicesWithHumidity = allDevices.filter((d) => d.lastReading.h > 0);

  const avgTemperature =
    stats?.avgTemperature ??
    (devicesWithTemp.length > 0
      ? devicesWithTemp.reduce((acc, d) => acc + d.lastReading.t, 0) /
        devicesWithTemp.length
      : 0);
  const avgHumidity =
    stats?.avgHumidity ??
    (devicesWithHumidity.length > 0
      ? devicesWithHumidity.reduce((acc, d) => acc + d.lastReading.h, 0) /
        devicesWithHumidity.length
      : 0);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-foreground">
                {t("dashboard.title")}
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                {t("dashboard.subtitle")}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <LanguageSelector />
              <Link to="/chirpstack/events">
                <Button variant="outline" size="sm">
                  <Radio className="w-4 h-4 mr-2" />
                  {t("dashboard.chirpstackEvents")}
                </Button>
              </Link>
              <Badge variant="outline" className="gap-2">
                <Server className="w-3 h-3" />
                {allDevices.length} {t("common.device")}
                {allDevices.length !== 1 ? "s" : ""}
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Stats Overview */}
        <div className="mb-8">
          <h2 className="text-lg font-medium text-foreground mb-4">
            {t("dashboard.overview")}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6 bg-card border-border">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-green-500/10">
                  <Activity className="w-6 h-6 text-green-500" />
                </div>
              </div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                {t("dashboard.onlineDevices")}
              </h3>
              <p className="text-3xl font-semibold text-foreground">
                {onlineDevices}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                {allDevices.length > 0
                  ? ((onlineDevices / allDevices.length) * 100).toFixed(0)
                  : 0}
                % {t("dashboard.ofTotal")}
              </p>
            </Card>

            <Card className="p-6 bg-card border-border">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-red-500/10">
                  <Activity className="w-6 h-6 text-red-500" />
                </div>
              </div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                {t("dashboard.offlineDevices")}
              </h3>
              <p className="text-3xl font-semibold text-foreground">
                {offlineDevices}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                {allDevices.length > 0
                  ? ((offlineDevices / allDevices.length) * 100).toFixed(0)
                  : 0}
                % {t("dashboard.ofTotal")}
              </p>
            </Card>

            <Card className="p-6 bg-card border-border">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-chart-1/10">
                  <Thermometer className="w-6 h-6 text-chart-1" />
                </div>
              </div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                {t("dashboard.avgTemperature")}
              </h3>
              <p className="text-3xl font-semibold text-foreground">
                {avgTemperature > 0 ? `${avgTemperature.toFixed(1)}°C` : "—"}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                {devicesWithTemp.length > 0
                  ? `${devicesWithTemp.length} ${t("common.device")}${
                      devicesWithTemp.length > 1 ? "s" : ""
                    }`
                  : t("dashboard.noData")}
              </p>
            </Card>

            <Card className="p-6 bg-card border-border">
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-lg bg-chart-2/10">
                  <Droplets className="w-6 h-6 text-chart-2" />
                </div>
              </div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                {t("dashboard.avgHumidity")}
              </h3>
              <p className="text-3xl font-semibold text-foreground">
                {avgHumidity > 0 ? `${avgHumidity.toFixed(1)}%` : "—"}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                {devicesWithHumidity.length > 0
                  ? `${devicesWithHumidity.length} ${t("common.device")}${
                      devicesWithHumidity.length > 1 ? "s" : ""
                    }`
                  : t("dashboard.noData")}
              </p>
            </Card>
          </div>
        </div>

        {/* Quick Access Cards */}
        <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="p-6 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-blue-500/20">
                  <Radio className="w-8 h-8 text-blue-500" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-1">
                    {t("dashboard.chirpstackEvents")}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t("dashboard.chirpstackEventsDescription")}
                  </p>
                </div>
              </div>
              <Link to="/chirpstack/events">
                <Button size="lg" className="bg-blue-500 hover:bg-blue-600">
                  <Radio className="w-5 h-5 mr-2" />
                  {t("dashboard.viewEvents")}
                </Button>
              </Link>
            </div>
          </Card>

          <Card className="p-6 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-purple-500/20">
                  <Brain className="w-8 h-8 text-purple-500" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-1">
                    {t("dashboard.mlAnalysis")}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t("dashboard.mlAnalysisDescription")}
                  </p>
                </div>
              </div>
              <Link to="/ml/analysis">
                <Button size="lg" className="bg-purple-500 hover:bg-purple-600">
                  <Brain className="w-5 h-5 mr-2" />
                  {t("dashboard.analyze")}
                </Button>
              </Link>
            </div>
          </Card>
        </div>

        {/* Devices Table */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-foreground">
              {t("dashboard.registeredDevices")}
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchData}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t("common.updating")}
                </>
              ) : (
                t("common.update")
              )}
            </Button>
          </div>
          <DeviceTable devices={allDevices} />
        </div>
      </main>
    </div>
  );
}
