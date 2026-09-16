import { useState } from "react";
import { Building2, Droplets, HeartPulse, LifeBuoy, PhoneCall, Search, ShieldCheck, Truck, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";

export interface HelpingResource {
  id: string;
  name: string;
  category: "Hospital" | "NGO" | "Military Unit" | "NDRF / Fire" | "Water & Relief Base";
  location: string;
  contactLead: string;
  phone: string;
  status: "Active & Available" | "Fully Deployed" | "On Standby";
  capacityOrInventory: string;
  occupancyPct: number;
  waterSupplies: string;
  equipment: string[];
}

const RESOURCES_DATA: HelpingResource[] = [
  {
    id: "RES-101",
    name: "Sion Municipal General Hospital & Trauma Care",
    category: "Hospital",
    location: "Sion West, Mumbai",
    contactLead: "Dr. Rajesh K. Sharma (Chief Medical Officer)",
    phone: "+91 98200 11223",
    status: "Active & Available",
    capacityOrInventory: "240 / 300 ICU & Trauma Beds",
    occupancyPct: 80,
    waterSupplies: "18,000 Litres (Emergency Backup Tank)",
    equipment: ["25 Ambulances", "40 Oxygen Concentrators", "Trauma Operation Theatres"],
  },
  {
    id: "RES-102",
    name: "NDRF Battalion 5 Emergency Response Depot",
    category: "NDRF / Fire",
    location: "Andheri East Command Base",
    contactLead: "Cmdt. Vikram Singh (NDRF Platoon Lead)",
    phone: "+91 98111 44556",
    status: "Active & Available",
    capacityOrInventory: "120 Personnel On Duty",
    occupancyPct: 65,
    waterSupplies: "25,000 Litres Portable Purified Packs",
    equipment: ["18 Inflatable Rescue Boats", "Heavy Chainsaws", "Drone Search Sensors", "Submersible Pumps"],
  },
  {
    id: "RES-103",
    name: "Indian Red Cross Society Relief Staging Point",
    category: "NGO",
    location: "Kurla West High School Compound",
    contactLead: "Ananya Mehta (Relief Coordinator)",
    phone: "+91 97690 33445",
    status: "Active & Available",
    capacityOrInventory: "4,500 Ration & Food Packets",
    occupancyPct: 45,
    waterSupplies: "12,000 L Mineral Drinking Water Bottles",
    equipment: ["First Aid Tents", "1,200 Dry Blankets", "Hygiene Kits", "Mobile Kitchen"],
  },
  {
    id: "RES-104",
    name: "Indian Army Disaster Relief Taskforce (Western Command)",
    category: "Military Unit",
    location: "Kalina Military Camp",
    contactLead: "Col. S. V. Deshmukh",
    phone: "+91 99300 55667",
    status: "Active & Available",
    capacityOrInventory: "250 Armed Personnel + Amphibious Vehicles",
    occupancyPct: 50,
    waterSupplies: "35,000 L Water Tankers (High Capacity)",
    equipment: ["4 Amphibious Rescue Trucks", "Bridge Construction Kit", "Satellite Emergency Comms"],
  },
  {
    id: "RES-105",
    name: "Mumbai Fire Brigade Central Dispatch & Water Station",
    category: "NDRF / Fire",
    location: "Byculla Headquarters",
    contactLead: "Officer K. N. Patil",
    phone: "+91 98210 99887",
    status: "Fully Deployed",
    capacityOrInventory: "32 Fire Tenders Deployed",
    occupancyPct: 95,
    waterSupplies: "50,000 L High-Pressure Hose Reservoirs",
    equipment: ["Hydraulic Cutters", "High-Reach Ladders", "Hazmat Suits", "High-Volume Water Extraction Cannon"],
  },
  {
    id: "RES-106",
    name: "BKC Water Purification & Emergency Supply Depot",
    category: "Water & Relief Base",
    location: "Bandra Kurla Complex Block G",
    contactLead: "Eng. Amit Joshi (BMC Water Works)",
    phone: "+91 98700 22114",
    status: "Active & Available",
    capacityOrInventory: "80,000 Litres Filtered Drinking Water",
    occupancyPct: 30,
    waterSupplies: "80,000 L Fresh Purified Reserve",
    equipment: ["6 Water Bowsers", "Reverse Osmosis Mobile Filtration Unit", "Water Can Distribution Vans"],
  },
];

export default function ResourcesView() {
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = RESOURCES_DATA.filter((r) => {
    const matchesCat = categoryFilter === "all" || r.category === categoryFilter;
    const matchesSearch =
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.contactLead.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-5 p-5">
      {/* Header Banner */}
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-border/80 bg-card p-5 shadow-sm lg:flex-row lg:items-center">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
            <Truck className="h-5.5 w-5.5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Helping Points &amp; Emergency Resource Inventory</h1>
            <p className="text-xs font-medium text-muted-foreground">
              Directory of active NGOs, Hospitals, Military Taskforces, Water Stations &amp; Emergency Assets.
            </p>
          </div>
        </div>

        {/* Quick Resource Stats Bar */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-xl border border-border bg-secondary/80 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-muted-foreground">Hospitals &amp; Trauma</span>
            <span className="text-base font-bold text-foreground">12 Units</span>
          </div>
          <div className="rounded-xl border border-border bg-cyan-500/10 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-cyan-400">Water Supplies</span>
            <span className="text-base font-bold text-cyan-400">220,000 L</span>
          </div>
          <div className="rounded-xl border border-border bg-primary/10 px-3.5 py-2 text-center">
            <span className="block text-xs font-medium text-primary">Military &amp; NDRF</span>
            <span className="text-base font-bold text-primary">8 Battalions</span>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col gap-3 rounded-2xl border border-border/80 bg-card p-3.5 shadow-xs sm:flex-row sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search hospital, NGO, water depot or contact lead…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-9.5 pl-9 text-xs font-medium"
          />
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {[
            { id: "all", label: "All Helping Points" },
            { id: "Hospital", label: "Hospitals" },
            { id: "NGO", label: "NGOs" },
            { id: "Military Unit", label: "Military" },
            { id: "NDRF / Fire", label: "NDRF & Fire" },
            { id: "Water & Relief Base", label: "Water Depots" },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setCategoryFilter(cat.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                categoryFilter === cat.id
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-secondary text-muted-foreground hover:text-foreground"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Resource Cards Grid */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((res) => {
          return (
            <div
              key={res.id}
              className="flex flex-col justify-between rounded-2xl border border-border/80 bg-card p-5 shadow-sm hover:border-primary/50 transition-all hover:shadow-md"
            >
              <div>
                <div className="flex items-start justify-between gap-3 border-b border-border/50 pb-3">
                  <div>
                    <span className="rounded-md bg-secondary px-2.5 py-0.5 text-xs font-bold text-primary">
                      {res.category}
                    </span>
                    <h3 className="mt-2 text-base font-bold text-foreground leading-snug">{res.name}</h3>
                    <p className="text-xs font-medium text-muted-foreground mt-0.5">📍 {res.location}</p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                      res.status === "Active & Available"
                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                        : res.status === "Fully Deployed"
                          ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {res.status}
                  </span>
                </div>

                <div className="mt-3.5 space-y-2 text-xs">
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span className="flex items-center gap-1 font-medium">
                      <Building2 className="h-3.5 w-3.5 text-primary" /> Facility Capacity:
                    </span>
                    <span className="font-mono font-bold text-foreground">{res.capacityOrInventory}</span>
                  </div>
                  <Progress value={res.occupancyPct} className="h-2" />

                  <div className="flex items-center justify-between pt-1 text-muted-foreground">
                    <span className="flex items-center gap-1 font-medium text-cyan-400">
                      <Droplets className="h-3.5 w-3.5" /> Emergency Water Reserve:
                    </span>
                    <span className="font-mono font-bold text-cyan-400">{res.waterSupplies}</span>
                  </div>
                </div>

                <div className="mt-3.5 border-t border-border/50 pt-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
                    Available Equipment &amp; Assets
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {res.equipment.map((eq) => (
                      <span key={eq} className="rounded-md bg-secondary px-2 py-0.5 text-[11px] font-semibold text-foreground">
                        ⚡ {eq}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-5 border-t border-border/50 pt-3">
                <div className="mb-3 text-xs">
                  <span className="text-muted-foreground block font-medium">Officer / Contact Lead:</span>
                  <span className="font-bold text-foreground">{res.contactLead}</span>
                </div>
                <div className="flex gap-2">
                  <Button className="flex-1 h-9 text-xs font-bold" size="default">
                    <PhoneCall className="h-3.5 w-3.5 mr-1.5" /> {res.phone}
                  </Button>
                  <Button variant="outline" className="h-9 px-3 text-xs font-semibold">
                    Request Stock
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
