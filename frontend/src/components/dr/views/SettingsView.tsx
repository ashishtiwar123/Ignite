import { useState } from "react";
import { Bell, Check, Database, Eye, Globe, HardDrive, Layers, RefreshCw, Save, Shield, Sliders } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

export default function SettingsView() {
  const [audioSiren, setAudioSiren] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [highResTiles, setHighResTiles] = useState(true);
  const [aiAutoDispatch, setAiAutoDispatch] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-5 p-5 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 rounded-2xl border border-border/80 bg-card p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-secondary text-primary">
            <Sliders className="h-5.5 w-5.5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Command Centre System Settings</h1>
            <p className="text-xs font-medium text-muted-foreground">
              Configure EOC alert sirens, map tile rendering frequency, AI dispatch threshold &amp; node parameters.
            </p>
          </div>
        </div>

        <Button onClick={handleSave} className="h-9.5 px-4 text-xs font-bold">
          {saved ? (
            <>
              <Check className="h-4 w-4 mr-1.5 text-emerald-400" /> Settings Saved!
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-1.5" /> Save Preferences
            </>
          )}
        </Button>
      </div>

      {/* Settings Grid */}
      <div className="space-y-4">
        {/* Section 1: Alert & Notification Settings */}
        <div className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-border/50 pb-3 text-sm font-bold text-foreground">
            <Bell className="h-4 w-4 text-primary" /> Emergency Alert Siren &amp; Notifications
          </div>

          <div className="space-y-3.5">
            <div className="flex items-center justify-between">
              <div>
                <span className="block text-xs font-bold text-foreground">Audio Siren on Critical Hazards</span>
                <span className="text-xs font-medium text-muted-foreground">
                  Play audible alert chime whenever a new Critical severity incident or cloudburst alert is triggered.
                </span>
              </div>
              <Switch checked={audioSiren} onCheckedChange={setAudioSiren} />
            </div>

            <div className="flex items-center justify-between border-t border-border/40 pt-3">
              <div>
                <span className="block text-xs font-bold text-foreground">AI Automatic Dispatch Suggestion</span>
                <span className="text-xs font-medium text-muted-foreground">
                  Pre-populate optimal rescue units for one-click EOC commander authorization.
                </span>
              </div>
              <Switch checked={aiAutoDispatch} onCheckedChange={setAiAutoDispatch} />
            </div>
          </div>
        </div>

        {/* Section 2: Map & Satellite View Preferences */}
        <div className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-border/50 pb-3 text-sm font-bold text-foreground">
            <Layers className="h-4 w-4 text-primary" /> Map Rendering &amp; Satellite Tile Parameters
          </div>

          <div className="space-y-3.5">
            <div className="flex items-center justify-between">
              <div>
                <span className="block text-xs font-bold text-foreground">Live Telemetry Auto-Refresh (30s)</span>
                <span className="text-xs font-medium text-muted-foreground">
                  Stream Doppler radar layers and GPS unit coordinates automatically every 30 seconds.
                </span>
              </div>
              <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
            </div>

            <div className="flex items-center justify-between border-t border-border/40 pt-3">
              <div>
                <span className="block text-xs font-bold text-foreground">High-Resolution Satellite Imagery</span>
                <span className="text-xs font-medium text-muted-foreground">
                  Load Mapbox high-definition satellite imagery tiles for maximum ground clarity.
                </span>
              </div>
              <Switch checked={highResTiles} onCheckedChange={setHighResTiles} />
            </div>
          </div>
        </div>

        {/* Section 3: EOC Node System Information */}
        <div className="rounded-2xl border border-border/80 bg-card p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 border-b border-border/50 pb-3 text-sm font-bold text-foreground">
            <Shield className="h-4 w-4 text-primary" /> Command Node System Metadata
          </div>

          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="rounded-xl bg-secondary/80 p-3">
              <dt className="text-muted-foreground font-medium">Active EOC Node ID</dt>
              <dd className="font-mono font-bold text-foreground mt-0.5">EOC-MUMBAI-PRIMARY-01</dd>
            </div>
            <div className="rounded-xl bg-secondary/80 p-3">
              <dt className="text-muted-foreground font-medium">Regional Mesh Gateway</dt>
              <dd className="font-mono font-bold text-foreground mt-0.5">ASIA-SOUTH-IN-WEST-1</dd>
            </div>
            <div className="rounded-xl bg-secondary/80 p-3">
              <dt className="text-muted-foreground font-medium">Mapbox Engine SDK</dt>
              <dd className="font-mono font-bold text-foreground mt-0.5">v3.1.2 (Satellite HD)</dd>
            </div>
            <div className="rounded-xl bg-secondary/80 p-3">
              <dt className="text-muted-foreground font-medium">Emergency Network Protocol</dt>
              <dd className="font-mono font-bold text-emerald-400 mt-0.5">Encrypted ResQ-Mesh Active</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
