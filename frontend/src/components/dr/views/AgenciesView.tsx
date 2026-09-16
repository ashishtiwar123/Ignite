import { useState } from "react";
import { Building, PhoneCall, Shield, ShieldAlert, Users, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface ResponseAgency {
  id: string;
  name: string;
  abbreviation: string;
  type: "National Rescue Force" | "State Armed Division" | "Municipal Emergency" | "NGO Relief Network" | "Maritime Security";
  commander: string;
  hotline: string;
  headquarters: string;
  activePersonnel: number;
  deployedVehicles: number;
  status: "Immediate Readiness" | "Active Deployment" | "Reserve Standby";
  specialties: string[];
  notes: string;
}

const AGENCIES_DATA: ResponseAgency[] = [
  {
    id: "AGY-01",
    name: "National Disaster Response Force (NDRF)",
    abbreviation: "NDRF",
    type: "National Rescue Force",
    commander: "Director General Atul Karwal",
    hotline: "1078 / +91 11 2436 3260",
    headquarters: "NDRF Command HQ, New Delhi & Battalion 5 Mumbai",
    activePersonnel: 480,
    deployedVehicles: 42,
    status: "Active Deployment",
    specialties: ["Water & Flood Rescue", "Deep Debris Extraction", "Helicopter Winching", "Hazmat Containment"],
    notes: "Lead federal agency operating 6 rescue inflatable teams across Kurla and Sion flood basins.",
  },
  {
    id: "AGY-02",
    name: "Indian Army Disaster Relief Cell (Western Command)",
    abbreviation: "Indian Army",
    type: "State Armed Division",
    commander: "Brig. V. K. Nambiar",
    hotline: "+91 22 2413 8899",
    headquarters: "Mil Command Depot, Colaba & Kalina Transit Camp",
    activePersonnel: 350,
    deployedVehicles: 28,
    status: "Active Deployment",
    specialties: ["Amphibious Evacuation", "Pontoon Bridge Construction", "Heavy Equipment Towing", "Air Drops"],
    notes: "Deploying 4 amphibious rescue trucks and mobile field kitchens for 5,000 citizens.",
  },
  {
    id: "AGY-03",
    name: "Mumbai Fire Brigade & Hazardous Response Wing",
    abbreviation: "MFB",
    type: "Municipal Emergency",
    commander: "Chief Fire Officer Ravindra Ambulgekar",
    hotline: "101 / +91 22 2307 6111",
    headquarters: "Byculla Fire Headquarters, Mumbai",
    activePersonnel: 620,
    deployedVehicles: 85,
    status: "Active Deployment",
    specialties: ["Fire Suppression", "Submergence Dewatering Pumps", "High-Rise Rescue", "Gas Leak Containment"],
    notes: "Operating 12 high-capacity dewatering pumps at SCLR subway and Kurla West railway track.",
  },
  {
    id: "AGY-04",
    name: "Indian Coast Guard Relief Taskforce (Region West)",
    abbreviation: "ICG",
    type: "Maritime Security",
    commander: "Inspector General Bhisham Sharma",
    hotline: "1554 / +91 22 2437 1999",
    headquarters: "Coast Guard Regional HQ, Worli Seaface",
    activePersonnel: 180,
    deployedVehicles: 14,
    status: "Immediate Readiness",
    specialties: ["Coastal Inundation Rescue", "Helicopter Air-Evac", "Sea & Creek Patrol", "Drowning Recovery"],
    notes: "3 Chetak helicopters on standby at Juhu Aerodrome for aerial reconnaissance and winch rescues.",
  },
  {
    id: "AGY-05",
    name: "Indian Red Cross Society (Maharashtra Branch)",
    abbreviation: "IRCS",
    type: "NGO Relief Network",
    commander: "Dr. Rama Rao (State Relief Director)",
    hotline: "+91 22 2266 1530",
    headquarters: "Red Cross Building, Town Hall Compound, Fort",
    activePersonnel: 220,
    deployedVehicles: 16,
    status: "Active Deployment",
    specialties: ["First Aid Tents", "Drinking Water Supply", "Temporary Shelter Management", "Tracing Stranded Families"],
    notes: "Managing 3 emergency relief camps with dry ration packets, infant milk, and hygiene supplies.",
  },
  {
    id: "AGY-06",
    name: "State Disaster Response Force (SDRF Maharashtra)",
    abbreviation: "SDRF",
    type: "National Rescue Force",
    commander: "Commandant S. P. Gaikwad",
    hotline: "+91 20 2612 2244",
    headquarters: "Nagpur Base & Mumbai Transit Wing",
    activePersonnel: 300,
    deployedVehicles: 24,
    status: "Reserve Standby",
    specialties: ["Landslide Recovery", "Swift Water Rescue", "Search & Rescue K9 Unit"],
    notes: "Reserve battalion staged at Thane Base ready for rapid deployment within 15 minutes.",
  },
];

export default function AgenciesView() {
  const [agencies] = useState<ResponseAgency[]>(AGENCIES_DATA);

  return (
    <div className="space-y-5 p-5">
      {/* Header Banner */}
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-border/80 bg-card p-5 shadow-sm lg:flex-row lg:items-center">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/15 text-purple-400">
            <Users className="h-5.5 w-5.5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Disaster Response Agencies Directory</h1>
            <p className="text-xs font-medium text-muted-foreground">
              Official Command Directory of Federal, Military, Municipal &amp; Relief Bodies Operating in EOC Region.
            </p>
          </div>
        </div>

        {/* Total Personnel Stats */}
        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-border bg-secondary/80 px-4 py-2 text-center">
            <span className="block text-xs font-medium text-muted-foreground">Coordinated Bodies</span>
            <span className="text-base font-bold text-foreground">{agencies.length} Agencies</span>
          </div>
          <div className="rounded-xl border border-border bg-purple-500/10 px-4 py-2 text-center">
            <span className="block text-xs font-medium text-purple-400">Deployed Personnel</span>
            <span className="text-base font-bold text-purple-400">1,970 Force</span>
          </div>
        </div>
      </div>

      {/* Agency Grid */}
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
        {agencies.map((agency) => (
          <div
            key={agency.id}
            className="flex flex-col justify-between rounded-2xl border border-border/80 bg-card p-5 shadow-sm hover:border-purple-500/50 transition-all hover:shadow-md"
          >
            <div>
              <div className="flex items-start justify-between gap-3 border-b border-border/50 pb-3">
                <div>
                  <span className="rounded-md bg-purple-500/15 px-2.5 py-0.5 text-xs font-bold text-purple-300">
                    {agency.abbreviation}
                  </span>
                  <h2 className="mt-2 text-base font-bold text-foreground leading-snug">{agency.name}</h2>
                  <p className="text-xs font-medium text-muted-foreground mt-0.5">{agency.type}</p>
                </div>
                <span
                  className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                    agency.status === "Active Deployment"
                      ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                      : agency.status === "Immediate Readiness"
                        ? "bg-primary/15 text-primary border border-primary/30"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {agency.status}
                </span>
              </div>

              <div className="mt-3.5 space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-border/40">
                  <span className="text-muted-foreground">Lead Officer / Commander:</span>
                  <span className="font-bold text-foreground">{agency.commander}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/40">
                  <span className="text-muted-foreground">Active Personnel:</span>
                  <span className="font-mono font-bold text-foreground">{agency.activePersonnel} Troops / Rescuers</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/40">
                  <span className="text-muted-foreground">Deployed Vehicles:</span>
                  <span className="font-mono font-bold text-foreground">{agency.deployedVehicles} Heavy Units</span>
                </div>
                <div className="py-1">
                  <span className="text-muted-foreground block mb-0.5">Command Base Headquarters:</span>
                  <span className="font-semibold text-foreground">{agency.headquarters}</span>
                </div>
              </div>

              <div className="mt-3.5 border-t border-border/50 pt-3">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
                  Core Tactical Capabilities
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {agency.specialties.map((spec) => (
                    <span key={spec} className="rounded-md bg-secondary px-2 py-0.5 text-[11px] font-semibold text-purple-300">
                      🎯 {spec}
                    </span>
                  ))}
                </div>
              </div>

              <p className="mt-3 rounded-xl bg-secondary/80 p-2.5 text-xs text-muted-foreground leading-relaxed">
                {agency.notes}
              </p>
            </div>

            <div className="mt-5 border-t border-border/50 pt-3 flex gap-2">
              <Button className="flex-1 h-9.5 text-xs font-bold" size="default">
                <PhoneCall className="h-3.5 w-3.5 mr-1.5" /> Hotline: {agency.hotline.split("/")[0]}
              </Button>
              <Button variant="outline" className="h-9.5 px-3 text-xs font-semibold">
                Request Backup
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
