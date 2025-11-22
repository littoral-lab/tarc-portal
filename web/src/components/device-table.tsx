import { useTranslation } from "react-i18next";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Eye } from "lucide-react";
import { Link } from "react-router-dom";
import type { Device } from "@/lib/mock-data";

interface DeviceTableProps {
  devices: Device[];
}

export function DeviceTable({ devices }: DeviceTableProps) {
  const { t } = useTranslation();
  return (
    <Card className="bg-card border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t("common.name")}</TableHead>
            <TableHead>{t("common.id")}</TableHead>
            <TableHead>{t("common.status")}</TableHead>
            <TableHead>{t("common.location")}</TableHead>
            <TableHead>{t("common.lastUpdate")}</TableHead>
            <TableHead>{t("common.temperature")}</TableHead>
            <TableHead>{t("common.humidity")}</TableHead>
            <TableHead className="text-right">{t("common.actions")}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {devices.map((device) => (
            <TableRow key={device.id}>
              <TableCell className="font-medium">{device.name}</TableCell>
              <TableCell className="font-mono text-xs">{device.id}</TableCell>
              <TableCell>
                <Badge
                  variant={device.status === "online" ? "default" : "secondary"}
                  className={
                    device.status === "online"
                      ? "bg-green-500/10 text-green-500 hover:bg-green-500/20"
                      : ""
                  }
                >
                  <div
                    className={`w-2 h-2 rounded-full mr-2 ${
                      device.status === "online"
                        ? "bg-green-500 animate-pulse"
                        : "bg-muted-foreground"
                    }`}
                  />
                  {device.status === "online"
                    ? t("common.online")
                    : t("common.offline")}
                </Badge>
              </TableCell>
              <TableCell>{device.location}</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {device.lastUpdate}
              </TableCell>
              <TableCell>
                {device.lastReading.t > 0
                  ? `${device.lastReading.t.toFixed(1)}°C`
                  : "—"}
              </TableCell>
              <TableCell>
                {device.lastReading.h > 0
                  ? `${device.lastReading.h.toFixed(1)}%`
                  : "—"}
              </TableCell>
              <TableCell className="text-right">
                <Link to={`/device/${device.id}`}>
                  <Button variant="ghost" size="sm">
                    <Eye className="w-4 h-4 mr-2" />
                    {t("common.viewDetails")}
                  </Button>
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}
