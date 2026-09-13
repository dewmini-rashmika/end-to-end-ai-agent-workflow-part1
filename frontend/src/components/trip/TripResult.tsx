"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Plane,
  Building2,
  CalendarDays,
  FileText,
  MapPin,
  Users,
  Clock,
  ArrowRight,
  AlertTriangle,
  Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent } from "@/components/ui/card";
import { FlightCard } from "./FlightCard";
import { HotelCard } from "./HotelCard";
import { ItineraryDay } from "./ItineraryDay";
import { formatDate } from "@/lib/utils";
import type { TripPlan } from "@/types";

interface TripResultProps {
  plan: TripPlan;
}

function EmptyState({ icon: Icon, message }: { icon: React.ElementType; message: string }) {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-muted-foreground">
      <Icon className="h-10 w-10 opacity-30" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function TripResult({ plan }: TripResultProps) {
  const hasFlights = plan.flight_results.length > 0;
  const hasHotels = plan.hotel_results.length > 0;
  const hasItinerary = plan.itinerary.length > 0;
  const hasErrors = plan.errors.length > 0;

  const handleDownload = () => {
    const text = plan.final_response || "No summary available.";
    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trip-plan-${plan.origin || "origin"}-to-${plan.destination || "dest"}.md`.replace(/\s+/g, '-').toLowerCase();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Trip summary header */}
      <div className="rounded-xl border bg-gradient-to-r from-blue-50 to-indigo-50 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-xl font-bold text-foreground">
                {plan.origin && plan.destination ? (
                  <>
                    {plan.origin}{" "}
                    <ArrowRight className="inline h-5 w-5 text-muted-foreground" />{" "}
                    {plan.destination}
                  </>
                ) : (
                  plan.user_query.slice(0, 60) + (plan.user_query.length > 60 ? "…" : "")
                )}
              </h2>
              {plan.budget && (
                <Badge variant="secondary" className="capitalize">
                  {plan.budget}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {plan.user_query}
            </p>
          </div>

          {/* Quick stats */}
          <div className="flex flex-wrap gap-3 text-sm">
            {plan.departure_date && (
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                {formatDate(plan.departure_date)}
                {plan.return_date && (
                  <>
                    {" "}— {formatDate(plan.return_date)}
                  </>
                )}
              </span>
            )}
            {plan.trip_duration_days > 0 && (
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <CalendarDays className="h-3.5 w-3.5" />
                {plan.trip_duration_days} days
              </span>
            )}
            {plan.num_travelers > 0 && (
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Users className="h-3.5 w-3.5" />
                {plan.num_travelers} traveler{plan.num_travelers !== 1 ? "s" : ""}
              </span>
            )}
          </div>
          
          <Button 
            variant="outline" 
            size="sm" 
            className="ml-auto flex items-center gap-2 mt-2 w-full sm:w-auto sm:mt-0" 
            onClick={handleDownload}
          >
            <Download className="h-4 w-4" />
            Download Plan
          </Button>
        </div>

        {/* Errors */}
        {hasErrors && (
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-800 text-xs">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <p>Some agents encountered issues: {plan.errors.join("; ")}</p>
          </div>
        )}
      </div>

      {/* Tabbed result sections */}
      <Tabs defaultValue={hasFlights ? "flights" : hasHotels ? "hotels" : "itinerary"}>
        <TabsList className="w-full grid grid-cols-4">
          <TabsTrigger value="flights" className="flex items-center gap-1.5 text-xs sm:text-sm">
            <Plane className="h-3.5 w-3.5" />
            <span>Flights</span>
            {hasFlights && (
              <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                {plan.flight_results.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="hotels" className="flex items-center gap-1.5 text-xs sm:text-sm">
            <Building2 className="h-3.5 w-3.5" />
            <span>Hotels</span>
            {hasHotels && (
              <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                {plan.hotel_results.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="itinerary" className="flex items-center gap-1.5 text-xs sm:text-sm">
            <CalendarDays className="h-3.5 w-3.5" />
            <span>Itinerary</span>
            {hasItinerary && (
              <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                {plan.itinerary.length}d
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="summary" className="flex items-center gap-1.5 text-xs sm:text-sm">
            <FileText className="h-3.5 w-3.5" />
            <span>Summary</span>
          </TabsTrigger>
        </TabsList>

        {/* Flights */}
        <TabsContent value="flights" className="mt-4">
          {hasFlights ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {plan.flight_results.map((flight, i) => (
                <FlightCard key={i} flight={flight} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Plane}
              message="No flight results were found for this trip."
            />
          )}
        </TabsContent>

        {/* Hotels */}
        <TabsContent value="hotels" className="mt-4">
          {hasHotels ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {plan.hotel_results.map((hotel, i) => (
                <HotelCard key={i} hotel={hotel} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Building2}
              message="No hotel results were found for this trip."
            />
          )}
        </TabsContent>

        {/* Itinerary */}
        <TabsContent value="itinerary" className="mt-4">
          {hasItinerary ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {plan.itinerary.map((day, i) => (
                <ItineraryDay key={i} day={day} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={CalendarDays}
              message="No day-by-day itinerary was generated for this trip."
            />
          )}
        </TabsContent>

        {/* Final summary */}
        <TabsContent value="summary" className="mt-4">
          {plan.final_response ? (
            <Card>
              <CardContent className="p-5 sm:p-6">
                <div className="prose prose-slate max-w-none dark:prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {plan.final_response}
                  </ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          ) : (
            <EmptyState
              icon={FileText}
              message="No travel summary was generated."
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
