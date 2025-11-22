import { BrowserRouter, Routes, Route } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import DevicePage from "./pages/DevicePage";
import ChirpStackEventsPage from "./pages/ChirpStackEventsPage";
import MLAnalysisPage from "./pages/MLAnalysisPage";
import "./i18n/config";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/device/:id" element={<DevicePage />} />
        <Route path="/chirpstack/events" element={<ChirpStackEventsPage />} />
        <Route path="/ml/analysis" element={<MLAnalysisPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
