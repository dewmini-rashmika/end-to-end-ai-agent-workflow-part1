import { Plane, Clock, ArrowRight, Users, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { formatDuration } from "@/lib/utils";
import type { FlightResult } from "@/types";

interface FlightCardProps {
  flight: FlightResult;
  className?: string;
}

function formatTime(dt: string | undefined): string {
  if (!dt) return "N/A";
  try {
    return new Date(dt).toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dt;
  }
}

function formatFlightDate(dt: string | undefined): string {
  if (!dt) return "";
  try {
    return new Date(dt).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  } catch {
    return "";
  }
}

export function FlightCard({ flight, className }: FlightCardProps) {
  // Handle raw_text only fallback
  if (!flight.flight_number && !flight.airline && flight.raw_text) {
    return (
      <Card className={className}>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
            {flight.raw_text}
          </p>
        </CardContent>
      </Card>
    );
  }

  const stops = flight.stops ?? 0;

  return (
    <Card className={className}>
      <CardHeader className="pb-3 pt-4 px-4">
        <div className="flex items-center justify-between gap-2">
          {/* Airline + flight number */}
          <div className="flex items-center gap-2 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-50">
              <Plane className="h-4 w-4 text-blue-600" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate">
                {flight.airline ?? "Unknown Airline"}
              </p>
              {flight.flight_number && (
                <p className="text-xs text-muted-foreground">
                  {flight.flight_number}
                </p>
              )}
            </div>
          </div>

          {/* Price */}
          {flight.price_usd != null ? (
            <Badge variant="secondary" className="shrink-0 font-semibold">
              ${flight.price_usd.toLocaleString()}
            </Badge>
          ) : (
            <Badge variant="outline" className="shrink-0 text-muted-foreground">
              Price N/A
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-4 space-y-3">
        {/* Route + timing */}
        <div className="flex items-center gap-3">
          {/* Departure */}
          <div className="text-center">
            <p className="text-lg font-bold tabular-nums">
              {formatTime(flight.departure)}
            </p>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              {flight.origin ?? "—"}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatFlightDate(flight.departure)}
            </p>
          </div>

          {/* Duration + stops */}
          <div className="flex-1 text-center">
            <p className="text-xs text-muted-foreground mb-1 flex items-center justify-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDuration(flight.duration_minutes)}
            </p>
            <div className="flex items-center gap-1">
              <div className="h-px flex-1 bg-border" />
              <Plane className="h-3 w-3 text-muted-foreground rotate-90" />
              <div className="h-px flex-1 bg-border" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stops === 0
                ? "Direct"
                : `${stops} stop${stops > 1 ? "s" : ""}`}
            </p>
          </div>

          {/* Arrival */}
          <div className="text-center">
            <p className="text-lg font-bold tabular-nums">
              {formatTime(flight.arrival)}
            </p>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              {flight.destination ?? "—"}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatFlightDate(flight.arrival)}
            </p>
          </div>
        </div>

        {/* Status + aircraft */}
        {(flight.status || flight.aircraft) && (
          <>
            <Separator />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              {flight.status && (
                <span className="flex items-center gap-1">
                  <span
                    className={
                      flight.status.toLowerCase() === "active"
                        ? "text-emerald-500"
                        : ""
                    }
                  >
                    {flight.status}
                  </span>
                </span>
              )}
              {flight.aircraft && <span>Aircraft: {flight.aircraft}</span>}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
