import { useState } from "react";
import { useTranslation } from "react-i18next";
import i18n from "@/i18n/config";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LanguageSelector } from "@/components/language-selector";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Brain,
  Loader2,
  AlertCircle,
  CheckCircle2,
  BarChart3,
  TrendingUp,
  Layers,
} from "lucide-react";
import {
  performMLAnalysis,
  type MLAnalysisRequest,
  type MLAnalysisResponse,
} from "@/lib/api";
import { Link } from "react-router-dom";

export default function MLAnalysisPage() {
  const { t, i18n } = useTranslation();
  const [analysisType, setAnalysisType] = useState<
    "clustering" | "prediction" | "classification"
  >("clustering");
  const [targetField, setTargetField] = useState<
    "temperature" | "humidity" | "rssi" | "vazao"
  >("temperature");
  const [timeRange, setTimeRange] = useState<string>("last_30_days");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MLAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const request: MLAnalysisRequest = {
        dataset: "sensor_data",
        analysis_type: analysisType,
        target_field: targetField,
        time_range: timeRange,
      };

      const response = await performMLAnalysis(request);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("mlAnalysis.error"));
      console.error("Erro ao realizar análise:", err);
    } finally {
      setLoading(false);
    }
  };

  const getAnalysisIcon = () => {
    switch (analysisType) {
      case "clustering":
        return <Layers className="w-5 h-5" />;
      case "prediction":
        return <TrendingUp className="w-5 h-5" />;
      case "classification":
        return <BarChart3 className="w-5 h-5" />;
    }
  };

  const renderResults = () => {
    if (!result) return null;

    const { results, analysis_type } = result;

    if (analysis_type === "clustering") {
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t("mlAnalysis.results.totalPoints")}
              </div>
              <div className="text-2xl font-semibold">
                {results.total_points || 0}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t("mlAnalysis.results.numClusters")}
              </div>
              <div className="text-2xl font-semibold">
                {results.n_clusters || 0}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t("mlAnalysis.results.inertia")}
              </div>
              <div className="text-2xl font-semibold">
                {results.inertia ? results.inertia.toFixed(2) : "—"}
              </div>
            </Card>
          </div>

          {results.cluster_stats && results.cluster_stats.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">
                {t("mlAnalysis.results.clusterStats")}
              </h3>
              <div className="grid gap-4">
                {results.cluster_stats.map((cluster: any) => (
                  <Card key={cluster.cluster_id} className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold">
                        {t("mlAnalysis.results.cluster")} {cluster.cluster_id}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {cluster.count} {t("mlAnalysis.results.points")}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">
                          {t("mlAnalysis.results.mean")}:{" "}
                        </span>
                        <span className="font-medium">
                          {cluster.mean.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">
                          {t("mlAnalysis.results.std")}:{" "}
                        </span>
                        <span className="font-medium">
                          {cluster.std.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">
                          {t("common.min")}:{" "}
                        </span>
                        <span className="font-medium">
                          {cluster.min.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">
                          {t("common.max")}:{" "}
                        </span>
                        <span className="font-medium">
                          {cluster.max.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {results.cluster_centers && results.cluster_centers.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-2">
                {t("mlAnalysis.results.clusterCenters")}
              </h3>
              <div className="flex gap-2 flex-wrap">
                {results.cluster_centers.map((center: number, idx: number) => (
                  <Badge
                    key={`cluster-${idx}`}
                    variant="outline"
                    className="text-sm"
                  >
                    {t("mlAnalysis.results.cluster")} {idx}: {center.toFixed(2)}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    if (analysis_type === "prediction") {
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card className="p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t("mlAnalysis.results.modelScore")}
              </div>
              <div className="text-2xl font-semibold">
                {results.model_score
                  ? (results.model_score * 100).toFixed(1)
                  : 0}
                %
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t("mlAnalysis.results.predictionsGenerated")}
              </div>
              <div className="text-2xl font-semibold">
                {results.predictions ? results.predictions.length : 0}
              </div>
            </Card>
          </div>

          {results.predictions && results.predictions.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">
                {t("mlAnalysis.results.futurePredictions")}
              </h3>
              <div className="space-y-2">
                {results.predictions.map((pred: any) => (
                  <Card key={pred.step} className="p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm text-muted-foreground">
                          {t("mlAnalysis.results.step")} {pred.step}
                        </span>
                        <div className="text-lg font-semibold">
                          {pred.predicted_value.toFixed(2)}
                        </div>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(pred.timestamp).toLocaleString(
                          i18n.language === "pt-BR" ? "pt-BR" : "en-US"
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {results.feature_importance && (
            <div>
              <h3 className="text-lg font-semibold mb-2">
                {t("mlAnalysis.results.featureImportance")}
              </h3>
              <div className="space-y-2">
                {Object.entries(results.feature_importance).map(
                  ([feature, importance]: [string, any]) => (
                    <div key={feature} className="flex items-center gap-2">
                      <span className="text-sm w-32 text-muted-foreground">
                        {feature}:
                      </span>
                      <div className="flex-1 bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full"
                          style={{ width: `${importance * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-12 text-right">
                        {(importance * 100).toFixed(1)}%
                      </span>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      );
    }

    if (analysis_type === "classification") {
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t("mlAnalysis.results.modelAccuracy")}
              </div>
              <div className="text-2xl font-semibold">
                {results.model_accuracy
                  ? (results.model_accuracy * 100).toFixed(1)
                  : 0}
                %
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t("mlAnalysis.results.totalClassified")}
              </div>
              <div className="text-2xl font-semibold">
                {results.total_classified || 0}
              </div>
            </Card>
          </div>

          {results.class_thresholds && (
            <div>
              <h3 className="text-lg font-semibold mb-2">
                {t("mlAnalysis.results.classThresholds")}
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <Card className="p-4">
                  <div className="text-sm text-muted-foreground mb-1">
                    {t("mlAnalysis.results.low")}
                  </div>
                  <div className="text-xl font-semibold">
                    &lt; {results.class_thresholds.baixo.toFixed(2)}
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="text-sm text-muted-foreground mb-1">
                    {t("mlAnalysis.results.normal")}
                  </div>
                  <div className="text-xl font-semibold">
                    {results.class_thresholds.baixo.toFixed(2)} -{" "}
                    {results.class_thresholds.alto.toFixed(2)}
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="text-sm text-muted-foreground mb-1">
                    {t("mlAnalysis.results.high")}
                  </div>
                  <div className="text-xl font-semibold">
                    &gt; {results.class_thresholds.alto.toFixed(2)}
                  </div>
                </Card>
              </div>
            </div>
          )}

          {results.class_distribution && (
            <div>
              <h3 className="text-lg font-semibold mb-3">
                {t("mlAnalysis.results.classDistribution")}
              </h3>
              <div className="space-y-2">
                {Object.entries(results.class_distribution).map(
                  ([className, count]: [string, any]) => (
                    <div key={className} className="flex items-center gap-4">
                      <span className="text-sm w-24 font-medium capitalize">
                        {className}:
                      </span>
                      <div className="flex-1 bg-muted rounded-full h-4">
                        <div
                          className="bg-primary h-4 rounded-full flex items-center justify-end pr-2"
                          style={{
                            width: `${
                              (count / results.total_classified) * 100
                            }%`,
                          }}
                        >
                          <span className="text-xs text-primary-foreground font-medium">
                            {count}
                          </span>
                        </div>
                      </div>
                      <span className="text-sm text-muted-foreground w-12 text-right">
                        {((count / results.total_classified) * 100).toFixed(1)}%
                      </span>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
        </div>
      );
    }

    return (
      <div className="p-4">
        <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
          {JSON.stringify(results, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-foreground flex items-center gap-2">
                <Brain className="w-6 h-6" />
                {t("mlAnalysis.title")}
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                {t("mlAnalysis.subtitle")}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <LanguageSelector />
              <Link to="/">
                <Button variant="outline" size="sm">
                  {t("common.backToDashboard")}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Formulário de Análise */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>{t("mlAnalysis.configure")}</CardTitle>
            <CardDescription>
              {t("mlAnalysis.configureDescription")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div>
                <label
                  htmlFor="analysis-type"
                  className="text-sm font-medium mb-2 block"
                >
                  {t("mlAnalysis.analysisType")}
                </label>
                <Select
                  name="analysis-type"
                  value={analysisType}
                  onValueChange={(value) =>
                    setAnalysisType(
                      value as "clustering" | "prediction" | "classification"
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="clustering">
                      <div className="flex items-center gap-2">
                        <Layers className="w-4 h-4" />
                        {t("mlAnalysis.clustering")}
                      </div>
                    </SelectItem>
                    <SelectItem value="prediction">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" />
                        {t("mlAnalysis.prediction")}
                      </div>
                    </SelectItem>
                    <SelectItem value="classification">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4" />
                        {t("mlAnalysis.classification")}
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label
                  htmlFor="target-field"
                  className="text-sm font-medium mb-2 block"
                >
                  {t("mlAnalysis.targetField")}
                </label>
                <Select
                  name="target-field"
                  value={targetField}
                  onValueChange={(value) =>
                    setTargetField(
                      value as "temperature" | "humidity" | "rssi" | "vazao"
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="temperature">
                      {t("common.temperature")}
                    </SelectItem>
                    <SelectItem value="humidity">
                      {t("common.humidity")}
                    </SelectItem>
                    <SelectItem value="rssi">RSSI</SelectItem>
                    <SelectItem value="vazao">{t("common.flow")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label
                  htmlFor="time-range"
                  className="text-sm font-medium mb-2 block"
                >
                  {t("mlAnalysis.timeRange")}
                </label>
                <Select
                  name="time-range"
                  value={timeRange}
                  onValueChange={setTimeRange}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="last_24h">
                      {t("mlAnalysis.timeRanges.last_24h")}
                    </SelectItem>
                    <SelectItem value="last_7_days">
                      {t("mlAnalysis.timeRanges.last_7_days")}
                    </SelectItem>
                    <SelectItem value="last_30_days">
                      {t("mlAnalysis.timeRanges.last_30_days")}
                    </SelectItem>
                    <SelectItem value="last_90_days">
                      {t("mlAnalysis.timeRanges.last_90_days")}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button
              onClick={handleAnalyze}
              disabled={loading}
              size="lg"
              className="w-full md:w-auto"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t("mlAnalysis.analyzing")}
                </>
              ) : (
                <>
                  {getAnalysisIcon()}
                  {t("mlAnalysis.execute")}
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Resultados */}
        {error && (
          <Card className="mb-8 border-destructive">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="w-5 h-5" />
                <span className="font-medium">{t("common.error")}</span>
              </div>
              <p className="mt-2 text-sm">{error}</p>
            </CardContent>
          </Card>
        )}

        {result && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                    {t("mlAnalysis.results")}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {result.analysis_type} - {result.target_field} -{" "}
                    {result.time_range}
                  </CardDescription>
                </div>
                <div className="text-xs text-muted-foreground">
                  {new Date(result.metadata.timestamp).toLocaleString(
                    i18n.language === "pt-BR" ? "pt-BR" : "en-US"
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>{renderResults()}</CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
