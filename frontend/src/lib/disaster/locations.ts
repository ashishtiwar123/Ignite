import type { LngLat } from "./geo";

export interface LocationPreset {
  key: string;
  label: string;
  region: string;
  center: LngLat;
  zoom: number;
  zones: string[];
}

export const LOCATIONS: LocationPreset[] = [
  {
    key: "mumbai",
    label: "Mumbai",
    region: "Maharashtra",
    center: [72.8656, 19.0728],
    zoom: 11.4,
    zones: ["Kurla West", "BKC", "Sion", "Dadar", "Mahim", "Vikhroli"],
  },
  {
    key: "chennai",
    label: "Chennai",
    region: "Tamil Nadu",
    center: [80.2385, 13.0435],
    zoom: 11.4,
    zones: ["Velachery", "Adyar", "T. Nagar", "Mylapore", "Perungudi", "Guindy"],
  },
  {
    key: "kolkata",
    label: "Kolkata",
    region: "West Bengal",
    center: [88.3639, 22.5726],
    zoom: 11.4,
    zones: ["Salt Lake", "Behala", "Howrah", "Ballygunge", "Tollygunge", "Dumdum"],
  },
  {
    key: "delhi",
    label: "Delhi NCR",
    region: "Delhi",
    center: [77.209, 28.6139],
    zoom: 11,
    zones: ["Yamuna Bank", "Okhla", "Rohini", "Dwarka", "Shahdara", "Karol Bagh"],
  },
  {
    key: "dehradun",
    label: "Dehradun Hills",
    region: "Uttarakhand",
    center: [78.0322, 30.3165],
    zoom: 11.2,
    zones: ["Rajpur", "Mussoorie Road", "Sahastradhara", "Clement Town", "Raipur", "Doiwala"],
  },
  {
    key: "kochi",
    label: "Kochi",
    region: "Kerala",
    center: [76.2673, 9.9312],
    zoom: 11.4,
    zones: ["Fort Kochi", "Kakkanad", "Aluva", "Edappally", "Vyttila", "Tripunithura"],
  },
];

export const getLocation = (key: string) => LOCATIONS.find((l) => l.key === key) ?? LOCATIONS[0]!;
