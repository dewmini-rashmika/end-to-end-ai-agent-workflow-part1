// ============================================================
// TripMate AI — Shared TypeScript types
// Mirror the FastAPI Pydantic response schemas exactly
// ============================================================

export type BudgetTier = "budget" | "mid-range" | "luxury" | "";

// ---- Agent SSE event types -----------------------------------------

export type AgentName =
  | "parse_query"
  | "flight_agent"
  | "hotel_agent"
  | "itinerary_agent"
  | "final_response";

export interface AgentUpdateEvent {
  agent: AgentName;
  session_id: string;
  status: "running" | "completed" | "error";
  preview?: string;
  errors?: string[];
}

export type SSEEventType = "start" | "agent_update" | "done" | "error";

export interface SSEStartEvent {
  session_id: string;
  message: string;
  agents: AgentName[];
}

// ---- Trip plan ---------------------------------------------------------

export interface FlightResult {
  raw_text?: string;
  flight_number?: string;
  airline?: string;
  origin?: string;
  destination?: string;
  departure?: string;
  arrival?: string;
  duration_minutes?: number | null;
  stops?: number;
  price_usd?: number | null;
  status?: string;
  aircraft?: string | null;
  [key: string]: unknown;
}

export interface HotelResult {
  raw_text?: string;
  name?: string;
  address?: string;
  rating?: number | null;
  total_ratings?: number;
  price_level?: number | null;
  price_per_night_usd?: number | null;
  amenities?: string[];
  coordinates?: { lat: number; lng: number };
  url?: string | null;
  tier?: "budget" | "mid-range" | "luxury";
  [key: string]: unknown;
}

export interface ItineraryDay {
  raw_text?: string;
  day?: number;
  date?: string;
  morning?: string;
  afternoon?: string;
  evening?: string;
  notes?: string;
  [key: string]: unknown;
}

export interface TripPlan {
  session_id: string;
  conversation_id: string;
  user_query: string;
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string | null;
  num_travelers: number;
  trip_duration_days: number;
  budget: BudgetTier;
  interests: string;
  flight_results: FlightResult[];
  hotel_results: HotelResult[];
  itinerary: ItineraryDay[];
  final_response: string;
  completed_agents: AgentName[];
  errors: string[];
}

// ---- API request bodies -----------------------------------------------

export interface PlanTripRequest {
  user_query: string;
  session_id?: string;
  origin?: string;
  destination?: string;
  departure_date?: string;
  return_date?: string;
  num_travelers?: number;
  trip_duration_days?: number;
  budget?: BudgetTier;
  interests?: string;
}

export interface FollowUpRequest {
  message: string;
}

// ---- Session history --------------------------------------------------

export interface ConversationSummary {
  id: string;
  session_id: string;
  user_query: string;
  status: "pending" | "completed" | "error";
  created_at: string;
  updated_at: string;
  has_final_response: boolean;
}

// ---- UI state ---------------------------------------------------------

export type PlanningStatus =
  | "idle"
  | "connecting"
  | "planning"
  | "completed"
  | "error";

export interface AgentStep {
  name: AgentName;
  label: string;
  status: "waiting" | "running" | "completed" | "error";
  preview?: string;
  startedAt?: number;
  completedAt?: number;
}

export const AGENT_LABELS: Record<AgentName, string> = {
  parse_query: "Understanding your request",
  flight_agent: "Searching flights",
  hotel_agent: "Finding hotels",
  itinerary_agent: "Building itinerary",
  final_response: "Composing travel plan",
};

export const AGENT_ORDER: AgentName[] = [
  "parse_query",
  "flight_agent",
  "hotel_agent",
  "itinerary_agent",
  "final_response",
];
