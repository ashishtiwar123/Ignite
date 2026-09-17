import { useEffect, useState } from "react";
import { Building2, Droplets, HeartPulse, LifeBuoy, PhoneCall, RefreshCw, Search, ShieldCheck, Truck, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getResources } from "@/lib/api/resources";
import type { ResourceRecord } from "@/lib/api/types";

import { isDemoMode } from "@/lib/demoScenario";

const DEMO_INVENTORY: ResourceRecord[] = [
  {
    resource_id: "res-001",
    location_id: "Mumbai Central Depot",
    resource_type: "Portable Water",
    category: "WATER",
    quantity_available: 12000,
    unit: "L",
    updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    resource_id: "res-002",
    location_id: "Mumbai Relief Warehouse",
    resource_type: "Cereal / Food",
    category: "FOOD",
    quantity_available: 0.8,
    unit: "MT",
    updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    resource_id: "res-003",
    location_id: "Emergency Medical Depot",
    resource_type: "Medical Kits",
    category: "MEDICAL",
    quantity_available: 320,
    unit: "units",
    updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    resource_id: "res-004",
    location_id: "Shelter Depot",
    resource_type: "Family Shelter Kits",
    category: "SHELTER",
    quantity_available: 300,
    unit: "units",
    updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    resource_id: "res-005",
    location_id: "Rescue Unit Alpha",
    resource_type: "Rescue Boats",
    category: "RESCUE",
    quantity_available: 8,
    unit: "units",
    updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    resource_id: "res-006",
    location_id: "Central Transport Hub",
    resource_type: "Emergency Vehicles",
    category: "TRANSPORT",
    quantity_available: 12,
    unit: "units",
    updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
];

export default function ResourcesView() {
  const [resources, setResources] = useState<ResourceRecord[]>(isDemoMode() ? DEMO_INVENTORY : []);
  const [loading, setLoading] = useState(!isDemoMode());
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchInventory = async () => {
    if (isDemoMode()) {
      setResources(DEMO_INVENTORY);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getResources();
      setResources(data);
    } catch (err: any) {
      setError(err.detail || err.message || "Failed to load operational inventory from backend");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const filtered = resources.filter((res) => {
    const matchesSearch =
      res.resource_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      res.location_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (res.category && res.category.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSearch;
  });

  return (
    <div className="space-y-5 p-5">
      {/* Header Banner */}
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-border/80 bg-card p-5 shadow-sm lg:flex-row lg:items-center">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
            <Truck className="h-5.5 w-5.5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Operational Resource Inventory</h1>
            <p className="text-xs font-medium text-muted-foreground">
              Real-time inventory levels from FastAPI backend (`GET /resources`) consumed by OR-Tools solver.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button onClick={fetchInventory} variant="outline" size="sm" className="text-xs font-semibold">
            <RefreshCw className={`h-3.5 w-3.5 mr-1 ${loading ? "animate-spin" : ""}`} /> Refresh Inventory
          </Button>
          <div className="rounded-xl border border-border bg-secondary/80 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-muted-foreground">Depots & Reserves</span>
            <span className="text-base font-bold text-foreground">{resources.length}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs font-medium text-rose-400">
          {error}
        </div>
      )}

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search by resource type, category or warehouse location ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="h-9.5 pl-9 text-xs font-medium"
        />
      </div>

      {/* Inventory Grid */}
      {loading ? (
        <div className="py-12 text-center text-xs text-muted-foreground">
          <RefreshCw className="h-5 w-5 animate-spin inline mr-2 text-primary" /> Loading real inventory...
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-border bg-card p-8 text-center text-xs text-muted-foreground">
          No inventory records found in backend database.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((res) => (
            <div key={res.resource_id} className="rounded-2xl border border-border/80 bg-card p-4 space-y-3 shadow-xs">
              <div className="flex justify-between items-start border-b border-border/50 pb-2.5">
                <div>
                  <span className="text-[10px] font-mono font-bold text-muted-foreground uppercase">{res.resource_id.slice(0, 8)}</span>
                  <h3 className="text-sm font-bold text-foreground">{res.resource_type}</h3>
                  <span className="text-[11px] text-muted-foreground">Category: {res.category || "GENERAL"}</span>
                </div>
                <span className="rounded-full bg-emerald-500/15 text-emerald-400 font-bold px-2 py-0.5 text-[10px] uppercase">
                  Available
                </span>
              </div>

              <div className="space-y-1 text-xs">
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Depot Location:</span>
                  <span className="font-semibold text-foreground">{res.location_id}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-muted-foreground">Quantity Available:</span>
                  <span className="font-mono font-bold text-amber-400">
                    {res.quantity_available.toLocaleString()} {res.unit}
                  </span>
                </div>
                <div className="flex justify-between py-1 text-[11px] text-muted-foreground">
                  <span>Last Updated:</span>
                  <span className="font-mono">{new Date(res.updated_at).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
